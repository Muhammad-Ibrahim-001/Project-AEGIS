-- ==============================================================================
-- DL3004 DWBI Final Project: Phase 2 Physical DW Schema SQL
-- Deliverable: DW Schema SQL
-- Target Architectures:
--   1. Primary Cloud Target: Databricks Serverless Cloud Lakehouse (dwbi_catalog.gold_warehouse)
--   2. Syllabus Baseline Target: PostgreSQL (project_dw)
-- Storage: Delta Lake (ACID, Liquid Clustering) / ANSI Relational Tables
-- ==============================================================================

-- ##############################################################################
-- PART 1: DATABRICKS SERVERLESS CLOUD LAKEHOUSE (DELTA LAKE)
-- Catalog: dwbi_catalog | Schema: gold_warehouse
-- ##############################################################################

CREATE CATALOG IF NOT EXISTS dwbi_catalog;
USE CATALOG dwbi_catalog;

CREATE SCHEMA IF NOT EXISTS gold_warehouse;

-- ------------------------------------------------------------------------------
-- 1. CONFORMED DIMENSIONS (SURROGATE KEYS & IDENTITY SPECIFICATION)
-- ------------------------------------------------------------------------------

-- Dim_Date (Universal Calendar & Peak Period Dimension: 2021-2024, 1,461 Days)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_date (
    date_key                 INT NOT NULL,          -- Format: YYYYMMDD
    calendar_date            DATE NOT NULL,
    calendar_year            INT NOT NULL,
    calendar_quarter         INT NOT NULL,
    calendar_month           INT NOT NULL,
    month_name               STRING NOT NULL,
    day_of_month             INT NOT NULL,
    day_of_week              INT NOT NULL,
    day_name                 STRING NOT NULL,
    is_weekend               BOOLEAN NOT NULL,
    season_name              STRING,
    is_summer_peak           BOOLEAN,
    is_winter_freeze         BOOLEAN,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
) USING DELTA;

-- Dim_Balancing_Authority (Regional Reliability & Grid Balancing Authorities)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_balancing_authority (
    ba_key                   BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    ba_code                  STRING NOT NULL,                     -- Natural Business Key
    ba_name                  STRING NOT NULL,
    region                   STRING,
    is_active                BOOLEAN DEFAULT TRUE,
    CONSTRAINT pk_dim_ba PRIMARY KEY (ba_key)
) USING DELTA;

-- Dim_Plant (Power Generation Facility Master)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_plant (
    plant_key                BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    orispl_code              INT NOT NULL,                        -- Natural Business Key (EIA / EPA ORISPL)
    plant_name               STRING NOT NULL,
    utility_id               INT,
    utility_name             STRING,
    latitude                 DECIMAL(9, 6),
    longitude                DECIMAL(9, 6),
    state_code               STRING NOT NULL,
    county_name              STRING,
    ba_code                  STRING,
    epa_region               INT,
    is_combined_heat_power   BOOLEAN DEFAULT FALSE,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_dim_plant PRIMARY KEY (plant_key)
) USING DELTA;

-- Dim_Generator (SCD Type 2: Unit Operating Status & Capacity Evolution)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_generator (
    generator_key            BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    orispl_code              INT NOT NULL,                        -- Natural Business Key
    generator_id             STRING NOT NULL,                     -- Natural Business Key
    prime_mover_code         STRING NOT NULL,
    primary_energy_source    STRING NOT NULL,
    nameplate_capacity_mw    DECIMAL(10, 2),
    operating_status         STRING NOT NULL, -- OP (Operating), SB (Standby), RE (Retired)
    valid_from               TIMESTAMP NOT NULL,
    valid_to                 TIMESTAMP DEFAULT TIMESTAMP('9999-12-31 23:59:59'),
    is_current               BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_generator PRIMARY KEY (generator_key)
) USING DELTA;

-- Dim_Weather_Station (NOAA Integrated Surface Database Observation Stations)
CREATE TABLE IF NOT EXISTS gold_warehouse.dim_weather_station (
    station_key              BIGINT GENERATED ALWAYS AS IDENTITY, -- Surrogate Key
    station_id               STRING NOT NULL,                     -- Natural Business Key (USAF-WBAN)
    station_name             STRING,
    state_code               STRING,
    latitude                 DECIMAL(9, 6),
    longitude                DECIMAL(9, 6),
    elevation_m              DECIMAL(7, 2),
    CONSTRAINT pk_dim_station PRIMARY KEY (station_key)
) USING DELTA;

-- ------------------------------------------------------------------------------
-- 2. MULTI-GRAIN FACT TABLES (THREE KIMBALL ARCHETYPES WITH LIQUID CLUSTERING)
-- ------------------------------------------------------------------------------

