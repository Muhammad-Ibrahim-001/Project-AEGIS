-- ==============================================================================
-- DL3004 DWBI Final Project: OLAP Analytical Queries
-- Schema: project_dw
-- Aligned with: DWBI Lab Phase 3 Specifications (ROLLUP, CUBE, Window Functions)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. OLAP CUBE: Monthly Generation & Heat Rate by Geography and Fuel Source
-- ------------------------------------------------------------------------------
SELECT 
    d.calendar_year,
    p.state_code,
    f.energy_source_code,
    COUNT(DISTINCT f.plant_key) AS active_plants_count,
    ROUND(SUM(f.net_generation_mwh), 2) AS total_net_generation_mwh,
    ROUND(AVG(f.avg_heat_rate_btu_kwh), 2) AS weighted_avg_heat_rate
FROM project_dw.fact_monthly_plant_operations f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
JOIN project_dw.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY CUBE (d.calendar_year, p.state_code, f.energy_source_code)
ORDER BY d.calendar_year NULLS LAST, p.state_code NULLS LAST, f.energy_source_code NULLS LAST;

-- ------------------------------------------------------------------------------
-- 2. OLAP ROLLUP: Hierarchical Aggregation of Grid Demand (Year -> Quarter -> Month)
-- ------------------------------------------------------------------------------
SELECT 
    d.calendar_year,
    d.calendar_quarter,
    d.calendar_month,
    ba.ba_code,
    ROUND(AVG(g.demand_mw), 2) AS avg_hourly_demand_mw,
    ROUND(MAX(g.demand_mw), 2) AS peak_hourly_demand_mw,
    ROUND(SUM(g.net_gen_wind_mw + g.net_gen_solar_mw), 2) AS total_renewable_generation_mwh
FROM project_dw.fact_regional_grid_demand g
JOIN project_dw.dim_balancing_authority ba ON g.ba_key = ba.ba_key
JOIN project_dw.dim_date d ON g.date_key = d.date_key
GROUP BY ROLLUP (d.calendar_year, d.calendar_quarter, d.calendar_month, ba.ba_code)
ORDER BY d.calendar_year NULLS LAST, d.calendar_quarter NULLS LAST, d.calendar_month NULLS LAST;

-- ------------------------------------------------------------------------------
-- 3. WINDOW FUNCTIONS: Month-Over-Month Ramp Rate & Growth %
-- ------------------------------------------------------------------------------
WITH monthly_plant_metrics AS (
    SELECT 
        f.plant_key,
        p.plant_name,
        d.calendar_year,
        d.calendar_month,
        SUM(f.net_generation_mwh) AS current_net_mwh,
        LAG(SUM(f.net_generation_mwh), 1) OVER (
            PARTITION BY f.plant_key 
            ORDER BY d.calendar_year, d.calendar_month
        ) AS previous_month_net_mwh
    FROM project_dw.fact_monthly_plant_operations f
    JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
    JOIN project_dw.dim_date d ON f.month_start_date_key = d.date_key
    GROUP BY f.plant_key, p.plant_name, d.calendar_year, d.calendar_month
)
SELECT 
    plant_key,
    plant_name,
    calendar_year,
    calendar_month,
    current_net_mwh,
    previous_month_net_mwh,
    ROUND(current_net_mwh - previous_month_net_mwh, 2) AS mom_net_delta_mwh,
    ROUND(
        ((current_net_mwh - previous_month_net_mwh) / NULLIF(previous_month_net_mwh, 0)) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_plant_metrics
ORDER BY plant_key, calendar_year, calendar_month;
