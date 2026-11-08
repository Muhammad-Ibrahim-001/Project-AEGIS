# Databricks notebook source
# COMMAND ----------
"""
==============================================================================
DL3004 DWBI Final Project: Master Lakehouse Configuration & Catalog Setup
Platform: Databricks Serverless Compute / Databricks SQL Warehouse
Storage:  Delta Lake (ACID, Schema Enforcement, Liquid Clustering)
Catalog:  Unity Catalog (`dwbi_catalog`) with Hive Metastore Fallback
Horizon:  4-Year Historical Analysis Window (2021 - 2024)
==============================================================================

This notebook/module is the SINGLE SOURCE OF TRUTH for:
  1. Catalog, Schema & Volume definitions
  2. 4-Year Temporal Horizon parameters (2021 - 2024)
  3. Federal Bulk Ingestion Endpoints (EIA-860, EIA-923, EPA CAMPD, NOAA ISD)
  4. Dimensional Attribute Contracts (Kimball Pruning Matrix)
  5. Defensive Data Quality & Physical Thermodynamic Thresholds

USAGE IN DATABRICKS:
  - Run directly: Automatically initializes schemas, volumes, and audit tables.
  - In other notebooks: Call `%run ./config` or `import config`
"""

import os
from typing import Dict, List, Any, Tuple

# COMMAND ----------
# ==============================================================================
# 1. CATALOG, SCHEMAS & STORAGE CONFIGURATION
# ==============================================================================

CATALOG_CONFIG: Dict[str, Any] = {
    # Primary Unity Catalog 3-tier namespace container
    "CATALOG_NAME": "dwbi_catalog",
    
    # Toggle for Unity Catalog (3-tier) vs Hive Metastore (2-tier fallback)
    "USE_UNITY_CATALOG": True,
    
    # Medallion Lakehouse Architecture Schemas
    "SCHEMAS": {
        "BRONZE": "bronze_staging",        # Raw append-only Delta tables + ETL run logs
        "SILVER": "silver_conformed",      # Cleaned, typed, deduplicated conformed data
        "GOLD_DW": "gold_warehouse",       # Kimball Star Schema (5 Dims + 3 Facts)
        "GOLD_MARTS": "gold_marts",        # Materialized views for Power BI DirectQuery
        "QUARANTINE": "quarantine"         # Dead-letter quarantine table for rejected rows
    },
    
    # Academic course rubric compliance aliases (for university grading scripts)
    "COURSE_SCHEMA_ALIASES": {
        "project_staging": "bronze_staging",
        "project_dw": "gold_warehouse",
        "project_reporting": "gold_marts"
    },
    
    # Unity Catalog Volume landing paths
    "VOLUMES": {
        "RAW_LANDING": "/Volumes/dwbi_catalog/bronze_staging/raw_landing",
        "CHECKPOINTS": "/Volumes/dwbi_catalog/bronze_staging/checkpoints"
    },
    
    # Local workspace fallback paths
    "LOCAL_PATHS": {
        "RAW_DATA": "02_Data/raw_data",
        "CLEANED_DATA": "02_Data/cleaned_data"
    }
}

# COMMAND ----------
# ==============================================================================
# 2. TEMPORAL HORIZON (4-YEAR WINDOW: 2021 - 2024)
# ==============================================================================

TEMPORAL_CONFIG: Dict[str, Any] = {
    "START_YEAR": 2021,
    "END_YEAR": 2024,
    "TARGET_YEARS": [2021, 2022, 2023, 2024],
    "DATE_START": "2021-01-01",
    "DATE_END": "2024-12-31",
    # 2021 (8,760h) + 2022 (8,760h) + 2023 (8,760h) + 2024 leap (8,784h) = 35,064 hours
    "TOTAL_HOURLY_PERIODS": 35064,
    "TOTAL_CALENDAR_DAYS": 1461
}

# COMMAND ----------
# ==============================================================================
# 3. FEDERAL DATA SOURCE DIRECTORY & BULK DOWNLOAD ENDPOINTS
# ==============================================================================