-- FACT 1 (Transactional Fact): Hourly Smokestack Emissions & Weather Observations
-- Grain: One record per power generation smokestack unit per clock hour
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_hourly_emissions_weather (
    date_key                 INT NOT NULL,
    hour_of_day              INT NOT NULL,
    plant_key                BIGINT NOT NULL,
    unit_id                  STRING NOT NULL,
    station_key              BIGINT,
    gross_load_mw            DECIMAL(10, 2),
    heat_input_mmbtu         DECIMAL(12, 3),
    so2_mass_lbs             DECIMAL(12, 3),
    nox_mass_lbs             DECIMAL(12, 3),
    co2_mass_tons            DECIMAL(12, 3),
    ambient_temp_celsius     DECIMAL(5, 2),
    wind_speed_mps           DECIMAL(5, 2),
    weather_distance_km      DECIMAL(6, 2)
) USING DELTA
CLUSTER BY (date_key, plant_key);

-- FACT 2 (Periodic Snapshot Fact): Monthly Plant Fuel Consumption & Net Generation
-- Grain: One record per power plant per prime mover per fuel type per calendar month
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_monthly_plant_operations (
    snapshot_key             BIGINT GENERATED ALWAYS AS IDENTITY,
    month_start_date_key     INT NOT NULL,
    plant_key                BIGINT NOT NULL,
    prime_mover_code         STRING NOT NULL,
    energy_source_code       STRING NOT NULL,
    net_generation_mwh       DECIMAL(14, 3) NOT NULL, -- Negative values allowed during station maintenance outages
    fuel_consumed_physical   DECIMAL(14, 3),
    fuel_consumed_mmbtu      DECIMAL(14, 3),
    avg_heat_rate_btu_kwh    DECIMAL(10, 2),
    delivered_fuel_cost_per_mmbtu DECIMAL(8, 2),
    ending_fuel_stock_physical DECIMAL(14, 3)
) USING DELTA
CLUSTER BY (month_start_date_key, plant_key);

-- FACT 3 (Aggregate Grid Fact): Hourly Balancing Authority Telemetry
-- Grain: One record per regional balancing authority per clock hour
CREATE TABLE IF NOT EXISTS gold_warehouse.fact_regional_grid_demand (
    date_key                 INT NOT NULL,
    hour_of_day              INT NOT NULL,
    ba_key                   BIGINT NOT NULL,
    demand_mw                DECIMAL(12, 2),
    demand_forecast_mw       DECIMAL(12, 2),
    net_gen_coal_mw          DECIMAL(12, 2),
    net_gen_gas_mw           DECIMAL(12, 2),
    net_gen_nuclear_mw       DECIMAL(12, 2),
    net_gen_hydro_mw         DECIMAL(12, 2),
    net_gen_wind_mw          DECIMAL(12, 2),
    net_gen_solar_mw         DECIMAL(12, 2),
    net_interchange_mw       DECIMAL(12, 2)
) USING DELTA
CLUSTER BY (date_key, ba_key);


-- ##############################################################################
-- PART 2: POSTGRESQL EQUIVALENT STAR SCHEMA DDL WITH FORMAL FOREIGN KEYS
-- Schema: project_dw
-- ##############################################################################

CREATE SCHEMA IF NOT EXISTS project_dw;

-- PostgreSQL Dim_Date
CREATE TABLE IF NOT EXISTS project_dw.dim_date (
    date_key                 INT PRIMARY KEY,
    calendar_date            DATE NOT NULL,
    calendar_year            INT NOT NULL,
    calendar_quarter         INT NOT NULL,
    calendar_month           INT NOT NULL,
    month_name               VARCHAR(16) NOT NULL,
    day_of_month             INT NOT NULL,
    day_of_week              INT NOT NULL,
    day_name                 VARCHAR(16) NOT NULL,
    is_weekend               BOOLEAN NOT NULL,
    season_name              VARCHAR(16),
    is_summer_peak           BOOLEAN,
    is_winter_freeze         BOOLEAN
);

-- PostgreSQL Dim_Balancing_Authority
CREATE TABLE IF NOT EXISTS project_dw.dim_balancing_authority (
    ba_key                   BIGSERIAL PRIMARY KEY,
    ba_code                  VARCHAR(32) UNIQUE NOT NULL,
    ba_name                  VARCHAR(255) NOT NULL,
    region                   VARCHAR(64),
    is_active                BOOLEAN DEFAULT TRUE
);

