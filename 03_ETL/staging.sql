-- ==============================================================================
-- DL3004 DWBI Final Project: Staging & Quarantine Tables
-- Target Engine: PostgreSQL 14+
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS project_staging;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- ------------------------------------------------------------------------------
-- 1. ETL AUDIT RUN LOG
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS project_staging.etl_run_log CASCADE;
CREATE TABLE project_staging.etl_run_log (
    run_id               BIGSERIAL PRIMARY KEY,
    batch_id             UUID NOT NULL,
    pipeline_step        VARCHAR(100) NOT NULL,
    source_system        VARCHAR(50) NOT NULL,
    records_read         INTEGER DEFAULT 0,
    records_inserted     INTEGER DEFAULT 0,
    records_updated      INTEGER DEFAULT 0,
    records_rejected     INTEGER DEFAULT 0,
    execution_status     VARCHAR(30) NOT NULL, -- 'RUNNING', 'COMPLETED', 'FAILED'
    start_time           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time             TIMESTAMP WITH TIME ZONE,
    error_message        TEXT
);

-- ------------------------------------------------------------------------------
-- 2. DEAD-LETTER QUARANTINE TABLE
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS quarantine.rejected_records CASCADE;
CREATE TABLE quarantine.rejected_records (
    rejection_id         BIGSERIAL PRIMARY KEY,
    batch_id             UUID NOT NULL,
    source_system        VARCHAR(50) NOT NULL, -- e.g., 'EIA-923', 'EPA-CAMPD', 'NOAA-ISD'
    source_table         VARCHAR(100) NOT NULL,
    source_row_identifier VARCHAR(100),
    rejection_reason     VARCHAR(255) NOT NULL, -- e.g., 'SENTINEL_DETECTED', 'HEAT_RATE_OUT_OF_BOUNDS'
    raw_payload_json     JSONB NOT NULL,
    rejected_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 3. BRONZE LANDING TABLES (UNVALIDATED RAW DATA)
-- ------------------------------------------------------------------------------

-- Raw EIA-860 Generator Inventory
DROP TABLE IF EXISTS project_staging.raw_eia860_generator CASCADE;
CREATE TABLE project_staging.raw_eia860_generator (
    utility_id           VARCHAR(50),
    utility_name         VARCHAR(255),
    plant_code           VARCHAR(50),
    plant_name           VARCHAR(255),
    state                VARCHAR(10),
    county               VARCHAR(100),
    generator_id         VARCHAR(50),
    prime_mover          VARCHAR(20),
    nameplate_capacity_mw VARCHAR(50),
    status               VARCHAR(20),
    operating_year       VARCHAR(20),
    retirement_year      VARCHAR(20),
    energy_source_1      VARCHAR(20),
    balancing_auth_code  VARCHAR(50),
    batch_id             UUID NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw EIA-860 Boiler-Generator Associations (6_1_EnviroAssoc)
DROP TABLE IF EXISTS project_staging.raw_eia860_enviro_assoc CASCADE;
CREATE TABLE project_staging.raw_eia860_enviro_assoc (
    utility_id           VARCHAR(50),
    utility_name         VARCHAR(255),
    plant_code           VARCHAR(50),
    plant_name           VARCHAR(255),
    boiler_id            VARCHAR(50),
    generator_id         VARCHAR(50),
    batch_id             UUID NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw EIA-923 Monthly Generation & Fuel
DROP TABLE IF EXISTS project_staging.raw_eia923_monthly_generation CASCADE;
CREATE TABLE project_staging.raw_eia923_monthly_generation (
    plant_id             VARCHAR(50),
    plant_name           VARCHAR(255),
    operator_name        VARCHAR(255),
    plant_state          VARCHAR(10),
    census_region        VARCHAR(50),
    reported_prime_mover VARCHAR(20),
    reported_fuel_type   VARCHAR(20),
    physical_unit_label  VARCHAR(50),
    quantity_january     VARCHAR(50),
    quantity_february    VARCHAR(50),
    netgen_january       VARCHAR(50),
    netgen_february      VARCHAR(50),
    batch_id             UUID NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw EPA CAMPD Hourly Emissions (CEMS)
DROP TABLE IF EXISTS project_staging.raw_epa_hourly_emissions CASCADE;
CREATE TABLE project_staging.raw_epa_hourly_emissions (
    state                VARCHAR(10),
    facility_name        VARCHAR(255),
    oris_code            VARCHAR(50),
    unit_id              VARCHAR(50),
    date_observed        VARCHAR(30),
    hour_observed        VARCHAR(10),
    op_time              VARCHAR(20),
    gross_load_mw        VARCHAR(50),
    so2_mass_lbs         VARCHAR(50),
    nox_mass_lbs         VARCHAR(50),
    co2_mass_tons        VARCHAR(50),
    heat_input_mmbtu     VARCHAR(50),
    batch_id             UUID NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw NOAA ISD Hourly Weather
DROP TABLE IF EXISTS project_staging.raw_noaa_isd_weather CASCADE;
CREATE TABLE project_staging.raw_noaa_isd_weather (
    station_id           VARCHAR(50),
    timestamp_utc        VARCHAR(50),
    air_temperature_c    VARCHAR(20),
    dew_point_c          VARCHAR(20),
    sea_level_pressure_hpa VARCHAR(20),
    wind_speed_mps       VARCHAR(20),
    precipitation_mm     VARCHAR(20),
    quality_flags        VARCHAR(50),
    batch_id             UUID NOT NULL,
    ingested_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