SOURCES_CONFIG: Dict[str, Any] = {
    # EIA-860: Annual Electric Generator Report
    "EIA_860": {
        "NAME": "EIA-860 Annual Electric Generator Report",
        "AGENCY": "U.S. Energy Information Administration",
        "URL_TEMPLATE": "https://www.eia.gov/electricity/data/eia860/archive/xls/eia860{year}.zip",
        "SCHEDULES": {
            "PLANT": "2___Plant_Y{year}.xlsx",
            "GENERATOR": "3_1_Generator_Y{year}.xlsx",
            "ENVIRO_ASSOC": "6_1_EnviroAssoc_Y{year}.xlsx"
        },
        "HEADER_SCAN_KEYS": ["Plant Code", "Plant Id", "utility_id"]
    },
    
    # EIA-923: Monthly Generation and Fuel Report
    "EIA_923": {
        "NAME": "EIA-923 Monthly Generation & Fuel",
        "AGENCY": "U.S. Energy Information Administration",
        "URL_TEMPLATE": "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{year}.zip",
        "PRIMARY_SHEET": "Page 1 Generation and Fuel Data",
        "HEADER_SCAN_KEYS": ["Plant Id", "Plant Code", "Netgen"]
    },
    
    # EIA-930: Real-Time Hourly Grid Balancing Authority Telemetry
    "EIA_930": {
        "NAME": "EIA-930 Hourly Electric Grid Monitor",
        "AGENCY": "U.S. Energy Information Administration",
        "BULK_URL_TEMPLATE": "https://www.eia.gov/electricity/gridmonitor/knownissues/xls/EIA930_BALANCE_{year}_Jan_Jun.csv",
        "GRAIN": "Hourly per Balancing Authority"
    },
    
    # EPA CAMPD: Continuous Emission Monitoring System (CEMS)
    "EPA_CAMPD": {
        "NAME": "EPA CAMPD Hourly Flue-Gas Emissions",
        "AGENCY": "U.S. Environmental Protection Agency",
        "BULK_PORTAL": "https://campd.epa.gov/data/bulk-data-files",
        "API_STREAM_URL": "https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly",
        "GRAIN": "Hourly per Boiler / Smokestack Unit"
    },
    
    # EPA-EIA Crosswalk: Facility & Unit Linking Bridge
    "EPA_EIA_CROSSWALK": {
        "NAME": "EPA-EIA Power Sector Crosswalk Bridge",
        "GITHUB_RAW_URL": "https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv",
        "LINK_KEYS": ["CAMD_PLANT_ID", "EIA_PLANT_ID", "CAMD_UNIT_ID", "EIA_GENERATOR_ID"]
    },
    
    # NOAA ISD: Integrated Surface Database Weather Observations
    "NOAA_ISD": {
        "NAME": "NOAA ISD Synoptic Hourly Surface Weather",
        "AGENCY": "NOAA National Centers for Environmental Information",
        "STATION_HISTORY_URL": "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv",
        "ANNUAL_URL_TEMPLATE": "https://www.ncei.noaa.gov/pub/data/noaa/{year}/"
    }
}

# COMMAND ----------
# ==============================================================================
# 4. DEFENSIVE DATA QUALITY RULES & THERMODYNAMIC THRESHOLDS
# ==============================================================================

DATA_QUALITY_RULES: Dict[str, Any] = {
    # String sentinels converted to SQL NULL
    "SENTINEL_VALUES": [
        ".", "NM", "*", "--", "NA", "N/A", "null", "NULL", "None", "", "   ",
        -9999, "-9999", -9999.0, "-9999.0"
    ],
    
    # Physical Heat Rate Bounds (Btu/kWh)
    # Formula: (Total Fuel MMBtu * 1,000) / Net Generation MWh
    "HEAT_RATE_BOUNDS": {
        "CCGT": {"min": 5000, "max": 14000, "prime_movers": ["CA", "CT", "CS", "CC"]},
        "COAL_ST": {"min": 8500, "max": 18000, "prime_movers": ["ST"]},
        "PEAKER_GT": {"min": 9000, "max": 22000, "prime_movers": ["GT"]},
        "GENERAL_THERMAL": {"min": 4500, "max": 30000}
    },
    
    # Physical Auxiliary Load Reconciliation (EPA Gross MWh vs EIA Net MWh)
    "AUXILIARY_LOAD_RATIO": {
        "GAS_PLANT": {"min_ratio": 0.01, "max_ratio": 0.12},
        "COAL_PLANT": {"min_ratio": 0.04, "max_ratio": 0.16},
        "MAX_UNEXPLAINED_DISCREPANCY": 0.02
    },
    
    # Spatial Join Thresholds
    "MAX_WEATHER_DISTANCE_KM": 100.0,
    "MAX_TEMPORAL_WEATHER_DIFF_MINUTES": 60,
    
    # Business rule: Negative net generation during maintenance outages is VALID
    "ALLOW_NEGATIVE_NET_GENERATION": True,

    # Data Quality Validation Thresholds
    "DEFAULT_MEMBER_RATE_WARN_THRESHOLD": 0.05,  # Warn if > 5% mapped to -1 default member
    "DEFAULT_MEMBER_RATE_FAIL_THRESHOLD": 0.25,  # Fail if > 25% mapped to -1 default member
    "KEY_NULL_TOLERANCE_PCT": 0.0,               # Primary/Foreign keys must have 0% nulls
    "MEASURE_NULL_TOLERANCE_PCT": 5.0            # Non-key measures null tolerance
}