-- PostgreSQL Dim_Plant
CREATE TABLE IF NOT EXISTS project_dw.dim_plant (
    plant_key                BIGSERIAL PRIMARY KEY,
    orispl_code              INT UNIQUE NOT NULL,
    plant_name               VARCHAR(255) NOT NULL,
    utility_id               INT,
    utility_name             VARCHAR(255),
    latitude                 NUMERIC(9, 6),
    longitude                NUMERIC(9, 6),
    state_code               VARCHAR(8) NOT NULL,
    county_name              VARCHAR(128),
    ba_code                  VARCHAR(32),
    epa_region               INT,
    is_combined_heat_power   BOOLEAN DEFAULT FALSE,
    created_at               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL Dim_Generator (SCD Type 2)
CREATE TABLE IF NOT EXISTS project_dw.dim_generator (
    generator_key            BIGSERIAL PRIMARY KEY,
    orispl_code              INT NOT NULL,
    generator_id             VARCHAR(32) NOT NULL,
    prime_mover_code         VARCHAR(16) NOT NULL,
    primary_energy_source    VARCHAR(16) NOT NULL,
    nameplate_capacity_mw    NUMERIC(10, 2),
    operating_status         VARCHAR(16) NOT NULL,
    valid_from               TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_to                 TIMESTAMP WITH TIME ZONE DEFAULT '9999-12-31 23:59:59+00',
    is_current               BOOLEAN NOT NULL DEFAULT TRUE
);

-- PostgreSQL Dim_Weather_Station
CREATE TABLE IF NOT EXISTS project_dw.dim_weather_station (
    station_key              BIGSERIAL PRIMARY KEY,
    station_id               VARCHAR(32) UNIQUE NOT NULL,
    station_name             VARCHAR(255),
    state_code               VARCHAR(8),
    latitude                 NUMERIC(9, 6),
    longitude                NUMERIC(9, 6),
    elevation_m              NUMERIC(7, 2)
);

-- PostgreSQL Fact 1: fact_hourly_emissions_weather
CREATE TABLE IF NOT EXISTS project_dw.fact_hourly_emissions_weather (
    date_key                 INT NOT NULL REFERENCES project_dw.dim_date(date_key),
    hour_of_day              INT NOT NULL,
    plant_key                BIGINT NOT NULL REFERENCES project_dw.dim_plant(plant_key),
    unit_id                  VARCHAR(32) NOT NULL,
    station_key              BIGINT REFERENCES project_dw.dim_weather_station(station_key),
    gross_load_mw            NUMERIC(10, 2),
    heat_input_mmbtu         NUMERIC(12, 3),
    so2_mass_lbs             NUMERIC(12, 3),
    nox_mass_lbs             NUMERIC(12, 3),
    co2_mass_tons            NUMERIC(12, 3),
    ambient_temp_celsius     NUMERIC(5, 2),
    wind_speed_mps           NUMERIC(5, 2),
    weather_distance_km      NUMERIC(6, 2),
    CONSTRAINT pk_fact_hourly PRIMARY KEY (date_key, hour_of_day, plant_key, unit_id)
);

-- PostgreSQL Fact 2: fact_monthly_plant_operations
CREATE TABLE IF NOT EXISTS project_dw.fact_monthly_plant_operations (
    snapshot_key             BIGSERIAL PRIMARY KEY,
    month_start_date_key     INT NOT NULL REFERENCES project_dw.dim_date(date_key),
    plant_key                BIGINT NOT NULL REFERENCES project_dw.dim_plant(plant_key),
    prime_mover_code         VARCHAR(16) NOT NULL,
    energy_source_code       VARCHAR(16) NOT NULL,
    net_generation_mwh       NUMERIC(14, 3) NOT NULL,
    fuel_consumed_physical   NUMERIC(14, 3),
    fuel_consumed_mmbtu      NUMERIC(14, 3),
    avg_heat_rate_btu_kwh    NUMERIC(10, 2),
    delivered_fuel_cost_per_mmbtu NUMERIC(8, 2),
    ending_fuel_stock_physical NUMERIC(14, 3)
);

-- PostgreSQL Fact 3: fact_regional_grid_demand
CREATE TABLE IF NOT EXISTS project_dw.fact_regional_grid_demand (
    date_key                 INT NOT NULL REFERENCES project_dw.dim_date(date_key),
    hour_of_day              INT NOT NULL,
    ba_key                   BIGINT NOT NULL REFERENCES project_dw.dim_balancing_authority(ba_key),
    demand_mw                NUMERIC(12, 2),
    demand_forecast_mw       NUMERIC(12, 2),
    net_gen_coal_mw          NUMERIC(12, 2),
    net_gen_gas_mw           NUMERIC(12, 2),
    net_gen_nuclear_mw       NUMERIC(12, 2),
    net_gen_hydro_mw         NUMERIC(12, 2),
    net_gen_wind_mw          NUMERIC(12, 2),
    net_gen_solar_mw         NUMERIC(12, 2),
    net_interchange_mw       NUMERIC(12, 2),
    CONSTRAINT pk_fact_grid PRIMARY KEY (date_key, hour_of_day, ba_key)
);
