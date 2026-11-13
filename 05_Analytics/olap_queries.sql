-- ==============================================================================
-- DL3004 DWBI Final Project: Production OLAP Analytical SQL Suite
-- Work Package: WP4 (Analytics, OLAP, Power BI & Performance Lead)
-- Platform:     Databricks Serverless SQL Warehouse / Photon Engine
-- Catalog:      dwbi_catalog
-- Schema:       gold_warehouse
-- Storage:      Delta Lake with Liquid Clustering
-- Course Scope: DWBI Lab Phase 3 Specifications (OLAP CUBE, ROLLUP, Windowing)
-- ==============================================================================

USE CATALOG dwbi_catalog;

-- ==============================================================================
-- 1. MULTI-DIMENSIONAL OLAP CUBE: Generation & Heat Rate by Geography & Fuel Mix (ANSWERS BQ3)
-- Analytical Question: BQ3 - Prime Mover & Fuel Thermal Efficiency / Heat Rate Benchmarking
-- Fact Table:  fact_monthly_plant_operations
-- Dimensions:  dim_plant, dim_date
-- Measures:    net_generation_mwh, fuel_consumed_mmbtu, avg_heat_rate_btu_kwh
-- Demonstrates full combinatorial cross-tabulation across Year, State, and Fuel.
-- ==============================================================================
SELECT 
    COALESCE(CAST(d.calendar_year AS STRING), 'ALL_YEARS') AS calendar_year,
    COALESCE(p.state_code, 'ALL_STATES') AS state_code,
    COALESCE(f.energy_source_code, 'ALL_FUELS') AS energy_source_code,
    COUNT(DISTINCT f.plant_key) AS active_plants_count,
    ROUND(SUM(f.net_generation_mwh), 2) AS total_net_generation_mwh,
    ROUND(SUM(f.fuel_consumed_mmbtu), 2) AS total_fuel_mmbtu,
    ROUND(
        SUM(f.fuel_consumed_mmbtu * 1000.0) / NULLIF(SUM(f.net_generation_mwh), 0), 2
    ) AS weighted_avg_heat_rate_btu_kwh
FROM gold_warehouse.fact_monthly_plant_operations f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY CUBE (d.calendar_year, p.state_code, f.energy_source_code)
ORDER BY 
    d.calendar_year NULLS LAST, 
    p.state_code NULLS LAST, 
    f.energy_source_code NULLS LAST;


-- ==============================================================================
-- 2. HIERARCHICAL OLAP ROLLUP: Temporal & Spatial Grid Demand Slicing (ANSWERS BQ5)
-- Analytical Question: BQ5 - Balancing Authority Peak Demand, Renewable Penetration & Interchanges
-- Fact Table:  fact_regional_grid_demand
-- Dimensions:  dim_balancing_authority, dim_date
-- Measures:    demand_mw, net_gen_wind_mw, net_gen_solar_mw, renewable_coverage_pct
-- Hierarchical aggregation: Year -> Quarter -> Month -> Balancing Authority.
-- ==============================================================================
SELECT 
    COALESCE(CAST(d.calendar_year AS STRING), 'ALL_YEARS') AS calendar_year,
    COALESCE(CAST(d.calendar_quarter AS STRING), 'ALL_QUARTERS') AS calendar_quarter,
    COALESCE(CAST(d.calendar_month AS STRING), 'ALL_MONTHS') AS calendar_month,
    COALESCE(ba.ba_code, 'ALL_BAS') AS ba_code,
    ROUND(AVG(g.demand_mw), 2) AS avg_hourly_demand_mw,
    ROUND(MAX(g.demand_mw), 2) AS peak_hourly_demand_mw,
    ROUND(SUM(COALESCE(g.net_gen_wind_mw, 0) + COALESCE(g.net_gen_solar_mw, 0)), 2) AS total_renewable_generation_mwh,
    ROUND(
        SUM(COALESCE(g.net_gen_wind_mw, 0) + COALESCE(g.net_gen_solar_mw, 0)) / 
        NULLIF(SUM(g.demand_mw), 0) * 100, 2
    ) AS renewable_coverage_pct
FROM gold_warehouse.fact_regional_grid_demand g
JOIN gold_warehouse.dim_balancing_authority ba ON g.ba_key = ba.ba_key
JOIN gold_warehouse.dim_date d ON g.date_key = d.date_key
GROUP BY ROLLUP (d.calendar_year, d.calendar_quarter, d.calendar_month, ba.ba_code)
ORDER BY 
    d.calendar_year NULLS LAST, 
    d.calendar_quarter NULLS LAST, 
    d.calendar_month NULLS LAST;


