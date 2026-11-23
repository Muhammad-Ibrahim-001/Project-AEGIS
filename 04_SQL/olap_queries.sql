-- ==============================================================================
-- DL3004 DATA WAREHOUSING & BUSINESS INTELLIGENCE — PHASE 3
-- Technology: Databricks Serverless Cloud Lakehouse (dwbi_catalog) / PostgreSQL 16
-- Deliverable: OLAP Queries Layer (ROLLUP, CUBE & Analytical Aggregations)
-- Aligned Rubric: Phase 3 Section 1 (OLAP Implementation - 5 Marks)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. OLAP QUERY 1: HIERARCHICAL MULTI-LEVEL ROLLUP
-- ------------------------------------------------------------------------------
-- Business Objective:
-- Evaluates bulk electric generation, thermal fuel consumption, and emission
-- totals across a 3-level geographical hierarchy:
-- Level 3: Balancing Authority Region (NERC Interconnection / Regional Grid)
--   ↓ Level 2: State
--     ↓ Level 1: Power Plant
--
-- The ROLLUP operator automatically computes:
-- 1. Plant-level sub-totals
-- 2. State-level regional sub-totals
-- 3. Balancing Authority grand sub-totals
-- 4. National Fleetwide Grand Total

SELECT 
    COALESCE(b.ba_code, 'ALL REGIONS') AS balancing_authority,
    COALESCE(p.state, 'ALL STATES') AS state,
    COALESCE(p.plant_name, 'ALL PLANTS (SUBTOTAL)') AS plant_name,
    COUNT(DISTINCT m.snapshot_key) AS operational_months_reported,
    ROUND(SUM(m.net_generation_mwh), 2) AS total_generation_mwh,
    ROUND(SUM(m.fuel_consumed_mmbtu), 2) AS total_fuel_mmbtu,
    ROUND(AVG(m.avg_heat_rate_btu_kwh), 2) AS avg_heat_rate_btu_kwh
FROM dwbi_catalog.gold_warehouse.fact_monthly_plant_operations m
JOIN dwbi_catalog.gold_warehouse.dim_plant p 
    ON m.plant_key = p.plant_key
JOIN dwbi_catalog.gold_warehouse.dim_balancing_authority b 
    ON p.ba_code = b.ba_code
JOIN dwbi_catalog.gold_warehouse.dim_date d 
    ON m.month_start_date_key = d.date_key
WHERE d.calendar_year = 2024
GROUP BY ROLLUP (b.ba_code, p.state, p.plant_name)
ORDER BY 
    b.ba_code NULLS LAST, 
    p.state NULLS LAST, 
    total_generation_mwh DESC;


-- ------------------------------------------------------------------------------
-- 2. OLAP QUERY 2: MULTI-DIMENSIONAL CUBE ANALYSIS
-- ------------------------------------------------------------------------------
-- Business Objective:
-- Computes the full dimensional lattice (all 2^N subtotal combinations)
-- across Energy Fuel Type × Calendar Quarter × Prime Mover Technology:
-- Dimensions analyzed:
--   1. Energy Source Code (COAL, NG, NUC, WND, SUN, WAT)
--   2. Calendar Quarter (Q1, Q2, Q3, Q4)
--   3. Prime Mover Code (CA = Combined Cycle Steam, CT = Combustion Turbine, ST = Steam Turbine)
--
-- The CUBE operator evaluates:
-- - (Energy Source, Quarter, Prime Mover)
-- - (Energy Source, Quarter)
-- - (Energy Source, Prime Mover)
-- - (Quarter, Prime Mover)
-- - (Energy Source)
-- - (Quarter)
-- - (Prime Mover)
-- - () Fleetwide Grand Total

SELECT 
    CASE 
        WHEN GROUPING(m.energy_source_code) = 1 THEN 'ALL FUELS'
        ELSE m.energy_source_code 
    END AS energy_fuel_source,
    CASE 
        WHEN GROUPING(d.fiscal_quarter) = 1 THEN 'ALL QUARTERS'
        ELSE CONCAT('Q', CAST(d.fiscal_quarter AS STRING))
    END AS calendar_quarter,
    CASE 
        WHEN GROUPING(m.prime_mover_code) = 1 THEN 'ALL TECHNOLOGIES'
        ELSE m.prime_mover_code 
    END AS prime_mover_tech,
    COUNT(*) AS total_monthly_records,
    ROUND(SUM(m.net_generation_mwh), 2) AS total_generation_mwh,
    ROUND(SUM(m.fuel_consumed_mmbtu), 2) AS total_fuel_mmbtu,
    ROUND(AVG(m.avg_heat_rate_btu_kwh), 2) AS avg_heat_rate_btu_kwh
