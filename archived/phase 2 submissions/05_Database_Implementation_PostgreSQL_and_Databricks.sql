-- ==============================================================================
-- DL3004 DWBI Final Project: Phase 2 Database Implementation Master Script
-- Deliverable: PostgreSQL Database SQL Scripts & Databricks Lakehouse SQL
-- Aligned with: DWBI Lab Phase 2 Grading Rubric (Database Implementation: 10 Marks)
-- ==============================================================================

-- ##############################################################################
-- SECTION A: COMPLETE POSTGRESQL IMPLEMENTATION SCRIPT
-- Schemas: project_staging, project_dw, project_reporting
-- ##############################################################################

-- 1. Create PostgreSQL Schemas
CREATE SCHEMA IF NOT EXISTS project_staging;
CREATE SCHEMA IF NOT EXISTS project_dw;
CREATE SCHEMA IF NOT EXISTS project_reporting;

-- 2. Create PostgreSQL Staging Tables
CREATE TABLE IF NOT EXISTS project_staging.stg_eia860_plant (
    utility_id               VARCHAR(32),
    utility_name             VARCHAR(255),
    plant_code               VARCHAR(32),
    plant_name               VARCHAR(255),
    street_address           VARCHAR(255),
    city                     VARCHAR(128),
    state                    VARCHAR(16),
    zip                      VARCHAR(16),
    county                   VARCHAR(128),
    latitude                 VARCHAR(32),
    longitude                VARCHAR(32),
    nerc_region              VARCHAR(32),
    balancing_auth_code      VARCHAR(32),
    batch_id                 VARCHAR(64) NOT NULL,
    ingested_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_staging.stg_eia860_generator (
    utility_id               VARCHAR(32),
    plant_code               VARCHAR(32),
    generator_id             VARCHAR(32),
    prime_mover              VARCHAR(16),
    nameplate_capacity_mw    VARCHAR(32),
    status                   VARCHAR(16),
    operating_year           VARCHAR(16),
    energy_source_1          VARCHAR(16),
    batch_id                 VARCHAR(64) NOT NULL,
    ingested_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_staging.stg_epa_hourly_emissions (
    state                    VARCHAR(16),
    facility_name            VARCHAR(255),
    orispl_code              VARCHAR(32),
    unit_id                  VARCHAR(32),
    op_date                  VARCHAR(32),
    op_hour                  VARCHAR(16),
    gload                    VARCHAR(32),
    so2_mass                 VARCHAR(32),
    nox_mass                 VARCHAR(32),
    co2_mass                 VARCHAR(32),
    heat_input               VARCHAR(32),
    batch_id                 VARCHAR(64) NOT NULL,
    ingested_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create PostgreSQL Star Schema Dimensions
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

CREATE TABLE IF NOT EXISTS project_dw.dim_balancing_authority (
    ba_key                   BIGSERIAL PRIMARY KEY,
    ba_code                  VARCHAR(32) UNIQUE NOT NULL,
    ba_name                  VARCHAR(255) NOT NULL,
    region                   VARCHAR(64),
    is_active                BOOLEAN DEFAULT TRUE
);

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

CREATE TABLE IF NOT EXISTS project_dw.dim_weather_station (
    station_key              BIGSERIAL PRIMARY KEY,
    station_id               VARCHAR(32) UNIQUE NOT NULL,
    station_name             VARCHAR(255),
    state_code               VARCHAR(8),
    latitude                 NUMERIC(9, 6),
    longitude                NUMERIC(9, 6),
    elevation_m              NUMERIC(7, 2)
);

-- 4. Create PostgreSQL Fact Tables with Referential Integrity Constraints
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

-- 5. Seed Default Unknown Member (-1) Records in PostgreSQL
INSERT INTO project_dw.dim_date (date_key, calendar_date, calendar_year, calendar_quarter, calendar_month, month_name, day_of_month, day_of_week, day_name, is_weekend)
VALUES (-1, '1900-01-01', 1900, 1, 1, 'Unknown', 1, 1, 'Unknown', FALSE)
ON CONFLICT (date_key) DO NOTHING;

INSERT INTO project_dw.dim_balancing_authority (ba_key, ba_code, ba_name, region, is_active)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKN', 'Unknown Balancing Authority', 'UNKNOWN', TRUE)
ON CONFLICT (ba_code) DO NOTHING;

INSERT INTO project_dw.dim_plant (plant_key, orispl_code, plant_name, utility_id, utility_name, latitude, longitude, state_code, county_name, ba_code, epa_region)
OVERRIDING SYSTEM VALUE
VALUES (-1, -1, 'Unknown Plant', -1, 'Unknown Utility', 0.0, 0.0, 'XX', 'Unknown County', 'UNKN', -1)
ON CONFLICT (orispl_code) DO NOTHING;

INSERT INTO project_dw.dim_weather_station (station_key, station_id, station_name, state_code, latitude, longitude, elevation_m)
OVERRIDING SYSTEM VALUE
VALUES (-1, '999999-99999', 'Unknown Station', 'XX', 0.0, 0.0, 0.0)
ON CONFLICT (station_id) DO NOTHING;


-- ##############################################################################
-- SECTION B: REPORTING VIEWS (PROJECT_REPORTING SCHEMA)
-- ##############################################################################

CREATE OR REPLACE VIEW project_reporting.vw_emissions_intensity AS
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
    ROUND(SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0), 4) AS co2_intensity_tons_per_mw,
    ROUND(AVG(f.ambient_temp_celsius), 2) AS avg_ambient_temp_celsius
FROM project_dw.fact_hourly_emissions_weather f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
JOIN project_dw.dim_date d ON f.date_key = d.date_key
GROUP BY 
    d.calendar_year, d.calendar_month, d.calendar_date,
    p.orispl_code, p.plant_name, p.state_code, p.ba_code;


-- ##############################################################################
-- SECTION C: REFERENTIAL INTEGRITY VERIFICATION QUERIES
-- Validates zero orphan records across all 3 multi-grain fact tables
-- ##############################################################################

-- Check 1: Fact Hourly Emissions -> Dim Plant
SELECT COUNT(*) AS orphan_plant_keys
FROM project_dw.fact_hourly_emissions_weather f
LEFT JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
WHERE p.plant_key IS NULL; -- MUST RETURN 0

-- Check 2: Fact Hourly Emissions -> Dim Date
SELECT COUNT(*) AS orphan_date_keys
FROM project_dw.fact_hourly_emissions_weather f
LEFT JOIN project_dw.dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL; -- MUST RETURN 0

-- Check 3: Fact Monthly Operations -> Dim Plant
SELECT COUNT(*) AS orphan_monthly_plant_keys
FROM project_dw.fact_monthly_plant_operations f
LEFT JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
WHERE p.plant_key IS NULL; -- MUST RETURN 0

-- Check 4: Fact Grid Demand -> Dim Balancing Authority
SELECT COUNT(*) AS orphan_ba_keys
FROM project_dw.fact_regional_grid_demand f
LEFT JOIN project_dw.dim_balancing_authority b ON f.ba_key = b.ba_key
WHERE b.ba_key IS NULL; -- MUST RETURN 0