# COMMAND ----------
# ==============================================================================
# 5. DIMENSIONAL ATTRIBUTE CONTRACTS (KIMBALL PRUNING MATRIX)
# ==============================================================================

DIMENSION_ATTRIBUTES: Dict[str, Dict[str, Any]] = {
    # Dim_Plant: Facility Master (1 Row per ORISPL)
    "dim_plant": {
        "surrogate_key": "plant_key",
        "natural_key": "orispl_code",
        "keep_attributes": [
            "orispl_code", "plant_name", "utility_id", "utility_name",
            "latitude", "longitude", "state_code", "county_name",
            "balancing_authority_code", "epa_region", "nerc_region",
            "is_combined_heat_power"
        ],
        "discarded_attributes": [
            "street_address", "zip", "city", "water_source_name", "naics_code",
            "regulatory_status", "sector", "ferc_cogen_docket", "ferc_small_power_docket",
            "ash_impoundment_lined", "ash_impoundment_status", "transmission_owner_id",
            "grid_voltage_1", "grid_voltage_2", "grid_voltage_3", "gas_pipeline_1",
            "gas_pipeline_2", "pipeline_notes", "lng_storage"
        ]
    },

    # Dim_Generator: SCD Type 2 Generator Master
    "dim_generator": {
        "surrogate_key": "generator_key",
        "natural_composite_key": ["orispl_code", "generator_id"],
        "scd2_tracked_attributes": ["operating_status", "nameplate_capacity_mw"],
        "keep_attributes": [
            "orispl_code", "generator_id", "prime_mover_code", "primary_energy_source",
            "nameplate_capacity_mw", "operating_status", "operating_year",
            "planned_retirement_year", "valid_from", "valid_to", "is_current"
        ],
        "discarded_attributes": [
            "rotor_speed_rpm", "synchronous_condenser_flag", "black_start_capability",
            "solid_fuel_gasification", "turbine_manufacturer", "duct_burners_flag",
            "cooling_water_temperature_limits", "bypass_damper_flag"
        ]
    },

    # Dim_Balancing_Authority: Regional Grid Operators
    "dim_balancing_authority": {
        "surrogate_key": "ba_key",
        "natural_key": "ba_code",
        "keep_attributes": ["ba_code", "ba_name", "region", "is_active"]
    },

    # Dim_Weather_Station: NOAA ISD Stations
    "dim_weather_station": {
        "surrogate_key": "station_key",
        "natural_key": "station_id",
        "keep_attributes": ["station_id", "station_name", "state_code", "latitude", "longitude", "elevation_m"]
    },

    # Dim_Date: Universal Calendar & Hour Dimension (2021 - 2024)
    "dim_date": {
        "surrogate_key": "date_key",
        "keep_attributes": [
            "date_key", "calendar_date", "calendar_year", "calendar_quarter",
            "calendar_month", "month_name", "day_of_month", "day_of_week",
            "day_name", "is_weekend", "season_name", "is_summer_peak", "is_winter_freeze"
        ]
    }
}

# COMMAND ----------
# ==============================================================================
# 6. HELPER FUNCTIONS & FULLY QUALIFIED TABLE NAMES
# ==============================================================================

def get_table_fqn(schema_key: str, table_name: str) -> str:
    """
    Returns the fully qualified 3-tier or 2-tier table name.
    Example: get_table_fqn("GOLD_DW", "dim_plant") -> "dwbi_catalog.gold_warehouse.dim_plant"
    """
    schema = CATALOG_CONFIG["SCHEMAS"].get(schema_key.upper(), schema_key.lower())
    if CATALOG_CONFIG["USE_UNITY_CATALOG"]:
        return f"{CATALOG_CONFIG['CATALOG_NAME']}.{schema}.{table_name}"
    return f"{schema}.{table_name}"


def get_volume_path(subpath: str = "") -> str:
    """
    Returns the target Unity Catalog Volume path.
    Example: get_volume_path("eia860") -> "/Volumes/dwbi_catalog/bronze_staging/raw_landing/eia860"
    """
    base = CATALOG_CONFIG["VOLUMES"]["RAW_LANDING"]
    if subpath:
        return f"{base.rstrip('/')}/{subpath.lstrip('/')}"
    return base

# COMMAND ----------
# ==============================================================================
# 7. AUTOMATED DATABRICKS ENVIRONMENT INITIALIZATION
# ==============================================================================