-- ==============================================================================
-- 3. WINDOW FUNCTIONS: Month-Over-Month Ramp Rate, Growth % & Prior Year Lag (ANSWERS BQ10)
-- Analytical Question: BQ10 - Multi-Year Generation Trends & Decarbonization by Prime Mover
-- Fact Table:  fact_monthly_plant_operations
-- Dimensions:  dim_plant, dim_date
-- Measures:    current_net_mwh, mom_growth_pct, moving_avg_3month_mwh
-- ==============================================================================
WITH monthly_plant_totals AS (
    SELECT 
        f.plant_key,
        p.plant_name,
        p.state_code,
        d.calendar_year,
        d.calendar_month,
        SUM(f.net_generation_mwh) AS current_net_mwh,
        SUM(f.fuel_consumed_mmbtu) AS current_fuel_mmbtu
    FROM gold_warehouse.fact_monthly_plant_operations f
    JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
    JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
    GROUP BY f.plant_key, p.plant_name, p.state_code, d.calendar_year, d.calendar_month
)
SELECT 
    plant_name,
    state_code,
    calendar_year,
    calendar_month,
    ROUND(current_net_mwh, 2) AS current_net_mwh,
    ROUND(
        LAG(current_net_mwh, 1) OVER (
            PARTITION BY plant_key 
            ORDER BY calendar_year, calendar_month
        ), 2
    ) AS previous_month_net_mwh,
    ROUND(
        (current_net_mwh - LAG(current_net_mwh, 1) OVER (
            PARTITION BY plant_key ORDER BY calendar_year, calendar_month
        )) / NULLIF(ABS(LAG(current_net_mwh, 1) OVER (
            PARTITION BY plant_key ORDER BY calendar_year, calendar_month
        )), 0) * 100, 2
    ) AS mom_growth_pct,
    -- 3-Month Moving Average of Net Generation
    ROUND(
        AVG(current_net_mwh) OVER (
            PARTITION BY plant_key 
            ORDER BY calendar_year, calendar_month 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS moving_avg_3month_mwh
FROM monthly_plant_totals
ORDER BY plant_name, calendar_year, calendar_month;


-- ==============================================================================
-- 4. WINDOW FUNCTIONS: Facility Emissions Intensity Benchmarking & Dense Ranking (ANSWERS BQ1)
-- Analytical Question: BQ1 - Facility Emissions Intensity & Regional Distribution
-- Fact Table:  fact_hourly_emissions_weather
-- Dimensions:  dim_plant, dim_date
-- Measures:    gross_load_mw, co2_mass_tons, co2_intensity_tons_per_mw
-- ==============================================================================
WITH plant_annual_emissions AS (
    SELECT 
        d.calendar_year,
        p.orispl_code,
        p.plant_name,
        p.state_code,
        SUM(f.gross_load_mw) AS annual_gross_mw,
        SUM(f.co2_mass_tons) AS annual_co2_tons,
        ROUND(
            SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0), 4
        ) AS co2_intensity_tons_per_mw
    FROM gold_warehouse.fact_hourly_emissions_weather f
    JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
    JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY d.calendar_year, p.orispl_code, p.plant_name, p.state_code
)
SELECT 
    calendar_year,
    plant_name,
    state_code,
    annual_gross_mw,
    annual_co2_tons,
    co2_intensity_tons_per_mw,
    -- Rank plants from cleanest (lowest intensity) to highest emitters
    DENSE_RANK() OVER (
        PARTITION BY calendar_year 
        ORDER BY co2_intensity_tons_per_mw ASC NULLS LAST
    ) AS clean_energy_efficiency_rank,
    -- Cumulative Emissions Share per Year
    ROUND(
        annual_co2_tons / NULLIF(SUM(annual_co2_tons) OVER (PARTITION BY calendar_year), 0) * 100, 2
    ) AS pct_of_annual_national_emissions
FROM plant_annual_emissions
ORDER BY calendar_year, clean_energy_efficiency_rank;


-- ==============================================================================
-- 5. PERFORMANCE TUNING: EXPLAIN EXTENDED EXECUTION PLAN DEMONSTRATION
-- Verifies Liquid Clustering (CLUSTER BY date_key, plant_key) data skipping.
-- ==============================================================================
EXPLAIN EXTENDED
SELECT 
    d.calendar_date,
    p.plant_name,
    SUM(f.gross_load_mw) AS total_generation_mw,
    SUM(f.co2_mass_tons) AS total_co2_tons
FROM gold_warehouse.fact_hourly_emissions_weather f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
WHERE f.date_key BETWEEN 20230101 AND 20230131
  AND f.plant_key = 1
GROUP BY d.calendar_date, p.plant_name;


-- ==============================================================================
-- 6. WEATHER EXTREMES VS EMISSIONS & LOAD IMPACT (ANSWERS BQ2)
-- Analytical Question: BQ2 - Synoptic Weather Stress vs Emissions & Generation
-- Fact Table:  fact_hourly_emissions_weather
-- Dimensions:  dim_plant, dim_weather_station, dim_date
-- Measures:    gross_load_mw, co2_mass_tons, ambient_temp_celsius, wind_speed_mps
-- Business Intent: Evaluates plant efficiency derating and emissions intensity 
--                  under freezing, moderate, and extreme heat temperature regimes.
-- ==============================================================================
SELECT 
    CASE 
        WHEN f.ambient_temp_celsius < 0.0 THEN '1_FREEZING_BELOW_0C'
        WHEN f.ambient_temp_celsius BETWEEN 0.0 AND 15.0 THEN '2_COLD_0_TO_15C'
        WHEN f.ambient_temp_celsius BETWEEN 15.01 AND 28.0 THEN '3_MODERATE_15_TO_28C'
        WHEN f.ambient_temp_celsius > 28.0 THEN '4_EXTREME_HEAT_ABOVE_28C'
        ELSE '5_UNKNOWN_TEMPERATURE'
    END AS temperature_regime,
    COUNT(*) AS total_operating_hours,
    ROUND(AVG(f.gross_load_mw), 2) AS avg_hourly_gross_load_mw,
    ROUND(SUM(f.gross_load_mw), 2) AS total_gross_generation_mw,
    ROUND(SUM(f.co2_mass_tons), 2) AS total_co2_mass_tons,
    ROUND(
        SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0), 4
    ) AS co2_intensity_tons_per_mw,
    ROUND(AVG(f.wind_speed_mps), 2) AS avg_wind_speed_mps,
    ROUND(AVG(f.weather_distance_km), 2) AS avg_station_distance_km
