-- ==============================================================================
-- DL3004 DWBI Final Project: Data Warehouse Schema DDL
-- Target Engine: PostgreSQL 14+
-- Schemas: project_staging, project_dw, project_reporting
-- Aligned with: DWBI Lab Phase 2 & Phase 3 Guidelines
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS project_staging;
CREATE SCHEMA IF NOT EXISTS project_dw;
CREATE SCHEMA IF NOT EXISTS project_reporting;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- ------------------------------------------------------------------------------
-- 1. CONFORMED DIMENSIONS (WITH SURROGATE KEYS)
-- ------------------------------------------------------------------------------

-- Dim_Date
DROP TABLE IF EXISTS project_dw.dim_date CASCADE;
CREATE TABLE project_dw.dim_date (
    date_key             INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    calendar_date        DATE NOT NULL UNIQUE,
    calendar_year        SMALLINT NOT NULL,
    calendar_quarter     SMALLINT NOT NULL,
    calendar_month       SMALLINT NOT NULL,
    month_name           VARCHAR(15) NOT NULL,
    day_of_month         SMALLINT NOT NULL,
    day_of_week          SMALLINT NOT NULL,
    day_name             VARCHAR(15) NOT NULL,
    is_weekend           BOOLEAN NOT NULL
);

-- Dim_Balancing_Authority (Regional Grid Operators)
DROP TABLE IF EXISTS project_dw.dim_balancing_authority CASCADE;
CREATE TABLE project_dw.dim_balancing_authority (
    ba_key               SERIAL PRIMARY KEY,      -- Surrogate Key
    ba_code              VARCHAR(20) NOT NULL UNIQUE, -- Natural Business Key
    ba_name              VARCHAR(150) NOT NULL,
    region               VARCHAR(50),
    is_active            BOOLEAN DEFAULT TRUE
);

