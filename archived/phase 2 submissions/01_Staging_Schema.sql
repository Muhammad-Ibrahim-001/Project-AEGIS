-- ==============================================================================
-- DL3004 DWBI Final Project: Phase 2 Physical Staging Schema SQL
-- Deliverable: Staging Schema SQL
-- Target Architectures:
--   1. Primary Cloud Target: Databricks Serverless Cloud Lakehouse (dwbi_catalog)
--   2. Syllabus Baseline Target: PostgreSQL (project_staging / quarantine)
-- ==============================================================================

-- ##############################################################################
-- PART 1: DATABRICKS SERVERLESS CLOUD LAKEHOUSE (DELTA LAKE)
-- Catalog: dwbi_catalog | Schemas: bronze_staging, quarantine
-- ##############################################################################

CREATE CATALOG IF NOT EXISTS dwbi_catalog;
USE CATALOG dwbi_catalog;

CREATE SCHEMA IF NOT EXISTS bronze_staging;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- Raw Landing Volume for multi-source file ingestion
CREATE VOLUME IF NOT EXISTS bronze_staging.raw_landing;

-- ------------------------------------------------------------------------------
-- 1. ETL AUDIT RUN LOG (Delta Table)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bronze_staging.etl_run_log (
    run_id               BIGINT GENERATED ALWAYS AS IDENTITY,
    batch_id             STRING NOT NULL,
    pipeline_step        STRING NOT NULL,
    source_system        STRING NOT NULL,
    records_read         INT DEFAULT 0,
    records_inserted     INT DEFAULT 0,
    records_updated      INT DEFAULT 0,
    records_rejected     INT DEFAULT 0,
    execution_status     STRING NOT NULL, -- 'RUNNING', 'COMPLETED', 'FAILED'
    start_time           TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    end_time             TIMESTAMP,
    error_message        STRING
) USING DELTA;