FROM dwbi_catalog.gold_warehouse.fact_monthly_plant_operations m
JOIN dwbi_catalog.gold_warehouse.dim_date d 
    ON m.month_start_date_key = d.date_key
WHERE d.calendar_year = 2024
GROUP BY CUBE (m.energy_source_code, d.fiscal_quarter, m.prime_mover_code)
ORDER BY 
    GROUPING(m.energy_source_code), 
    GROUPING(d.fiscal_quarter), 
    GROUPING(m.prime_mover_code), 
    total_generation_mwh DESC;


-- ------------------------------------------------------------------------------
-- 3. OLAP QUERY 3: EMISSIONS INTENSITY CUBE (WEATHER × TIME OF DAY)
-- ------------------------------------------------------------------------------
-- Business Objective:
-- Analyzes peak atmospheric emissions intensity across Weather Temperature Bands
-- and Diurnal Peak Demand windows (Peak vs Shoulder vs Off-Peak hours).

SELECT 
    CASE 
        WHEN GROUPING(
            CASE 
                WHEN f.temperature_celsius < 0 THEN '1. Freezing (<0C)'
                WHEN f.temperature_celsius BETWEEN 0 AND 15 THEN '2. Moderate (0-15C)'
                WHEN f.temperature_celsius BETWEEN 15 AND 30 THEN '3. Warm (15-30C)'
                ELSE '4. Extreme Heat (>30C)'
            END
        ) = 1 THEN 'ALL TEMPERATURE BANDS'
        ELSE CASE 
                WHEN f.temperature_celsius < 0 THEN '1. Freezing (<0C)'
                WHEN f.temperature_celsius BETWEEN 0 AND 15 THEN '2. Moderate (0-15C)'
                WHEN f.temperature_celsius BETWEEN 15 AND 30 THEN '3. Warm (15-30C)'
                ELSE '4. Extreme Heat (>30C)'
             END
    END AS temperature_band,
    CASE 
        WHEN GROUPING(
            CASE 
                WHEN d.hour_of_day BETWEEN 14 AND 19 THEN 'Peak (14:00 - 19:00)'
                WHEN d.hour_of_day BETWEEN 7 AND 13 THEN 'Morning Ramp (07:00 - 13:00)'
                ELSE 'Off-Peak / Night'
            END
        ) = 1 THEN 'ALL DIURNAL INTERVALS'
        ELSE CASE 
                WHEN d.hour_of_day BETWEEN 14 AND 19 THEN 'Peak (14:00 - 19:00)'
                WHEN d.hour_of_day BETWEEN 7 AND 13 THEN 'Morning Ramp (07:00 - 13:00)'
                ELSE 'Off-Peak / Night'
             END
    END AS diurnal_demand_window,
    COUNT(*) AS hourly_observations_count,
    ROUND(SUM(f.gross_load_mw), 2) AS total_gross_generation_mwh,
    ROUND(SUM(f.co2_mass_tons), 2) AS total_co2_tons,
    ROUND(SUM(f.so2_mass_lbs), 2) AS total_so2_lbs,
    ROUND(SUM(f.nox_mass_lbs), 2) AS total_nox_lbs,
    ROUND(SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0), 4) AS carbon_intensity_tons_per_mwh
FROM dwbi_catalog.gold_warehouse.fact_hourly_emissions_weather f
JOIN dwbi_catalog.gold_warehouse.dim_date d 
    ON f.date_key = d.date_key
GROUP BY CUBE (
    CASE 
        WHEN f.temperature_celsius < 0 THEN '1. Freezing (<0C)'
        WHEN f.temperature_celsius BETWEEN 0 AND 15 THEN '2. Moderate (0-15C)'
        WHEN f.temperature_celsius BETWEEN 15 AND 30 THEN '3. Warm (15-30C)'
        ELSE '4. Extreme Heat (>30C)'
    END,
    CASE 
        WHEN d.hour_of_day BETWEEN 14 AND 19 THEN 'Peak (14:00 - 19:00)'
        WHEN d.hour_of_day BETWEEN 7 AND 13 THEN 'Morning Ramp (07:00 - 13:00)'
        ELSE 'Off-Peak / Night'
    END
)
ORDER BY 
    total_co2_tons DESC;
