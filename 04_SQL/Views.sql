-- ==============================================================================
-- DL3004 DWBI Final Project: Reporting Views & Gold Layer Data Marts
-- Platform: Databricks Serverless Compute / Databricks SQL Warehouse
-- Catalog: dwbi_catalog
-- Schema:  gold_marts
-- Aligned with: DWBI Lab Phase 3 Specifications (Power BI DirectQuery Views)
-- ==============================================================================

CREATE CATALOG IF NOT EXISTS dwbi_catalog;
USE CATALOG dwbi_catalog;

CREATE SCHEMA IF NOT EXISTS gold_marts;

-- ------------------------------------------------------------------------------
-- 1. vw_emissions_intensity (Hourly Air Quality & CO2/SO2/NOx Rates)
-- Feeds Power BI Page 1 (Executive Overview)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_marts.vw_emissions_intensity AS
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
FROM gold_warehouse.fact_hourly_emissions_weather f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
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
-- Feeds Power BI Page 2 (Detailed Engineering Analysis)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_marts.vw_plant_performance AS
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
    ROUND(AVG(f.avg_heat_rate_btu_kwh), 2) AS avg_heat_rate_btu_kwh,
    ROUND(AVG(f.delivered_fuel_cost_per_mmbtu), 2) AS avg_delivered_fuel_cost,
    CASE 
        WHEN SUM(f.net_generation_mwh) < 0 THEN 'STATION_OUTAGE_AUXILIARY_LOAD'
        WHEN AVG(f.avg_heat_rate_btu_kwh) < 7000 THEN 'HIGH_EFFICIENCY_BASELOAD'
        WHEN AVG(f.avg_heat_rate_btu_kwh) > 12000 THEN 'LOW_EFFICIENCY_PEAKER'
        ELSE 'STANDARD_OPERATIONAL'
    END AS operational_category
FROM gold_warehouse.fact_monthly_plant_operations f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
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
-- 3. vw_grid_stress (Hourly Balancing Authority Demand & Fuel Dispatch)
-- Feeds Power BI Page 3 (Grid Decision Support)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_marts.vw_grid_stress AS
SELECT 
    d.calendar_year,
    d.calendar_month,
    d.calendar_date,
    g.hour_of_day,
    ba.ba_code,
    ba.ba_name,
    ba.region AS nerc_region,
    g.demand_mw,
    g.demand_forecast_mw,
    (g.demand_mw - g.demand_forecast_mw) AS demand_forecast_residual_mw,
    g.net_gen_coal_mw,
    g.net_gen_gas_mw,
    g.net_gen_nuclear_mw,
    g.net_gen_hydro_mw,
    g.net_gen_wind_mw,
    g.net_gen_solar_mw,
    (g.net_gen_wind_mw + g.net_gen_solar_mw) AS total_renewable_generation_mw,
    ROUND(
        (g.net_gen_wind_mw + g.net_gen_solar_mw) / NULLIF(g.demand_mw, 0) * 100, 2
    ) AS renewable_penetration_pct,
    g.net_interchange_mw
FROM gold_warehouse.fact_regional_grid_demand g
JOIN gold_warehouse.dim_balancing_authority ba ON g.ba_key = ba.ba_key
JOIN gold_warehouse.dim_date d ON g.date_key = d.date_key;

-- ------------------------------------------------------------------------------
-- 4. vw_monthly_generation_mix (Monthly Prime Mover & Fuel Generation Trends)
-- Feeds Power BI Page 2 & Long-Term Fleet Decarbonization Analysis (BQ10)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_marts.vw_monthly_generation_mix AS
SELECT 
    d.calendar_year,
    d.calendar_month,
    d.month_name,
    p.state_code,
    f.prime_mover_code,
    f.energy_source_code,
    SUM(f.net_generation_mwh) AS total_net_generation_mwh,
    SUM(f.fuel_consumed_mmbtu) AS total_fuel_mmbtu,
    ROUND(
        SUM(f.fuel_consumed_mmbtu * 1000.0) / NULLIF(SUM(f.net_generation_mwh), 0), 2
    ) AS weighted_heat_rate_btu_kwh,
    COUNT(DISTINCT f.plant_key) AS active_plants_count
FROM gold_warehouse.fact_monthly_plant_operations f
JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY 
    d.calendar_year,
    d.calendar_month,
    d.month_name,
    p.state_code,
    f.prime_mover_code,
    f.energy_source_code;

