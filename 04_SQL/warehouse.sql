-- ==============================================================================
-- DL3004 DWBI Final Project: Databricks Serverless Lakehouse Warehouse DDL
-- Platform: Databricks Serverless Compute / Databricks SQL Warehouse
-- Catalog: dwbi_catalog
-- Schema:  gold_warehouse
-- Storage: Delta Lake (ACID, Liquid Clustering)
-- ==============================================================================

CREATE CATALOG IF NOT EXISTS dwbi_catalog;
USE CATALOG dwbi_catalog;

CREATE SCHEMA IF NOT EXISTS gold_warehouse;

-- ------------------------------------------------------------------------------
-- 1. CONFORMED DIMENSIONS (WITH SURROGATE KEYS & IDENTITY COLUMNS)
-- ------------------------------------------------------------------------------

-- Dim_Date
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_date (
    date_key             INT NOT NULL,          -- Format: YYYYMMDD
    calendar_date        DATE NOT NULL,
    calendar_year        INT NOT NULL,
    calendar_quarter     INT NOT NULL,
    calendar_month       INT NOT NULL,
    month_name           STRING NOT NULL,
    day_of_month         INT NOT NULL,
    day_of_week          INT NOT NULL,
    day_name             STRING NOT NULL,
    is_weekend           BOOLEAN NOT NULL,
    season_name          STRING,
    is_summer_peak       BOOLEAN,
    is_winter_freeze     BOOLEAN,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
) USING DELTA;

-- Dim_Balancing_Authority (Regional Grid Operators)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_balancing_authority (
    ba_key               BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    ba_code              STRING NOT NULL,                     -- Natural Business Key
    ba_name              STRING NOT NULL,
    region               STRING,
    is_active            BOOLEAN DEFAULT TRUE,
    CONSTRAINT pk_dim_ba PRIMARY KEY (ba_key)
) USING DELTA;

-- Dim_Plant (Power Plant Facilities)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_plant (
    plant_key            BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    orispl_code          INT NOT NULL,                        -- Natural Business Key
    plant_name           STRING NOT NULL,
    utility_id           INT,
    utility_name         STRING,
    latitude             DECIMAL(9, 6),
    longitude            DECIMAL(9, 6),
    state_code           STRING NOT NULL,
    county_name          STRING,
    ba_code              STRING,
    epa_region           INT,
    is_combined_heat_power BOOLEAN DEFAULT FALSE,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_dim_plant PRIMARY KEY (plant_key)
) USING DELTA;

-- Dim_Generator (SCD Type 2: Unit Operating Status & Capacity Evolution)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_generator (
    generator_key        BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    orispl_code          INT NOT NULL,                        -- Natural Business Key
    generator_id         STRING NOT NULL,                     -- Natural Business Key
    prime_mover_code     STRING NOT NULL,
    primary_energy_source STRING NOT NULL,
    nameplate_capacity_mw DECIMAL(10, 2),
    operating_status     STRING NOT NULL, -- OP (Operating), SB (Standby), RE (Retired)
    valid_from           TIMESTAMP NOT NULL,
    valid_to             TIMESTAMP DEFAULT TIMESTAMP('9999-12-31 23:59:59'),
    is_current           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_generator PRIMARY KEY (generator_key)
) USING DELTA;

-- Dim_Weather_Station
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_weather_station (
    station_key          BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    station_id           STRING NOT NULL,                     -- Natural Business Key
    station_name         STRING,
    state_code           STRING,
    latitude             DECIMAL(9, 6),
    longitude            DECIMAL(9, 6),
    elevation_m          DECIMAL(7, 2),
    CONSTRAINT pk_dim_station PRIMARY KEY (station_key)
) USING DELTA;

-- ------------------------------------------------------------------------------
-- 2. MULTI-GRAIN FACT TABLES (KIMBALL THREE ARCHETYPES WITH LIQUID CLUSTERING)
-- ------------------------------------------------------------------------------

-- FACT 1 (Transactional Fact): Hourly Smokestack Emissions & Weather Observations
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_hourly_emissions_weather (
    date_key             INT NOT NULL,
    hour_of_day          INT NOT NULL,
    plant_key            BIGINT NOT NULL,
    unit_id              STRING NOT NULL,
    station_key          BIGINT,
    gross_load_mw        DECIMAL(10, 2),
    heat_input_mmbtu     DECIMAL(12, 3),
    so2_mass_lbs         DECIMAL(12, 3),
    nox_mass_lbs         DECIMAL(12, 3),
    co2_mass_tons        DECIMAL(12, 3),
    ambient_temp_celsius DECIMAL(5, 2),
    wind_speed_mps       DECIMAL(5, 2),
    weather_distance_km  DECIMAL(6, 2)
) USING DELTA
CLUSTER BY (date_key, plant_key);

-- FACT 2 (Periodic Snapshot Fact): Monthly Plant Fuel Consumption & Net Generation
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_monthly_plant_operations (
    snapshot_key         BIGINT GENERATED ALWAYS AS IDENTITY,
    month_start_date_key INT NOT NULL,
    plant_key            BIGINT NOT NULL,
    prime_mover_code     STRING NOT NULL,
    energy_source_code   STRING NOT NULL,
    net_generation_mwh   DECIMAL(14, 3) NOT NULL, -- May be negative during plant maintenance outages
    fuel_consumed_physical DECIMAL(14, 3),
    fuel_consumed_mmbtu  DECIMAL(14, 3),
    avg_heat_rate_btu_kwh DECIMAL(10, 2),
    delivered_fuel_cost_per_mmbtu DECIMAL(8, 2),
    ending_fuel_stock_physical DECIMAL(14, 3)
) USING DELTA
CLUSTER BY (month_start_date_key, plant_key);

-- FACT 3 (Aggregate Grid Fact): Hourly Balancing Authority Telemetry
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_regional_grid_demand (
    date_key             INT NOT NULL,
    hour_of_day          INT NOT NULL,
    ba_key               BIGINT NOT NULL,
    demand_mw            DECIMAL(12, 2),
    demand_forecast_mw   DECIMAL(12, 2),
    net_gen_coal_mw      DECIMAL(12, 2),
    net_gen_gas_mw       DECIMAL(12, 2),
    net_gen_nuclear_mw   DECIMAL(12, 2),
    net_gen_hydro_mw     DECIMAL(12, 2),
    net_gen_wind_mw      DECIMAL(12, 2),
    net_gen_solar_mw     DECIMAL(12, 2),
    net_interchange_mw   DECIMAL(12, 2)
) USING DELTA
CLUSTER BY (date_key, ba_key);
