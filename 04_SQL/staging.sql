-- ==============================================================================
-- DL3004 DWBI Final Project: Databricks Bronze Staging & Quarantine Tables
-- Platform: Databricks Serverless Compute / Databricks SQL Warehouse
-- Catalog: dwbi_catalog
-- Schemas: bronze_staging, quarantine
-- Storage: Delta Lake (ACID, Schema Enforcement)
-- ==============================================================================

CREATE CATALOG IF NOT EXISTS dwbi_catalog;
USE CATALOG dwbi_catalog;

CREATE SCHEMA IF NOT EXISTS bronze_staging;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- Create Raw Landing Volume for multi-source file ingestion
CREATE VOLUME IF NOT EXISTS bronze_staging.raw_landing;

-- ------------------------------------------------------------------------------
-- 1. ETL AUDIT RUN LOG (DELTA)
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
-- 2. DEAD-LETTER QUARANTINE TABLE (DELTA)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quarantine.rejected_records (
    rejection_id         BIGINT GENERATED ALWAYS AS IDENTITY,
    batch_id             STRING NOT NULL,
    source_system        STRING NOT NULL, -- e.g., 'EIA-923', 'EPA-CAMPD', 'NOAA-ISD'
    source_table         STRING NOT NULL,
    source_row_identifier STRING,
    rejection_reason     STRING NOT NULL, -- e.g., 'SENTINEL_DETECTED', 'HEAT_RATE_OUT_OF_BOUNDS'
    raw_payload_json     STRING NOT NULL,
    rejected_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- ------------------------------------------------------------------------------
-- 3. BRONZE LANDING TABLES (IMMUTABLE RAW APPEND-ONLY DELTA TABLES)
-- ------------------------------------------------------------------------------

-- Raw EIA-860 Generator Inventory
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia860_generator (
    utility_id           STRING,
    utility_name         STRING,
    plant_code           STRING,
    plant_name           STRING,
    state                STRING,
    county               STRING,
    generator_id         STRING,
    prime_mover          STRING,
    nameplate_capacity_mw STRING,
    status               STRING,
    operating_year       STRING,
    retirement_year      STRING,
    energy_source_1      STRING,
    balancing_auth_code  STRING,
    batch_id             STRING NOT NULL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-860 Boiler-Generator Associations (6_1_EnviroAssoc)
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia860_enviro_assoc (
    utility_id           STRING,
    utility_name         STRING,
    plant_code           STRING,
    plant_name           STRING,
    boiler_id            STRING,
    generator_id         STRING,
    batch_id             STRING NOT NULL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EIA-923 Monthly Generation & Fuel
CREATE TABLE IF NOT EXISTS bronze_staging.raw_eia923_monthly_generation (
    plant_id             STRING,
    plant_name           STRING,
    operator_name        STRING,
    plant_state          STRING,
    census_region        STRING,
    reported_prime_mover STRING,
    reported_fuel_type   STRING,
    physical_unit_label  STRING,
    quantity_january     STRING,
    quantity_february    STRING,
    netgen_january       STRING,
    netgen_february      STRING,
    batch_id             STRING NOT NULL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw EPA CAMPD Hourly Emissions (CEMS)
CREATE TABLE IF NOT EXISTS bronze_staging.raw_epa_hourly_emissions (
    state                STRING,
    facility_name        STRING,
    oris_code            STRING,
    unit_id              STRING,
    date_observed        STRING,
    hour_observed        STRING,
    op_time              STRING,
    gross_load_mw        STRING,
    so2_mass_lbs         STRING,
    nox_mass_lbs         STRING,
    co2_mass_tons        STRING,
    heat_input_mmbtu     STRING,
    batch_id             STRING NOT NULL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- Raw NOAA ISD Hourly Weather
CREATE TABLE IF NOT EXISTS bronze_staging.raw_noaa_isd_weather (
    station_id           STRING,
    timestamp_utc        STRING,
    air_temperature_c    STRING,
    dew_point_c          STRING,
    sea_level_pressure_hpa STRING,
    wind_speed_mps       STRING,
    precipitation_mm     STRING,
    quality_flags        STRING,
    batch_id             STRING NOT NULL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;