def init_databricks_environment(spark_session=None):
    """
    Executes DDL to automatically provision Catalog, Schemas, Volume,
    and Audit Logging tables in Databricks. Safe to re-run idempotently.
    """
    if spark_session is None:
        try:
            from pyspark.sql import SparkSession
            spark_session = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
        except Exception:
            print("[WARN] SparkSession not found. Skipping live Databricks DDL initialization.")
            return

    print("====================================================================")
    print("INITIALIZING DATABRICKS LAKEHOUSE INFRASTRUCTURE (dwbi_catalog)")
    print("====================================================================")

    # 1. Initialize Unity Catalog
    try:
        spark_session.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG_CONFIG['CATALOG_NAME']}")
        spark_session.sql(f"USE CATALOG {CATALOG_CONFIG['CATALOG_NAME']}")
        print(f"✓ Catalog: '{CATALOG_CONFIG['CATALOG_NAME']}' verified.")
    except Exception as e:
        print(f"! Unity Catalog notice: {e}. Falling back to default catalog.")
        CATALOG_CONFIG["USE_UNITY_CATALOG"] = False

    # 2. Initialize Schemas
    for key, schema_name in CATALOG_CONFIG["SCHEMAS"].items():
        if CATALOG_CONFIG["USE_UNITY_CATALOG"]:
            spark_session.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_CONFIG['CATALOG_NAME']}.{schema_name}")
        else:
            spark_session.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        print(f"✓ Schema: '{schema_name}' verified.")

    # 3. Initialize Raw Landing Volume (if Unity Catalog active)
    if CATALOG_CONFIG["USE_UNITY_CATALOG"]:
        try:
            spark_session.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG_CONFIG['CATALOG_NAME']}.bronze_staging.raw_landing")
            print(f"✓ Volume: '{CATALOG_CONFIG['VOLUMES']['RAW_LANDING']}' ready.")
        except Exception as e:
            print(f"! Volume creation note: {e}")

    # 4. Initialize ETL Run Log in Bronze Staging
    log_table = get_table_fqn("BRONZE", "etl_run_log")
    spark_session.sql(f"""
        CREATE TABLE IF NOT EXISTS {log_table} (
            run_id           BIGINT GENERATED ALWAYS AS IDENTITY,
            batch_id         STRING NOT NULL,
            pipeline_step    STRING NOT NULL,
            source_system    STRING NOT NULL,
            records_read     BIGINT DEFAULT 0,
            records_inserted BIGINT DEFAULT 0,
            records_updated  BIGINT DEFAULT 0,
            records_rejected BIGINT DEFAULT 0,
            execution_status STRING NOT NULL,
            start_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            end_time         TIMESTAMP,
            error_message    STRING
        ) USING DELTA
    """)
    print(f"✓ Audit Table: '{log_table}' ready.")

    # 5. Initialize Dead-Letter Quarantine Table
    quarantine_table = get_table_fqn("QUARANTINE", "rejected_records")
    spark_session.sql(f"""
        CREATE TABLE IF NOT EXISTS {quarantine_table} (
            rejection_id          BIGINT GENERATED ALWAYS AS IDENTITY,
            batch_id              STRING NOT NULL,
            source_system         STRING NOT NULL,
            source_table          STRING NOT NULL,
            source_row_identifier STRING,
            rejection_reason      STRING NOT NULL,
            raw_payload_json      STRING NOT NULL,
            rejected_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        ) USING DELTA
    """)
    print(f"✓ Quarantine Table: '{quarantine_table}' ready.")

    # 6. Initialize Data Quality Results Audit Table
    dq_results_table = get_table_fqn("QUARANTINE", "dq_check_results")
    spark_session.sql(f"""
        CREATE TABLE IF NOT EXISTS {dq_results_table} (
            check_id         STRING NOT NULL,
            check_category   STRING NOT NULL,
            check_name       STRING NOT NULL,
            table_name       STRING NOT NULL,
            column_name      STRING,
            metric_value     DOUBLE,
            threshold        STRING,
            status           STRING NOT NULL,
            run_batch_id     STRING NOT NULL,
            checked_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        ) USING DELTA
    """)
    print(f"✓ DQ Results Table: '{dq_results_table}' ready.")

    # 7. Initialize Cleaning Step Log Table in Silver Conformed
    cleaning_log_table = get_table_fqn("SILVER", "cleaning_step_log")
    spark_session.sql(f"""
        CREATE TABLE IF NOT EXISTS {cleaning_log_table} (
            log_id           BIGINT GENERATED ALWAYS AS IDENTITY,
            step_name        STRING NOT NULL,
            table_name       STRING NOT NULL,
            rows_in          BIGINT NOT NULL,
            rows_changed     BIGINT NOT NULL,
            rows_removed     BIGINT NOT NULL,
            rows_quarantined BIGINT NOT NULL,
            logged_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        ) USING DELTA
    """)
    print(f"✓ Cleaning Log Table: '{cleaning_log_table}' ready.")

    print("====================================================================")
    print("DATABRICKS ENVIRONMENT READY FOR 2021 - 2024 LAKEHOUSE PIPELINE")
    print("====================================================================")


# If executed directly inside a Databricks Notebook cell, run the setup
try:
    if "spark" in locals() or "spark" in globals():
        init_databricks_environment(spark)
except NameError:
    pass