-- ------------------------------------------------------------------------------
-- 2. DEAD-LETTER QUARANTINE TABLE (Delta Table)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quarantine.rejected_records (
    rejection_id         BIGINT GENERATED ALWAYS AS IDENTITY,
    batch_id             STRING NOT NULL,
    source_system        STRING NOT NULL, -- e.g., 'EIA-860', 'EIA-923', 'EPA-CAMPD', 'NOAA-ISD'
    source_table         STRING NOT NULL,
    source_row_identifier STRING,
    rejection_reason     STRING NOT NULL, -- e.g., 'SENTINEL_DETECTED', 'HEAT_RATE_OUT_OF_BOUNDS', 'NULL_NATURAL_KEY'
    raw_payload_json     STRING NOT NULL,
    rejected_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- ------------------------------------------------------------------------------
-- 3. BRONZE LANDING TABLES (Immutable Raw Append-Only Delta Tables)
-- ------------------------------------------------------------------------------

-- Raw EIA-860 Generator Inventory
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia860_generator (
    utility_id               STRING,
    utility_name             STRING,
    plant_code               STRING,
    plant_name               STRING,
    state                    STRING,
    county                   STRING,
    generator_id             STRING,
    prime_mover              STRING,
    nameplate_capacity_mw     STRING,
    status                   STRING,
    operating_year           STRING,
    retirement_year          STRING,
    energy_source_1          STRING,
    balancing_auth_code      STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-860 Boiler-Generator Associations (6_1_EnviroAssoc)
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia860_enviro_assoc (
    utility_id               STRING,
    utility_name             STRING,
    plant_code               STRING,
    plant_name               STRING,
    boiler_id                STRING,
    generator_id             STRING,
    assoc_type               STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-860 Plant Master
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia860_plant (
    utility_id               STRING,
    utility_name             STRING,
    plant_code               STRING,
    plant_name               STRING,
    street_address           STRING,
    city                     STRING,
    state                    STRING,
    zip                      STRING,
    county                   STRING,
    latitude                 STRING,
    longitude                STRING,
    nerc_region              STRING,
    balancing_auth_code      STRING,
    primary_purpose_naics_id STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-923 Monthly Generation & Fuel Consumption
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia923_monthly_generation (
    plant_id                 STRING,
    plant_name               STRING,
    operator_name            STRING,
    operator_id              STRING,
    state                    STRING,
    census_region            STRING,
    nerc_region              STRING,
    naics_code               STRING,
    eia_sector_number        STRING,
    sector_name              STRING,
    reported_prime_mover     STRING,
    reported_fuel_type_code  STRING,
    aer_fuel_type_code       STRING,
    physical_unit_label      STRING,
    quantity_january         STRING,
    quantity_february        STRING,
    quantity_march           STRING,
    quantity_april           STRING,
    quantity_may             STRING,
    quantity_june            STRING,
    quantity_july            STRING,
    quantity_august          STRING,
    quantity_september       STRING,
    quantity_october         STRING,
    quantity_november        STRING,
    quantity_december        STRING,
    netgen_january           STRING,
    netgen_february          STRING,
    netgen_march             STRING,
    netgen_april             STRING,
    netgen_may               STRING,
    netgen_june              STRING,
    netgen_july              STRING,
    netgen_august            STRING,
    netgen_september         STRING,
    netgen_october           STRING,
    netgen_november          STRING,
    netgen_december          STRING,
    year                     STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EPA CAMPD Hourly Smokestack Emissions Telemetry
CREATE TABLE IF NOT EXISTS bronze_staging.raw_epa_hourly_emissions (
    state                    STRING,
    facility_name            STRING,
    orispl_code              STRING,
    unit_id                  STRING,
    op_date                  STRING,
    op_hour                  STRING,
    op_time                  STRING,
    gload                    STRING,
    sload                    STRING,
    so2_mass                 STRING,
    so2_mass_measure_flg     STRING,
    so2_rate                 STRING,
    so2_rate_measure_flg     STRING,
    nox_rate                 STRING,
    nox_rate_measure_flg     STRING,
    nox_mass                 STRING,
    nox_mass_measure_flg     STRING,
    co2_mass                 STRING,
    co2_mass_measure_flg     STRING,
    co2_rate                 STRING,
    co2_rate_measure_flg     STRING,
    heat_input               STRING,
    heat_input_measure_flg   STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EPA-to-EIA Crosswalk Bridge
CREATE TABLE IF NOT EXISTS bronze_staging.raw_epa_eia_crosswalk (
    camd_plant_id            STRING,
    camd_unit_id             STRING,
    eia_plant_id             STRING,
    eia_generator_id         STRING,
    eia_boiler_id            STRING,
    match_type               STRING,
    confidence_score         STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw NOAA ISD Hourly Surface Weather Observations
CREATE TABLE IF NOT EXISTS bronze_staging.raw_noaa_hourly_weather (
    station_id               STRING,
    observation_timestamp    STRING,
    latitude                 STRING,
    longitude                STRING,
    elevation                STRING,
    air_temp_celsius         STRING,
    air_temp_quality_code    STRING,
    dew_point_celsius        STRING,
    dew_point_quality_code   STRING,
    sea_level_pressure_hpa   STRING,
    slp_quality_code         STRING,
    wind_direction_degrees   STRING,
    wind_dir_quality_code    STRING,
    wind_speed_mps           STRING,
    wind_speed_quality_code  STRING,
    sky_condition_code       STRING,
    precipitation_1hr_mm     STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw NOAA Station Master History
CREATE TABLE IF NOT EXISTS bronze_staging.raw_noaa_station_history (
    usaf_id                  STRING,
    wban_id                  STRING,
    station_name             STRING,
    country_code             STRING,
    state_code               STRING,
    call_sign                STRING,
    latitude                 STRING,
    longitude                STRING,
    elevation_m              STRING,
    begin_date               STRING,
    end_date                 STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-930 Hourly Balancing Authority Grid Telemetry
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia930_hourly_demand (
    data_date                STRING,
    hour_ending              STRING,
    ba_code                  STRING,
    ba_name                  STRING,
    demand_mw                STRING,
    demand_forecast_mw       STRING,
    net_generation_mw        STRING,
    total_interchange_mw     STRING,
    gen_coal_mw              STRING,
    gen_natgas_mw            STRING,
    gen_nuclear_mw           STRING,
    gen_hydro_mw             STRING,
    gen_wind_mw              STRING,
    gen_solar_mw             STRING,
    batch_id                 STRING NOT NULL,
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;


-- ##############################################################################
-- PART 2: POSTGRESQL EQUIVALENT STAGING DDL (ACADEMIC BENCHMARK COMPATIBILITY)
-- Schemas: project_staging, quarantine
-- ##############################################################################

CREATE SCHEMA IF NOT EXISTS project_staging;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- PostgreSQL Audit Run Log
CREATE TABLE IF NOT EXISTS project_staging.etl_run_log (
    run_id               BIGSERIAL PRIMARY KEY,
    batch_id             VARCHAR(64) NOT NULL,
    pipeline_step        VARCHAR(64) NOT NULL,
    source_system        VARCHAR(64) NOT NULL,
    records_read         INT DEFAULT 0,
    records_inserted     INT DEFAULT 0,
    records_updated      INT DEFAULT 0,
    records_rejected     INT DEFAULT 0,
    execution_status     VARCHAR(32) NOT NULL,
    start_time           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time             TIMESTAMP WITH TIME ZONE,
    error_message        TEXT
);

-- PostgreSQL Quarantine Dead-Letter Table
CREATE TABLE IF NOT EXISTS quarantine.rejected_records (
    rejection_id         BIGSERIAL PRIMARY KEY,
    batch_id             VARCHAR(64) NOT NULL,
    source_system        VARCHAR(64) NOT NULL,
    source_table         VARCHAR(64) NOT NULL,
    source_row_identifier VARCHAR(128),
    rejection_reason     VARCHAR(128) NOT NULL,
    raw_payload_json     TEXT NOT NULL,
    rejected_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL Staging: Plants
CREATE TABLE IF NOT EXISTS project_staging.stg_eia860_plant (
    utility_id           VARCHAR(32),
    utility_name         VARCHAR(255),
    plant_code           VARCHAR(32),
    plant_name           VARCHAR(255),
    street_address       VARCHAR(255),
    city                 VARCHAR(128),
    state                VARCHAR(16),
    zip                  VARCHAR(16),
    county               VARCHAR(128),
    latitude             VARCHAR(32),
    longitude            VARCHAR(32),
    nerc_region          VARCHAR(32),
    balancing_auth_code  VARCHAR(32),
    batch_id             VARCHAR(64) NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL Staging: Generators
CREATE TABLE IF NOT EXISTS project_staging.stg_eia860_generator (
    utility_id           VARCHAR(32),
    plant_code           VARCHAR(32),
    generator_id         VARCHAR(32),
    prime_mover          VARCHAR(16),
    nameplate_capacity_mw VARCHAR(32),
    status               VARCHAR(16),
    operating_year       VARCHAR(16),
    energy_source_1      VARCHAR(16),
    batch_id             VARCHAR(64) NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL Staging: Hourly Emissions
CREATE TABLE IF NOT EXISTS project_staging.stg_epa_hourly_emissions (
    state                VARCHAR(16),
    facility_name        VARCHAR(255),
    orispl_code          VARCHAR(32),
    unit_id              VARCHAR(32),
    op_date              VARCHAR(32),
    op_hour              VARCHAR(16),
    gload                VARCHAR(32),
    so2_mass             VARCHAR(32),
    nox_mass             VARCHAR(32),
    co2_mass             VARCHAR(32),
    heat_input           VARCHAR(32),
    batch_id             VARCHAR(64) NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
