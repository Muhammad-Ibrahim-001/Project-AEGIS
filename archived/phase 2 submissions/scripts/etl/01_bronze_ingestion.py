# Databricks notebook source
# COMMAND ----------
"""
==============================================================================
DL3004 DWBI Final Project: Bronze Staging Lakehouse Ingestion Engine
Work Package: WP1 (Ingestion & Bronze Lakehouse Lead)
Platform:     Databricks Serverless Compute / Apache Spark / Delta Lake
Catalog:      Unity Catalog (`dwbi_catalog.bronze_staging`)
==============================================================================

This module is responsible for:
  1. Dynamic shifting-header row discovery for EIA-860 (Row 2) and EIA-923 (Row 6).
  2. Multi-source file extraction from Unity Catalog Volumes (/Volumes/.../raw_landing).
  3. Writing immutable raw append-only Delta tables with metadata tracking:
     - `_batch_id`: Ingestion batch identifier
     - `_source_file`: Originating file name/path
     - `_ingested_at`: UTC timestamp of ingestion
  4. Execution audit logging to `dwbi_catalog.bronze_staging.etl_run_log`.
  5. Pure Python fallback mode for offline testing and verification without active Spark.
"""

import os
import sys
import csv
import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add 03_ETL to path for config module discovery
MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

try:
    import config
except ImportError:
    from . import config  # Fallback for relative package imports


# In-memory execution audit tracker for offline/unit-test environments
RUN_LOG_HISTORY: List[Dict[str, Any]] = []


# ==============================================================================
# 1. HELPER FUNCTIONS: HEADER DISCOVERY, COLUMN CLEANING & BATCH METADATA
# ==============================================================================

def generate_batch_id(prefix: str = "BATCH_BRONZE") -> str:
    """Generates a unique, timestamped batch ID for pipeline traceability."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand_suffix = uuid.uuid4().hex[:6]
    return f"{prefix}_{now_str}_{rand_suffix}"


def clean_column_name(name: str) -> str:
    """
    Sanitizes raw column names into Delta Lake / Parquet-compliant identifiers:
    - Replaces whitespace, newlines, and special characters with underscores.
    - Strips leading/trailing underscores and converts to lowercase.
    - Example: 'Plant Id' -> 'plant_id', 'Combined Heat And\\nPower Plant' -> 'combined_heat_and_power_plant'
    """
    if not name:
        return "unnamed_column"
    cleaned = re.sub(r"[\s\r\n\t\-/\.\(\)\*]+", "_", str(name).strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned.lower() if cleaned else "unnamed_column"


def find_header_row_csv(
    lines_or_path: Any,
    scan_keys: Optional[List[str]] = None,
    max_scan_rows: int = 25
) -> Tuple[int, List[str]]:
    """
    Dynamically discovers the header row in CSV content by scanning the first N rows
    for key identifier tokens (e.g. 'Plant Code', 'Plant Id', 'utility_id').
    Returns (header_row_index, cleaned_header_list).
    """
    if scan_keys is None:
        scan_keys = ["plant code", "plant id", "utility_id", "orispl"]
    scan_keys_lower = [k.strip().lower() for k in scan_keys]

    # Normalize input lines
    if isinstance(lines_or_path, (str, Path)) and os.path.exists(str(lines_or_path)):
        with open(str(lines_or_path), "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = list(csv.reader(f))
    elif isinstance(lines_or_path, list):
        if len(lines_or_path) > 0 and isinstance(lines_or_path[0], list):
            reader = lines_or_path
        else:
            reader = list(csv.reader(lines_or_path))
    else:
        reader = []

    if not reader:
        return 0, []

    for idx, row in enumerate(reader[:max_scan_rows]):
        row_str = " ".join(str(cell).strip().lower() for cell in row)
        for key in scan_keys_lower:
            if key in row_str:
                headers = [clean_column_name(c) for c in row]
                return idx, headers

    # Default to first row if no sentinel keyword was matched
    headers = [clean_column_name(c) for c in reader[0]]
    return 0, headers


# ==============================================================================
# 2. AUDIT LOGGING ENGINE (`dwbi_catalog.bronze_staging.etl_run_log`)
# ==============================================================================

def log_etl_run(
    spark_session=None,
    batch_id: str = "",
    pipeline_step: str = "BRONZE_INGESTION",
    source_system: str = "",
    records_read: int = 0,
    records_inserted: int = 0,
    records_updated: int = 0,
    records_rejected: int = 0,
    execution_status: str = "SUCCESS",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Logs pipeline execution details into `bronze_staging.etl_run_log`.
    If SparkSession is active and connected, writes directly to Delta.
    Always records into RUN_LOG_HISTORY for audit and test verification.
    """
    start_time = start_time or datetime.now(timezone.utc)
    end_time = end_time or datetime.now(timezone.utc)

    log_record = {
        "batch_id": batch_id,
        "pipeline_step": pipeline_step,
        "source_system": source_system,
        "records_read": records_read,
        "records_inserted": records_inserted,
        "records_updated": records_updated,
        "records_rejected": records_rejected,
        "execution_status": execution_status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "error_message": error_message or ""
    }
    RUN_LOG_HISTORY.append(log_record)

    if spark_session is not None:
        try:
            from pyspark.sql import Row
            log_table = config.get_table_fqn("BRONZE", "etl_run_log")
            df_log = spark_session.createDataFrame([Row(**log_record)])
            df_log.write.format("delta").mode("append").saveAsTable(log_table)
            print(f"[AUDIT] Successfully logged execution to {log_table} for batch {batch_id}")
        except Exception as e:
            print(f"[WARN] Failed to write audit log to Spark Delta table: {e}")

    return log_record