-- Dim_Plant (Power Plant Facilities)
DROP TABLE IF EXISTS project_dw.dim_plant CASCADE;
CREATE TABLE project_dw.dim_plant (
    plant_key            SERIAL PRIMARY KEY,      -- Surrogate Key
    orispl_code          INTEGER NOT NULL UNIQUE, -- Natural Business Key
    plant_name           VARCHAR(150) NOT NULL,
    utility_id           INTEGER,
    utility_name         VARCHAR(150),
    latitude             NUMERIC(9, 6),
    longitude            NUMERIC(9, 6),
    state_code           CHAR(2) NOT NULL,
    county_name          VARCHAR(100),
    ba_code              VARCHAR(20),
    epa_region           SMALLINT,
    is_combined_heat_power BOOLEAN DEFAULT FALSE,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dim_Generator (SCD Type 2: Unit Operating Status & Capacity Evolution)
DROP TABLE IF EXISTS project_dw.dim_generator CASCADE;
CREATE TABLE project_dw.dim_generator (
    generator_key        SERIAL PRIMARY KEY,      -- Surrogate Key
    orispl_code          INTEGER NOT NULL,        -- Natural Business Key
    generator_id         VARCHAR(20) NOT NULL,    -- Natural Business Key
    prime_mover_code     VARCHAR(10) NOT NULL,
    primary_energy_source VARCHAR(10) NOT NULL,
    nameplate_capacity_mw NUMERIC(10, 2),
    operating_status     VARCHAR(30) NOT NULL,    -- OP (Operating), SB (Standby), RE (Retired)
    row_effective_date   DATE NOT NULL,
    row_expiration_date  DATE NOT NULL DEFAULT '9999-12-31',
    is_current           BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (orispl_code) REFERENCES project_dw.dim_plant(orispl_code)
);
CREATE INDEX idx_dim_gen_lookup ON project_dw.dim_generator(orispl_code, generator_id, is_current);

-- Dim_Weather_Station
DROP TABLE IF EXISTS project_dw.dim_weather_station CASCADE;
CREATE TABLE project_dw.dim_weather_station (
    station_key          SERIAL PRIMARY KEY,      -- Surrogate Key
    station_id           VARCHAR(25) NOT NULL UNIQUE, -- Natural Business Key
    station_name         VARCHAR(150),
    state_code           CHAR(2),
    latitude             NUMERIC(9, 6),
    longitude            NUMERIC(9, 6),
    elevation_m          NUMERIC(7, 2)
);

-- ------------------------------------------------------------------------------
-- 2. FACT TABLES (KIMBALL THREE ARCHETYPES - >10,000 ROWS)
-- ------------------------------------------------------------------------------

-- FACT 1 (Transactional Fact): Hourly Smokestack Emissions & Weather Observations
DROP TABLE IF EXISTS project_dw.fact_hourly_emissions_weather CASCADE;
CREATE TABLE project_dw.fact_hourly_emissions_weather (
    date_key             INTEGER NOT NULL,
    hour_of_day          SMALLINT NOT NULL,
    plant_key            INTEGER NOT NULL,
    unit_id              VARCHAR(20) NOT NULL,
    station_key          INTEGER,
    gross_load_mw        NUMERIC(10, 2),
    heat_input_mmbtu     NUMERIC(12, 3),
    so2_mass_lbs         NUMERIC(12, 3),
    nox_mass_lbs         NUMERIC(12, 3),
    co2_mass_tons        NUMERIC(12, 3),
    ambient_temp_celsius NUMERIC(5, 2),
    wind_speed_mps       NUMERIC(5, 2),
    weather_distance_km  NUMERIC(6, 2),
    PRIMARY KEY (date_key, hour_of_day, plant_key, unit_id),
    FOREIGN KEY (date_key) REFERENCES project_dw.dim_date(date_key),
    FOREIGN KEY (plant_key) REFERENCES project_dw.dim_plant(plant_key)
) PARTITION BY RANGE (date_key);

-- FACT 2 (Periodic Snapshot Fact): Monthly Plant Fuel Consumption & Net Generation
DROP TABLE IF EXISTS project_dw.fact_monthly_plant_operations CASCADE;
CREATE TABLE project_dw.fact_monthly_plant_operations (
    snapshot_key         SERIAL PRIMARY KEY,
    month_start_date_key INTEGER NOT NULL,
    plant_key            INTEGER NOT NULL,
    prime_mover_code     VARCHAR(10) NOT NULL,
    energy_source_code   VARCHAR(10) NOT NULL,
    net_generation_mwh   NUMERIC(14, 3) NOT NULL, -- May be negative during plant outages
    fuel_consumed_physical NUMERIC(14, 3),
    fuel_consumed_mmbtu  NUMERIC(14, 3),
    avg_heat_rate_btu_kwh NUMERIC(10, 2),
    delivered_fuel_cost_per_mmbtu NUMERIC(8, 2),
    ending_fuel_stock_physical NUMERIC(14, 3),
    FOREIGN KEY (month_start_date_key) REFERENCES project_dw.dim_date(date_key),
    FOREIGN KEY (plant_key) REFERENCES project_dw.dim_plant(plant_key)
);

-- FACT 3 (Aggregate Grid Fact): Hourly Balancing Authority Telemetry
DROP TABLE IF EXISTS project_dw.fact_regional_grid_demand CASCADE;
CREATE TABLE project_dw.fact_regional_grid_demand (
    date_key             INTEGER NOT NULL,
    hour_of_day          SMALLINT NOT NULL,
    ba_key               INTEGER NOT NULL,
    demand_mw            NUMERIC(12, 2),
    demand_forecast_mw   NUMERIC(12, 2),
    net_gen_coal_mw      NUMERIC(12, 2),
    net_gen_gas_mw       NUMERIC(12, 2),
    net_gen_nuclear_mw   NUMERIC(12, 2),
    net_gen_hydro_mw     NUMERIC(12, 2),
    net_gen_wind_mw      NUMERIC(12, 2),
    net_gen_solar_mw     NUMERIC(12, 2),
    net_interchange_mw   NUMERIC(12, 2),
    PRIMARY KEY (date_key, hour_of_day, ba_key),
    FOREIGN KEY (date_key) REFERENCES project_dw.dim_date(date_key),
    FOREIGN KEY (ba_key) REFERENCES project_dw.dim_balancing_authority(ba_key)
);
