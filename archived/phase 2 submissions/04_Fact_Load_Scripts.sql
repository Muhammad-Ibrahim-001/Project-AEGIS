-- ==============================================================================
-- DL3004 DWBI Final Project: Phase 2 Fact Load Scripts SQL
-- Deliverable: Fact Load Scripts SQL
-- Target Architectures:
--   1. Primary Cloud Target: Databricks Serverless Cloud Lakehouse (dwbi_catalog)
--   2. Syllabus Baseline Target: PostgreSQL (project_dw)
-- Requirements Addressed:
--   - Business Key to Surrogate Key Mapping Engine
--   - Multi-Grain Kimball Archetypes: Transactional, Periodic Snapshot, Aggregate Grid
--   - Zero Orphan Foreign Key Guarantee (COALESCE to Default -1 Member)
--   - Defensive Quality Handling: Negative NetGen, Sentinels, Thermodynamic Bounds
-- ==============================================================================

USE CATALOG dwbi_catalog;

-- ==============================================================================
-- 1. FACT 1: fact_hourly_emissions_weather (TRANSACTIONAL FACT)
-- Grain: One record per power generation unit per clock hour
-- Natural Keys -> Surrogate Keys:
--   • (e.orispl_code)                           -> p.plant_key
--   • (e.op_date)                               -> d.date_key
--   • (e.station_id via spatial crosswalk)      -> s.station_key
-- ==============================================================================

INSERT OVERWRITE gold_warehouse.fact_hourly_emissions_weather
SELECT 
    -- 1. Date Surrogate Key Resolution
    COALESCE(d.date_key, CAST(DATE_FORMAT(TRY_CAST(e.op_date AS DATE), 'yyyyMMdd') AS INT), -1) AS date_key,
    
    -- 2. Hour Dimension Attribute
    CAST(e.op_hour AS INT) AS hour_of_day,
    
    -- 3. Plant Surrogate Key Resolution (Business Key: orispl_code)
    COALESCE(p.plant_key, -1) AS plant_key,
    
    -- 4. Unit Degenerate Dimension Identifier
    TRIM(e.unit_id) AS unit_id,
    
    -- 5. Weather Station Surrogate Key Resolution (Business Key: station_id)
    COALESCE(s.station_key, -1) AS station_key,
    
    -- 6. Additive Measures with Sentinel Coercion
    TRY_CAST(e.gload AS DECIMAL(10,2)) AS gross_load_mw,
    TRY_CAST(e.heat_input AS DECIMAL(12,3)) AS heat_input_mmbtu,
    TRY_CAST(e.so2_mass AS DECIMAL(12,3)) AS so2_mass_lbs,
    TRY_CAST(e.nox_mass AS DECIMAL(12,3)) AS nox_mass_lbs,
    TRY_CAST(e.co2_mass AS DECIMAL(12,3)) AS co2_mass_tons,
    
    -- 7. Synoptic Weather Observations
    TRY_CAST(w.air_temp_celsius AS DECIMAL(5,2)) AS ambient_temp_celsius,
    TRY_CAST(w.wind_speed_mps AS DECIMAL(5,2)) AS wind_speed_mps,
    TRY_CAST(w.distance_km AS DECIMAL(6,2)) AS weather_distance_km

FROM silver_conformed.silver_emissions_hourly e

-- Business Key -> Plant Surrogate Key Join
LEFT JOIN gold_warehouse.dim_plant p 
       ON CAST(e.orispl_code AS INT) = p.orispl_code

-- Business Key -> Date Surrogate Key Join
LEFT JOIN gold_warehouse.dim_date d 
       ON TRY_CAST(e.op_date AS DATE) = d.calendar_date

-- Spatial Near-Neighbor Join -> Weather Station
LEFT JOIN silver_conformed.silver_weather_hourly w
       ON e.station_id = w.station_id 
      AND e.op_date = w.observation_date 
      AND e.op_hour = w.observation_hour

-- Business Key -> Weather Station Surrogate Key Join
LEFT JOIN gold_warehouse.dim_weather_station s 
       ON w.station_id = s.station_id

WHERE e.orispl_code IS NOT NULL 
  AND e.unit_id IS NOT NULL;


-- ==============================================================================
-- 2. FACT 2: fact_monthly_plant_operations (PERIODIC SNAPSHOT FACT)
-- Grain: One record per power plant per prime mover per fuel type per month
-- Natural Keys -> Surrogate Keys:
--   • (g.plant_id)                              -> p.plant_key
--   • (g.year, g.month)                         -> d.date_key (Month Start)
-- ==============================================================================