# ==============================================================================
# 3. EXTRACTION ENGINES: CSV & JSON INGESTION WITH METADATA INJECTION
# ==============================================================================

def extract_csv_records(
    file_path: str,
    scan_keys: Optional[List[str]] = None,
    batch_id: Optional[str] = None
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Extracts records from a CSV file with dynamic header discovery and metadata columns.
    Returns (cleaned_fieldnames, list_of_row_dictionaries).
    """
    batch_id = batch_id or generate_batch_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    source_filename = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        raw_rows = list(csv.reader(f))

    if not raw_rows:
        return [], []

    header_idx, headers = find_header_row_csv(raw_rows, scan_keys=scan_keys)
    data_rows = raw_rows[header_idx + 1 :]

    records = []
    for row in data_rows:
        # Align row with headers
        record = {}
        for idx, col_name in enumerate(headers):
            val = row[idx].strip() if idx < len(row) else ""
            record[col_name] = val
        # Inject standard Bronze metadata columns
        record["_batch_id"] = batch_id
        record["_source_file"] = source_filename
        record["_ingested_at"] = now_iso
        records.append(record)

    all_headers = headers + ["_batch_id", "_source_file", "_ingested_at"]
    return all_headers, records


def extract_json_records(
    file_path: str,
    batch_id: Optional[str] = None
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Extracts records from a JSON array file and attaches Bronze metadata columns.
    Returns (cleaned_fieldnames, list_of_row_dictionaries).
    """
    batch_id = batch_id or generate_batch_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    source_filename = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []

    if not data:
        return [], []

    # Discover all distinct keys
    discovered_keys = {}
    for item in data:
        if isinstance(item, dict):
            for k in item.keys():
                cleaned = clean_column_name(k)
                discovered_keys[cleaned] = k

    records = []
    for item in data:
        if not isinstance(item, dict):
            continue
        row_dict = {}
        for clean_k, orig_k in discovered_keys.items():
            val = item.get(orig_k, "")
            row_dict[clean_k] = str(val) if val is not None else ""
        row_dict["_batch_id"] = batch_id
        row_dict["_source_file"] = source_filename
        row_dict["_ingested_at"] = now_iso
        records.append(row_dict)

    all_headers = list(discovered_keys.keys()) + ["_batch_id", "_source_file", "_ingested_at"]
    return all_headers, records


# ==============================================================================
# 4. BRONZE SOURCE EXTRACTORS
# ==============================================================================

def ingest_eia860_generator(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EIA-860 Generator Inventory into raw_eia860_generator."""
    batch_id = batch_id or generate_batch_id("EIA860_GEN")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_eia860_generator")

    # Resolve default source path
    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_eia860_generator.csv"

    scan_keys = config.SOURCES_CONFIG["EIA_860"]["HEADER_SCAN_KEYS"]
    headers, records = extract_csv_records(source_path, scan_keys=scan_keys, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EIA860_GEN", "EIA-860", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EIA860_GEN", "EIA-860", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_eia860_plant(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EIA-860 Plant Master into raw_eia860_plant."""
    batch_id = batch_id or generate_batch_id("EIA860_PLANT")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_eia860_plant")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_eia860_plant.csv"

    scan_keys = config.SOURCES_CONFIG["EIA_860"]["HEADER_SCAN_KEYS"]
    headers, records = extract_csv_records(source_path, scan_keys=scan_keys, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EIA860_PLANT", "EIA-860", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EIA860_PLANT", "EIA-860", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_eia860_enviro_assoc(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EIA-860 Schedule 6_1 Boiler-Generator Environmental Associations into raw_eia860_enviro_assoc."""
    batch_id = batch_id or generate_batch_id("EIA860_ASSOC")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_eia860_enviro_assoc")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_eia860_enviro_assoc.csv"

    scan_keys = config.SOURCES_CONFIG["EIA_860"]["HEADER_SCAN_KEYS"]
    headers, records = extract_csv_records(source_path, scan_keys=scan_keys, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EIA860_ASSOC", "EIA-860", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EIA860_ASSOC", "EIA-860", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_eia923_monthly_generation(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EIA-923 Monthly Generation & Fuel into raw_eia923_monthly_generation."""
    batch_id = batch_id or generate_batch_id("EIA923_GEN")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_eia923_monthly_generation")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_eia923_monthly_generation.csv"

    scan_keys = config.SOURCES_CONFIG["EIA_923"]["HEADER_SCAN_KEYS"]
    headers, records = extract_csv_records(source_path, scan_keys=scan_keys, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EIA923_GEN", "EIA-923", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EIA923_GEN", "EIA-923", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_epa_hourly_emissions(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EPA CAMPD Hourly CEMS Emissions into raw_epa_hourly_emissions."""
    batch_id = batch_id or generate_batch_id("EPA_CEMS")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_epa_hourly_emissions")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_epa_hourly_emissions.json"

    headers, records = extract_json_records(source_path, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EPA_CEMS", "EPA-CAMPD", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EPA_CEMS", "EPA-CAMPD", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_epa_eia_crosswalk(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EPA-EIA Crosswalk Bridge into raw_epa_eia_crosswalk."""
    batch_id = batch_id or generate_batch_id("EPA_XWALK")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_epa_eia_crosswalk")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_epa_eia_crosswalk.csv"

    headers, records = extract_csv_records(source_path, scan_keys=["camd_plant_id", "eia_plant_id"], batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EPA_XWALK", "EPA-EIA", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EPA_XWALK", "EPA-EIA", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_noaa_isd_weather(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests NOAA ISD Weather Observations into raw_noaa_isd_weather."""
    batch_id = batch_id or generate_batch_id("NOAA_WEATHER")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_noaa_isd_weather")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_noaa_isd_weather.json"

    headers, records = extract_json_records(source_path, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_NOAA_WEATHER", "NOAA-ISD", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_NOAA_WEATHER", "NOAA-ISD", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_noaa_isd_station_history(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests NOAA ISD Station History into raw_noaa_isd_station_history."""
    batch_id = batch_id or generate_batch_id("NOAA_STATION")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_noaa_isd_station_history")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_noaa_isd_station_history.csv"

    headers, records = extract_csv_records(source_path, scan_keys=["usaf", "station name", "icao"], batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_NOAA_STATION", "NOAA-ISD", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_NOAA_STATION", "NOAA-ISD", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


def ingest_eia930_hourly_grid(
    spark_session=None,
    source_path: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """Ingests EIA-930 Hourly Grid Balancing Authority Telemetry into raw_eia930_hourly_grid."""
    batch_id = batch_id or generate_batch_id("EIA930_GRID")
    start_time = datetime.now(timezone.utc)
    table_fqn = config.get_table_fqn("BRONZE", "raw_eia930_hourly_grid")

    if source_path is None:
        source_path = "archived/scratch_api_tests/sample_data/sample_eia930_hourly_grid.json"

    headers, records = extract_json_records(source_path, batch_id=batch_id)
    count = len(records)

    if spark_session is not None and count > 0:
        try:
            df = spark_session.createDataFrame(records)
            df.write.format("delta").mode("append").saveAsTable(table_fqn)
        except Exception as e:
            log_etl_run(spark_session, batch_id, "INGEST_EIA930_GRID", "EIA-930", count, 0, 0, count, "FAILED", start_time, datetime.now(timezone.utc), str(e))
            raise

    return log_etl_run(spark_session, batch_id, "INGEST_EIA930_GRID", "EIA-930", count, count, 0, 0, "SUCCESS", start_time, datetime.now(timezone.utc))


# ==============================================================================
# 5. MASTER BRONZE ORCHESTRATION SUITE
# ==============================================================================

def run_bronze_ingestion_suite(
    spark_session=None,
    master_batch_id: Optional[str] = None,
    custom_sources: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Executes end-to-end ingestion across all federal sources into Bronze Staging Delta tables.
    Returns a consolidated summary manifest of execution statuses and row counts.
    """
    master_batch_id = master_batch_id or generate_batch_id("BRONZE_MASTER")
    custom_sources = custom_sources or {}

    print("====================================================================")
    print(f"STARTING MASTER BRONZE INGESTION SUITE [Batch: {master_batch_id}]")
    print("====================================================================")

    extractors = [
        ("EIA-860 Generators", ingest_eia860_generator, custom_sources.get("eia860_gen")),
        ("EIA-860 Plants", ingest_eia860_plant, custom_sources.get("eia860_plant")),
        ("EIA-860 EnviroAssoc", ingest_eia860_enviro_assoc, custom_sources.get("eia860_assoc")),
        ("EIA-923 Monthly Gen", ingest_eia923_monthly_generation, custom_sources.get("eia923_gen")),
        ("EPA CAMPD Emissions", ingest_epa_hourly_emissions, custom_sources.get("epa_cems")),
        ("EPA-EIA Crosswalk", ingest_epa_eia_crosswalk, custom_sources.get("epa_xwalk")),
        ("NOAA ISD Weather", ingest_noaa_isd_weather, custom_sources.get("noaa_weather")),
        ("NOAA Station History", ingest_noaa_isd_station_history, custom_sources.get("noaa_station")),
        ("EIA-930 Grid Telemetry", ingest_eia930_hourly_grid, custom_sources.get("eia930_grid")),
    ]

    results = []
    total_records = 0

    for name, extractor_fn, src_path in extractors:
        try:
            print(f"-> Ingesting {name}...")
            res = extractor_fn(spark_session=spark_session, source_path=src_path, batch_id=master_batch_id)
            results.append(res)
            total_records += res.get("records_inserted", 0)
            print(f"   ✓ {name}: {res.get('records_inserted', 0)} records ingested.")
        except Exception as e:
            print(f"   ✗ {name} FAILED: {e}")
            results.append({
                "source_system": name,
                "execution_status": "FAILED",
                "error_message": str(e),
                "records_inserted": 0
            })

    summary = {
        "master_batch_id": master_batch_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_sources_attempted": len(extractors),
        "total_sources_successful": sum(1 for r in results if r.get("execution_status") == "SUCCESS"),
        "total_records_ingested": total_records,
        "results": results
    }

    print("====================================================================")
    print(f"MASTER BRONZE INGESTION COMPLETE: {summary['total_sources_successful']}/{summary['total_sources_attempted']} successful ({total_records} records)")
    print("====================================================================")
    return summary


# Databricks execution trigger
try:
    if "spark" in locals() or "spark" in globals():
        run_bronze_ingestion_suite(spark)
except NameError:
    pass