FROM gold_warehouse.fact_hourly_emissions_weather f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
WHERE f.ambient_temp_celsius IS NOT NULL
GROUP BY 
    CASE 
        WHEN f.ambient_temp_celsius < 0.0 THEN '1_FREEZING_BELOW_0C'
        WHEN f.ambient_temp_celsius BETWEEN 0.0 AND 15.0 THEN '2_COLD_0_TO_15C'
        WHEN f.ambient_temp_celsius BETWEEN 15.01 AND 28.0 THEN '3_MODERATE_15_TO_28C'
        WHEN f.ambient_temp_celsius > 28.0 THEN '4_EXTREME_HEAT_ABOVE_28C'
        ELSE '5_UNKNOWN_TEMPERATURE'
    END
ORDER BY temperature_regime;


-- ==============================================================================
-- 7. PLANT AUXILIARY LOAD OUTAGES & NEGATIVE NET GENERATION AUDIT (ANSWERS BQ4)
-- Analytical Question: BQ4 - Station Auxiliary Outages & Negative Net Generation
-- Fact Table:  fact_monthly_plant_operations
-- Dimensions:  dim_plant, dim_date
-- Measures:    net_generation_mwh, fuel_consumed_mmbtu, outage_frequency
-- Business Intent: Audits offline power plants consuming auxiliary station grid
--                  power during extended maintenance or unplanned shutdowns.
-- ==============================================================================
SELECT 
    d.calendar_year,
    p.orispl_code,
    p.plant_name,
    p.state_code,
    f.prime_mover_code,
    COUNT(CASE WHEN f.net_generation_mwh < 0 THEN 1 END) AS negative_generation_months,
    COUNT(*) AS total_reported_months,
    ROUND(
        COUNT(CASE WHEN f.net_generation_mwh < 0 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2
    ) AS outage_month_pct,
    ROUND(SUM(CASE WHEN f.net_generation_mwh < 0 THEN f.net_generation_mwh ELSE 0 END), 2) AS total_auxiliary_consumed_mwh,
    ROUND(SUM(f.fuel_consumed_mmbtu), 2) AS auxiliary_fuel_consumed_mmbtu
FROM gold_warehouse.fact_monthly_plant_operations f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY 
    d.calendar_year,
    p.orispl_code,
    p.plant_name,
    p.state_code,
    f.prime_mover_code
HAVING COUNT(CASE WHEN f.net_generation_mwh < 0 THEN 1 END) > 0
ORDER BY d.calendar_year, total_auxiliary_consumed_mwh ASC;


-- ==============================================================================
-- 8. CROSS-AGENCY GENERATION RECONCILIATION & AUXILIARY RATIO AUDIT (ANSWERS BQ6)
-- Analytical Question: BQ6 - Physical Reconciliation of EPA Gross vs EIA Net Gen
-- Fact Tables: fact_hourly_emissions_weather, fact_monthly_plant_operations
-- Dimensions:  dim_plant, dim_date
-- Measures:    total_gross_mw, total_net_mwh, aux_ratio_pct
-- Business Intent: Validates thermodynamic law: Gross Generation (CAMPD) >= Net Generation (EIA-923)
--                  with expected auxiliary station ratio between 3% and 14%.
-- ==============================================================================
WITH epa_monthly_gross AS (
    SELECT 
        f.plant_key,
        d.calendar_year,
        d.calendar_month,
        SUM(f.gross_load_mw) AS total_gross_mw
    FROM gold_warehouse.fact_hourly_emissions_weather f
    JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY f.plant_key, d.calendar_year, d.calendar_month
),
eia_monthly_net AS (
    SELECT 
        f.plant_key,
        d.calendar_year,
        d.calendar_month,
        SUM(f.net_generation_mwh) AS total_net_mwh
    FROM gold_warehouse.fact_monthly_plant_operations f
    JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
    GROUP BY f.plant_key, d.calendar_year, d.calendar_month
)
SELECT 
    p.orispl_code,
    p.plant_name,
    p.state_code,
    g.calendar_year,
    g.calendar_month,
    ROUND(g.total_gross_mw, 2) AS epa_gross_generation_mw,
    ROUND(n.total_net_mwh, 2) AS eia_net_generation_mwh,
    ROUND(g.total_gross_mw - n.total_net_mwh, 2) AS auxiliary_load_mwh,
    ROUND(
        (g.total_gross_mw - n.total_net_mwh) / NULLIF(g.total_gross_mw, 0) * 100.0, 2
    ) AS auxiliary_load_ratio_pct,
    CASE 
        WHEN n.total_net_mwh > g.total_gross_mw THEN 'PHYSICAL_VIOLATION_NET_EXCEEDS_GROSS'
        WHEN (g.total_gross_mw - n.total_net_mwh) / NULLIF(g.total_gross_mw, 0) BETWEEN 0.03 AND 0.14 THEN 'PHYSICAL_STANDARD_3_TO_14_PCT'
        ELSE 'AUXILIARY_ANOMALY_OUTSIDE_BOUNDS'
    END AS thermodynamic_reconciliation_status
FROM epa_monthly_gross g
JOIN eia_monthly_net n ON g.plant_key = n.plant_key 
                      AND g.calendar_year = n.calendar_year 
                      AND g.calendar_month = n.calendar_month
JOIN gold_warehouse.dim_plant p ON g.plant_key = p.plant_key
ORDER BY g.calendar_year, g.calendar_month, p.orispl_code;


-- ==============================================================================
-- 9. SCD TYPE 2 GENERATOR DECOMMISSIONING & RETIREMENT TRAJECTORY (ANSWERS BQ7)
-- Analytical Question: BQ7 - Generator Asset Lifecycle & SCD Type 2 Tracking
-- Dimension:   dim_generator (SCD Type 2), dim_plant
-- Measures:    nameplate_capacity_mw, historical_version_count, cumulative_retired_mw
-- Business Intent: Measures coal and gas generating unit retirements vs additions
--                  over the 2021-2024 compliance timeline.
-- ==============================================================================
SELECT 
    g.orispl_code,
    p.plant_name,
    g.generator_id,
    g.prime_mover_code,
    g.primary_energy_source,
    g.operating_status AS current_operating_status,
    g.nameplate_capacity_mw,
    g.valid_from,
    g.valid_to,
    g.is_current,
    COUNT(*) OVER (PARTITION BY g.orispl_code, g.generator_id) AS total_historical_revisions,
    CASE 
        WHEN g.operating_status IN ('RE', 'RET', 'RETIRED') THEN 'DECOMMISSIONED_ASSET'
        WHEN g.operating_status IN ('SB', 'STANDBY') THEN 'STANDBY_RESERVE'
        WHEN g.operating_status IN ('OP', 'OPERATING') THEN 'ACTIVE_COMMERCIAL_OPERATION'
        ELSE 'OTHER_LIFECYCLE_STATE'
    END AS asset_lifecycle_category
FROM gold_warehouse.dim_generator g
LEFT JOIN gold_warehouse.dim_plant p ON g.orispl_code = p.orispl_code
WHERE g.generator_key <> -1
ORDER BY g.orispl_code, g.generator_id, g.valid_from;


-- ==============================================================================
-- 10. CLIMATIC STRESS GRID DISPATCH & RESERVE MARGIN WINDOW ANALYSIS (ANSWERS BQ8)
-- Analytical Question: BQ8 - Extreme Climatic Stress vs Regional Grid Dispatch
-- Fact Tables: fact_regional_grid_demand, fact_hourly_emissions_weather
-- Shared Grain: Hourly per Balancing Authority (date_key, hour_of_day, ba_code)
-- Dimensions:  dim_balancing_authority, dim_plant, dim_date
-- Measures:    demand_mw, demand_forecast_mw, net_gen_gas_mw, net_gen_coal_mw, gross_load_mw
-- Business Intent: Pre-aggregates both facts separately in CTEs to the shared BA-hour
--                  grain before joining, avoiding multi-fact Cartesian fan-out.
-- ==============================================================================
WITH hourly_grid_demand AS (
    SELECT 
        g.date_key,
        g.hour_of_day,
        ba.ba_code,
        ba.ba_name,
        ba.region AS nerc_region,
        AVG(g.demand_mw) AS demand_mw,
        AVG(g.demand_forecast_mw) AS demand_forecast_mw,
        SUM(COALESCE(g.net_gen_gas_mw, 0) + COALESCE(g.net_gen_coal_mw, 0)) AS grid_thermal_dispatch_mw,
        SUM(COALESCE(g.net_gen_wind_mw, 0) + COALESCE(g.net_gen_solar_mw, 0)) AS grid_renewable_dispatch_mw
    FROM gold_warehouse.fact_regional_grid_demand g
    JOIN gold_warehouse.dim_balancing_authority ba ON g.ba_key = ba.ba_key
    GROUP BY g.date_key, g.hour_of_day, ba.ba_code, ba.ba_name, ba.region
),
hourly_ba_emissions AS (
    SELECT 
        f.date_key,
        f.hour_of_day,
        p.ba_code,
        SUM(f.gross_load_mw) AS plant_gross_generation_mw,
        SUM(f.co2_mass_tons) AS plant_co2_tons,
        AVG(f.ambient_temp_celsius) AS avg_ambient_temp_celsius
    FROM gold_warehouse.fact_hourly_emissions_weather f
    JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
    GROUP BY f.date_key, f.hour_of_day, p.ba_code
)
SELECT 
    d.calendar_date,
    g.hour_of_day,
    g.ba_code,
    g.ba_name,
    g.nerc_region,
    CASE 
        WHEN d.is_winter_freeze = TRUE THEN 'WINTER_FREEZE_EVENT'
        WHEN d.is_summer_peak = TRUE THEN 'SUMMER_PEAK_HEAT_DOME'
        ELSE 'STANDARD_CLIMATIC_CONDITIONS'
    END AS climatic_stress_event,
    ROUND(g.demand_mw, 2) AS demand_mw,
    ROUND(g.demand_forecast_mw, 2) AS demand_forecast_mw,
    ROUND(g.demand_mw - g.demand_forecast_mw, 2) AS forecast_residual_error_mw,
    ROUND(g.grid_thermal_dispatch_mw, 2) AS grid_thermal_dispatch_mw,
    ROUND(COALESCE(e.plant_gross_generation_mw, 0.0), 2) AS plant_monitored_gross_mw,
    ROUND(COALESCE(e.plant_co2_tons, 0.0), 2) AS plant_co2_tons,
    ROUND(e.avg_ambient_temp_celsius, 1) AS avg_ambient_temp_celsius,
    -- 24-Hour Rolling Average Demand within Balancing Authority
    ROUND(
        AVG(g.demand_mw) OVER (
            PARTITION BY g.ba_code 
            ORDER BY g.date_key, g.hour_of_day 
            ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_24hr_avg_demand_mw,
    -- Rank hourly peak stress within each climatic stress event
    DENSE_RANK() OVER (
        PARTITION BY g.ba_code, d.is_winter_freeze, d.is_summer_peak 
        ORDER BY (g.demand_mw - g.demand_forecast_mw) DESC
    ) AS underforecast_stress_rank
FROM hourly_grid_demand g
JOIN gold_warehouse.dim_date d ON g.date_key = d.date_key
LEFT JOIN hourly_ba_emissions e ON g.date_key = e.date_key 
                                AND g.hour_of_day = e.hour_of_day 
                                AND g.ba_code = e.ba_code
WHERE d.is_winter_freeze = TRUE OR d.is_summer_peak = TRUE
ORDER BY forecast_residual_error_mw DESC;


-- ==============================================================================
-- 11. THERMAL EFFICIENCY DEGRADATION & HEAT-RATE EXCEEDANCE FREQUENCY (ANSWERS BQ9)
-- Analytical Question: BQ9 - Plant Thermal Degradation & Out-of-Bounds Heat Rate Months
-- Fact Tables: fact_monthly_plant_operations, fact_hourly_emissions_weather
-- Shared Grain: Annual per Generating Facility (calendar_year, plant_key)
-- Dimensions:  dim_plant, dim_date
-- Measures:    avg_heat_rate_btu_kwh, degraded_operating_months, annual_fuel_mmbtu
-- Business Intent: Reconciles monthly heat rate degradation with annual emissions
--                  by pre-aggregating each fact in a CTE before joining.
-- ==============================================================================
WITH plant_monthly_thermal_ops AS (
    SELECT 
        f.plant_key,
        d.calendar_year,
        f.prime_mover_code,
        f.energy_source_code,
        COUNT(*) AS total_operating_months,
        SUM(f.net_generation_mwh) AS annual_net_generation_mwh,
        SUM(f.fuel_consumed_mmbtu) AS annual_fuel_consumed_mmbtu,
        ROUND(
            SUM(f.fuel_consumed_mmbtu * 1000.0) / NULLIF(SUM(f.net_generation_mwh), 0), 2
        ) AS weighted_heat_rate_btu_kwh,
        COUNT(CASE 
            WHEN f.prime_mover_code = 'CC' AND f.avg_heat_rate_btu_kwh > 10000 THEN 1
            WHEN f.prime_mover_code = 'ST' AND f.avg_heat_rate_btu_kwh > 14000 THEN 1
            WHEN f.prime_mover_code = 'GT' AND f.avg_heat_rate_btu_kwh > 16000 THEN 1
            ELSE NULL
        END) AS degraded_efficiency_months_count
    FROM gold_warehouse.fact_monthly_plant_operations f
    JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
    GROUP BY f.plant_key, d.calendar_year, f.prime_mover_code, f.energy_source_code
),
plant_annual_emissions_summary AS (
    SELECT 
        f.plant_key,
        d.calendar_year,
        SUM(f.gross_load_mw) AS total_gross_mw,
        SUM(f.co2_mass_tons) AS total_co2_tons
    FROM gold_warehouse.fact_hourly_emissions_weather f
    JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY f.plant_key, d.calendar_year
)
SELECT 
    t.calendar_year,
    p.orispl_code,
    p.plant_name,
    p.state_code,
    t.prime_mover_code,
    t.energy_source_code,
    t.total_operating_months,
    t.degraded_efficiency_months_count,
    ROUND(
        t.degraded_efficiency_months_count * 100.0 / NULLIF(t.total_operating_months, 0), 1
    ) AS degraded_operating_pct,
    t.annual_net_generation_mwh,
    t.annual_fuel_consumed_mmbtu,
    t.weighted_heat_rate_btu_kwh,
    ROUND(COALESCE(e.total_co2_tons, 0.0), 2) AS annual_co2_tons,
    CASE 
        WHEN t.degraded_efficiency_months_count >= 3 THEN 'CHRONIC_THERMAL_DEGRADATION'
        WHEN t.degraded_efficiency_months_count > 0 THEN 'MODERATE_EFFICIENCY_ALERT'
        ELSE 'NORMAL_EFFICIENCY_DISPATCH'
    END AS fleet_efficiency_status
FROM plant_monthly_thermal_ops t
JOIN gold_warehouse.dim_plant p ON t.plant_key = p.plant_key
LEFT JOIN plant_annual_emissions_summary e ON t.plant_key = e.plant_key 
                                           AND t.calendar_year = e.calendar_year
ORDER BY t.calendar_year, t.degraded_efficiency_months_count DESC, t.weighted_heat_rate_btu_kwh DESC;