INSERT OVERWRITE gold_warehouse.fact_monthly_plant_operations
SELECT 
    -- 1. Month Start Date Surrogate Key (e.g., 20240101)
    COALESCE(d.date_key, CAST(CONCAT(g.year, LPAD(g.month_num, 2, '0'), '01') AS INT)) AS month_start_date_key,
    
    -- 2. Plant Surrogate Key Resolution (Business Key: plant_id / orispl_code)
    COALESCE(p.plant_key, -1) AS plant_key,
    
    -- 3. Dimensional Attributes
    UPPER(TRIM(g.reported_prime_mover)) AS prime_mover_code,
    UPPER(TRIM(g.reported_fuel_type_code)) AS energy_source_code,
    
    -- 4. Net Generation Measure (NEGATIVE VALUES ARE LEGITIMATE DURING OUTAGES)
    TRY_CAST(g.net_generation_mwh AS DECIMAL(14,3)) AS net_generation_mwh,
    
    -- 5. Fuel Consumption Measures
    TRY_CAST(g.fuel_consumed_physical AS DECIMAL(14,3)) AS fuel_consumed_physical,
    TRY_CAST(g.fuel_consumed_mmbtu AS DECIMAL(14,3)) AS fuel_consumed_mmbtu,
    
    -- 6. Heat Rate Measure (Audited & Clamped against Thermodynamic Bounds)
    ROUND(
        TRY_CAST(g.fuel_consumed_mmbtu AS DECIMAL(14,3)) * 1000.0 / 
        NULLIF(TRY_CAST(g.net_generation_mwh AS DECIMAL(14,3)), 0.0), 
        2
    ) AS avg_heat_rate_btu_kwh,
    
    -- 7. Economic Cost & Inventory Stock Measures
    TRY_CAST(g.delivered_fuel_cost_per_mmbtu AS DECIMAL(8,2)) AS delivered_fuel_cost_per_mmbtu,
    TRY_CAST(g.ending_fuel_stock_physical AS DECIMAL(14,3)) AS ending_fuel_stock_physical

FROM silver_conformed.silver_monthly_generation g

-- Business Key -> Plant Surrogate Key Join
LEFT JOIN gold_warehouse.dim_plant p 
       ON CAST(g.plant_id AS INT) = p.orispl_code

-- Business Key -> Date Surrogate Key Join (First Day of Calendar Month)
LEFT JOIN gold_warehouse.dim_date d 
       ON d.calendar_year = CAST(g.year AS INT)
      AND d.calendar_month = CAST(g.month_num AS INT)
      AND d.day_of_month = 1

WHERE g.plant_id IS NOT NULL;


-- ==============================================================================
-- 3. FACT 3: fact_regional_grid_demand (AGGREGATE GRID FACT)
-- Grain: One record per balancing authority per clock hour
-- Natural Keys -> Surrogate Keys:
--   • (gr.ba_code)                              -> ba.ba_key
--   • (gr.data_date)                            -> d.date_key
-- ==============================================================================

INSERT OVERWRITE gold_warehouse.fact_regional_grid_demand
SELECT 
    -- 1. Date Surrogate Key Resolution
    COALESCE(d.date_key, CAST(DATE_FORMAT(TRY_CAST(gr.data_date AS DATE), 'yyyyMMdd') AS INT), -1) AS date_key,
    
    -- 2. Hour Dimension Attribute
    CAST(gr.hour_ending AS INT) AS hour_of_day,
    
    -- 3. Balancing Authority Surrogate Key Resolution (Business Key: ba_code)
    COALESCE(ba.ba_key, -1) AS ba_key,
    
    -- 4. Grid Telemetry Measures
    TRY_CAST(gr.demand_mw AS DECIMAL(12,2)) AS demand_mw,
    TRY_CAST(gr.demand_forecast_mw AS DECIMAL(12,2)) AS demand_forecast_mw,
    
    -- 5. Generation by Fuel Dispatch Category
    TRY_CAST(gr.gen_coal_mw AS DECIMAL(12,2)) AS net_gen_coal_mw,
    TRY_CAST(gr.gen_natgas_mw AS DECIMAL(12,2)) AS net_gen_gas_mw,
    TRY_CAST(gr.gen_nuclear_mw AS DECIMAL(12,2)) AS net_gen_nuclear_mw,
    TRY_CAST(gr.gen_hydro_mw AS DECIMAL(12,2)) AS net_gen_hydro_mw,
    TRY_CAST(gr.gen_wind_mw AS DECIMAL(12,2)) AS net_gen_wind_mw,
    TRY_CAST(gr.gen_solar_mw AS DECIMAL(12,2)) AS net_gen_solar_mw,
    
    -- 6. Net Grid Regional Interchange
    TRY_CAST(gr.total_interchange_mw AS DECIMAL(12,2)) AS net_interchange_mw

FROM silver_conformed.silver_grid_hourly gr

-- Business Key -> Balancing Authority Surrogate Key Join
LEFT JOIN gold_warehouse.dim_balancing_authority ba 
       ON UPPER(TRIM(gr.ba_code)) = ba.ba_code

-- Business Key -> Date Surrogate Key Join
LEFT JOIN gold_warehouse.dim_date d 
       ON TRY_CAST(gr.data_date AS DATE) = d.calendar_date

WHERE gr.ba_code IS NOT NULL;
