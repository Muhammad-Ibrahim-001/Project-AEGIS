-- ==============================================================================
-- DL3004 DWBI Final Project: Reporting Views & Gold Layer Data Marts
-- Target Engine: PostgreSQL 14+
-- Schema: project_reporting
-- Aligned with: DWBI Lab Phase 3 Specifications
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS project_reporting;

-- ------------------------------------------------------------------------------
-- 1. vw_emissions_intensity (Hourly Air Quality & CO2/SO2/NOx Rates)
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS project_reporting.vw_emissions_intensity CASCADE;
CREATE VIEW project_reporting.vw_emissions_intensity AS
SELECT 
    d.calendar_year,
    d.calendar_month,
    d.calendar_date,
    p.orispl_code,
    p.plant_name,
    p.state_code,
    p.ba_code,
    SUM(f.gross_load_mw) AS total_gross_mw,
    SUM(f.co2_mass_tons) AS total_co2_tons,
    SUM(f.so2_mass_lbs)  AS total_so2_lbs,
    SUM(f.nox_mass_lbs)  AS total_nox_lbs,
    ROUND(
        SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0), 4
    ) AS co2_intensity_tons_per_mw,
    ROUND(
        AVG(f.ambient_temp_celsius), 2
    ) AS avg_ambient_temp_celsius
FROM project_dw.fact_hourly_emissions_weather f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
JOIN project_dw.dim_date d ON f.date_key = d.date_key
GROUP BY 
    d.calendar_year,
    d.calendar_month,
    d.calendar_date,
    p.orispl_code,
    p.plant_name,
    p.state_code,
    p.ba_code;

-- ------------------------------------------------------------------------------
-- 2. vw_plant_performance (Monthly Fuel Consumption, NetGen & Heat Rate)
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS project_reporting.vw_plant_performance CASCADE;
CREATE VIEW project_reporting.vw_plant_performance AS
SELECT 
    d.calendar_year,
    d.month_name,
    p.orispl_code,
    p.plant_name,
    p.utility_name,
    p.state_code,
    f.prime_mover_code,
    f.energy_source_code,
    SUM(f.net_generation_mwh) AS net_generation_mwh,
    SUM(f.fuel_consumed_mmbtu) AS total_fuel_mmbtu,
    ROUND(AVG(f.avg_heat_rate_btu_kwh), 2) AS avg_heat_rate,
    ROUND(AVG(f.delivered_fuel_cost_per_mmbtu), 2) AS avg_delivered_fuel_cost,
    CASE 
        WHEN SUM(f.net_generation_mwh) < 0 THEN 'STATION_SERVICE_EXCEEDS_OUTPUT'
        ELSE 'NORMAL_GENERATION'
    END AS operational_state
FROM project_dw.fact_monthly_plant_operations f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
JOIN project_dw.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY 
    d.calendar_year,
    d.month_name,
    p.orispl_code,
    p.plant_name,
    p.utility_name,
    p.state_code,
    f.prime_mover_code,
    f.energy_source_code;

-- ------------------------------------------------------------------------------
-- 3. vw_monthly_generation (Regional Grid Dispatch & Renewable Share)
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS project_reporting.vw_monthly_generation CASCADE;
CREATE VIEW project_reporting.vw_monthly_generation AS
SELECT 
    d.calendar_year,
    d.calendar_month,
    ba.ba_code,
    ba.ba_name,
    ROUND(AVG(g.demand_mw), 2) AS avg_hourly_demand_mw,
    ROUND(MAX(g.demand_mw), 2) AS peak_hourly_demand_mw,
    ROUND(SUM(g.net_gen_coal_mw), 2) AS total_coal_mwh,
    ROUND(SUM(g.net_gen_gas_mw), 2) AS total_gas_mwh,
    ROUND(SUM(g.net_gen_nuclear_mw), 2) AS total_nuclear_mwh,
    ROUND(SUM(g.net_gen_wind_mw + g.net_gen_solar_mw), 2) AS total_clean_renewable_mwh,
    ROUND(
        (SUM(g.net_gen_wind_mw + g.net_gen_solar_mw) / NULLIF(SUM(g.demand_mw), 0)) * 100, 2
    ) AS renewable_penetration_pct
FROM project_dw.fact_regional_grid_demand g
JOIN project_dw.dim_balancing_authority ba ON g.ba_key = ba.ba_key
JOIN project_dw.dim_date d ON g.date_key = d.date_key
GROUP BY 
    d.calendar_year,
    d.calendar_month,
    ba.ba_code,
    ba.ba_name;
