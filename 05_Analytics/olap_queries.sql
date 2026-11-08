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
-- 1. MULTI-DIMENSIONAL OLAP CUBE: Generation & Heat Rate by Geography & Fuel Mix
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
-- 2. HIERARCHICAL OLAP ROLLUP: Temporal & Spatial Grid Demand Slicing
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
-- 3. WINDOW FUNCTIONS: Month-Over-Month Ramp Rate, Growth % & Prior Year Lag
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
-- 4. WINDOW FUNCTIONS: Facility Emissions Intensity Benchmarking & Dense Ranking
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

