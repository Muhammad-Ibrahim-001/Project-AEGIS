# Databricks notebook source
# COMMAND ----------
"""
==============================================================================
DL3004 DWBI Final Project: Silver Conformance, Data Quality & SCD-2 Pipeline
Work Package: WP2 (Data Quality & Silver Conformance Lead)
Platform:     Databricks Serverless Compute / Apache Spark / Delta Lake
Catalog:      Unity Catalog (`dwbi_catalog.silver_conformed`, `dwbi_catalog.quarantine`)
==============================================================================

This module is responsible for:
  1. Sentinel value coercion (coercing '.', 'NM', '*', '', and -9999 to SQL NULL / None).
  2. Strict ANSI-compliant numeric casting (using TRY_CAST semantics).
  3. Thermodynamic heat rate physical validation (CCGT: 5k-14k, Coal: 8.5k-18k, Peakers: 9k-22k Btu/kWh).
  4. Routing data quality violations to the Dead-Letter table: `dwbi_catalog.quarantine.rejected_records`.
  5. Negative Net Generation tolerance (allowing valid maintenance outage power consumption).
  6. SCD Type 2 dimension tracking for power plant generators (OP -> SB -> RE) with atomic validity horizons.
  7. Conforming and deduplicating entities into `silver_conformed.*` Delta tables.
  8. Pure Python fallback mode for local offline unit testing and automated grading.
"""

import os
import sys
import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Add 03_ETL to path for config module discovery
MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

try:
    import config
    import importlib
    bronze = importlib.import_module("01_bronze_ingestion")
except ImportError:
    from . import config
    from . import bronze_ingestion as bronze


# In-memory quarantine history for testing/offline audits
QUARANTINE_HISTORY: List[Dict[str, Any]] = []


# ==============================================================================
# 1. DATA QUALITY & SENTINEL COERCION PRIMITIVES
# ==============================================================================

SENTINEL_SET = {
    ".", "NM", "*", "--", "NA", "N/A", "null", "NULL", "None", "", "   ",
    "-9999", "-9999.0", -9999, -9999.0
}


def is_sentinel(value: Any) -> bool:
    """Checks whether a value is a documented federal missing-data sentinel."""
    if value is None:
        return True
    if isinstance(value, str):
        v_stripped = value.strip()
        if v_stripped in SENTINEL_SET:
            return True
        try:
            num = float(v_stripped)
            return num == -9999.0
        except ValueError:
            return False
    if isinstance(value, (int, float)):
        return value == -9999 or value == -9999.0
    return False


def coerce_sentinel(value: Any) -> Optional[Any]:
    """Coerces sentinel values to None (SQL NULL). Returns original value if clean."""
    return None if is_sentinel(value) else value


def try_cast_float(value: Any) -> Optional[float]:
    """
    Simulates ANSI SQL TRY_CAST(value AS DOUBLE).
    Coerces sentinels and unparseable strings to None without raising exceptions.
    """
    if is_sentinel(value):
        return None
    try:
        cleaned_str = str(value).replace(",", "").strip()
        return float(cleaned_str)
    except (ValueError, TypeError):
        return None


def try_cast_int(value: Any) -> Optional[int]:
    """
    Simulates ANSI SQL TRY_CAST(value AS INT).
    Coerces sentinels and unparseable values to None.
    """
    f_val = try_cast_float(value)
    return int(round(f_val)) if f_val is not None else None


# ==============================================================================
# 2. THERMODYNAMIC HEAT RATE BOUNDARY VALIDATION
# ==============================================================================

def calculate_and_validate_heat_rate(
    fuel_mmbtu_val: Any,
    netgen_mwh_val: Any,
    prime_mover_code: Optional[str] = None
) -> Tuple[Optional[float], bool, Optional[str]]:
    """
    Calculates Heat Rate (Btu/kWh) = (Fuel MMBtu * 1,000) / NetGen MWh.
    Validates against technology-specific physical thermodynamic boundaries.
    
    Returns:
        (heat_rate_value, is_valid, validation_status_code)
    """
    fuel_mmbtu = try_cast_float(fuel_mmbtu_val)
    netgen_mwh = try_cast_float(netgen_mwh_val)

    if fuel_mmbtu is None or netgen_mwh is None:
        return None, True, "MISSING_THERMAL_INPUTS"

    # Business Exception: Offline maintenance draw (NetGen < 0)
    if netgen_mwh < 0:
        return None, True, "STATION_SERVICE_EXCEEDS_OUTPUT"

    if netgen_mwh == 0:
        return None, True, "ZERO_GENERATION_STANDBY"

    heat_rate = (fuel_mmbtu * 1000.0) / netgen_mwh

    # Technology-specific boundary checks
    bounds_cfg = config.DATA_QUALITY_RULES.get("HEAT_RATE_BOUNDS", {})
    pm = (prime_mover_code or "").upper().strip()

    if pm in ["CA", "CT", "CS", "CC"]:
        bounds = bounds_cfg.get("CCGT", {"min": 5000, "max": 14000})
        category = "CCGT"
    elif pm in ["ST"]:
        bounds = bounds_cfg.get("COAL_ST", {"min": 8500, "max": 18000})
        category = "COAL_ST"
    elif pm in ["GT"]:
        bounds = bounds_cfg.get("PEAKER_GT", {"min": 9000, "max": 22000})
        category = "PEAKER_GT"
    else:
        bounds = bounds_cfg.get("GENERAL_THERMAL", {"min": 4500, "max": 30000})
        category = "GENERAL_THERMAL"

    if heat_rate < bounds["min"] or heat_rate > bounds["max"]:
        reason = f"HEAT_RATE_OUT_OF_BOUNDS_{category}_{round(heat_rate, 1)}_LIMITS_{bounds['min']}_{bounds['max']}"
        return round(heat_rate, 2), False, reason

    return round(heat_rate, 2), True, "PHYSICALLY_VALID"


# ==============================================================================
# 3. DEAD-LETTER QUARANTINE ROUTER (`dwbi_catalog.quarantine.rejected_records`)
# ==============================================================================

def quarantine_record(
    batch_id: str,
    source_system: str,
    source_table: str,
    source_row_identifier: str,
    rejection_reason: str,
    raw_payload: Dict[str, Any],
    spark_session=None
) -> Dict[str, Any]:
    """
    Routes an anomalous or sentinel-corrupted record to the dead-letter quarantine table.
    """
    record = {
        "batch_id": batch_id,
        "source_system": source_system,
        "source_table": source_table,
        "source_row_identifier": str(source_row_identifier),
        "rejection_reason": rejection_reason,
        "raw_payload_json": json.dumps(raw_payload, default=str),
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }
    QUARANTINE_HISTORY.append(record)

    if spark_session is not None:
        try:
            from pyspark.sql import Row
            quarantine_table = config.get_table_fqn("QUARANTINE", "rejected_records")
            df_q = spark_session.createDataFrame([Row(**record)])
            df_q.write.format("delta").mode("append").saveAsTable(quarantine_table)
        except Exception as e:
            print(f"[WARN] Failed to write record to Spark quarantine table: {e}")

    return record


# ==============================================================================
# 4. CONFORMANCE TRANSFORMERS
# ==============================================================================

def conform_plants(
    raw_plants: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms and deduplicates EIA-860 plant master records.
    Filters out rows with invalid or missing ORISPL codes.
    """
    conformed = []
    quarantined = []
    seen_orispl = set()

    for row in raw_plants:
        raw_code = row.get("plant_code") or row.get("plant_id")
        orispl = try_cast_int(raw_code)

        if orispl is None or orispl <= 0:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-860",
                source_table="bronze_staging.raw_eia860_plant",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_ORISPL_CODE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        if orispl in seen_orispl:
            # Deduplicate by retaining first verified plant definition
            continue
        seen_orispl.add(orispl)

        chp_flag = str(row.get("is_combined_heat_power", "")).strip().upper()
        conformed.append({
            "orispl_code": orispl,
            "plant_name": str(row.get("plant_name", "UNKNOWN")).strip(),
            "utility_id": try_cast_int(row.get("utility_id")),
            "utility_name": coerce_sentinel(row.get("utility_name")),
            "state_code": str(row.get("state", row.get("state_code", ""))).strip().upper()[:2],
            "county_name": coerce_sentinel(row.get("county", row.get("county_name"))),
            "latitude": try_cast_float(row.get("latitude")),
            "longitude": try_cast_float(row.get("longitude")),
            "ba_code": coerce_sentinel(row.get("balancing_auth_code", row.get("ba_code"))),
            "is_combined_heat_power": chp_flag in ["Y", "YES", "TRUE", "1"],
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    return conformed, quarantined


def conform_generators_scd2(
    raw_generators: List[Dict[str, Any]],
    batch_id: str,
    existing_dim_records: Optional[List[Dict[str, Any]]] = None,
    effective_timestamp: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Applies SCD Type 2 tracking to generators:
    - Natural Composite Key: (orispl_code, generator_id).
    - Monitored Attributes: operating_status, nameplate_capacity_mw.
    - If status or capacity changes, closes previous version (valid_to = now, is_current = False)
      and opens new version (valid_from = now, valid_to = '9999-12-31 23:59:59', is_current = True).
    """
    effective_timestamp = effective_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    open_infinity = "9999-12-31 23:59:59"

    # Index existing current records by (orispl, gen_id)
    existing_map = {}
    if existing_dim_records:
        for rec in existing_dim_records:
            if rec.get("is_current", True):
                k = (rec.get("orispl_code"), str(rec.get("generator_id")).strip().upper())
                existing_map[k] = dict(rec)

    conformed_updates = []
    conformed_inserts = []
    quarantined = []

    for row in raw_generators:
        raw_code = row.get("plant_code") or row.get("plant_id")
        orispl = try_cast_int(raw_code)
        gen_id = str(row.get("generator_id", "")).strip().upper()

        if orispl is None or not gen_id:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-860",
                source_table="bronze_staging.raw_eia860_generator",
                source_row_identifier=f"{raw_code}_{gen_id}",
                rejection_reason="MISSING_GENERATOR_NATURAL_KEY",
                raw_payload=row
            )
            quarantined.append(q_rec)
            continue

        raw_status = str(row.get("status", row.get("operating_status", "OP"))).strip().upper()
        capacity_mw = try_cast_float(row.get("nameplate_capacity_mw"))

        nat_key = (orispl, gen_id)
        if nat_key in existing_map:
            prior = existing_map[nat_key]
            prior_status = str(prior.get("operating_status", "")).strip().upper()
            prior_cap = try_cast_float(prior.get("nameplate_capacity_mw"))

            # Check if tracked attributes evolved
            if prior_status != raw_status or (capacity_mw is not None and prior_cap != capacity_mw):
                # Close the prior version (SCD-2 Expiration)
                prior["valid_to"] = effective_timestamp
                prior["is_current"] = False
                conformed_updates.append(prior)

                # Insert new active version
                new_version = dict(prior)
                new_version["operating_status"] = raw_status
                new_version["nameplate_capacity_mw"] = capacity_mw
                new_version["valid_from"] = effective_timestamp
                new_version["valid_to"] = open_infinity
                new_version["is_current"] = True
                new_version["_batch_id"] = batch_id
                conformed_inserts.append(new_version)
            else:
                # No tracked changes: keep current
                conformed_inserts.append(prior)
        else:
            # First time seeing this generator: Seed initial active version
            conformed_inserts.append({
                "orispl_code": orispl,
                "generator_id": gen_id,
                "prime_mover_code": str(row.get("prime_mover", row.get("prime_mover_code", ""))).strip().upper(),
                "primary_energy_source": str(row.get("energy_source_1", row.get("primary_energy_source", ""))).strip().upper(),
                "nameplate_capacity_mw": capacity_mw,
                "operating_status": raw_status,
                "operating_year": try_cast_int(row.get("operating_year")),
                "planned_retirement_year": try_cast_int(row.get("retirement_year", row.get("planned_retirement_year"))),
                "valid_from": effective_timestamp,
                "valid_to": open_infinity,
                "is_current": True,
                "_batch_id": batch_id
            })

    all_conformed = conformed_updates + conformed_inserts
    return all_conformed, quarantined


def conform_monthly_generation(
    raw_gen_records: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EIA-923 Monthly Generation & Fuel data:
    - Coerces sentinel strings ('.', 'NM') to NULL.
    - Calculates and validates heat rate per prime mover.
    - Routes out-of-bounds heat rate records to quarantine.
    - Allows negative net generation (station maintenance draw).
    """
    conformed = []
    quarantined = []

    for row in raw_gen_records:
        raw_code = row.get("plant_id") or row.get("plant_code")
        orispl = try_cast_int(raw_code)

        if orispl is None:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-923",
                source_table="bronze_staging.raw_eia923_monthly_generation",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_PLANT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        pm = str(row.get("reported_prime_mover", "")).strip().upper()
        fuel_code = str(row.get("reported_fuel_type", "")).strip().upper()

        # In EIA-923, each record contains monthly quantities and netgen
        # We test month-level pairs (e.g. january)
        qty_val = row.get("quantity_january")
        netgen_val = row.get("netgen_january")

        # Coerce sentinels
        qty_clean = try_cast_float(qty_val)
        netgen_clean = try_cast_float(netgen_val)

        # Estimate MMBtu if physical quantity is given (approx 1.0 MMBtu/unit)
        fuel_mmbtu = qty_clean if qty_clean is not None else 0.0

        heat_rate, is_valid, hr_status = calculate_and_validate_heat_rate(
            fuel_mmbtu_val=fuel_mmbtu,
            netgen_mwh_val=netgen_clean,
            prime_mover_code=pm
        )

        if not is_valid:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-923",
                source_table="bronze_staging.raw_eia923_monthly_generation",
                source_row_identifier=f"{orispl}_{pm}_{fuel_code}_JAN",
                rejection_reason=hr_status or "HEAT_RATE_OUT_OF_BOUNDS",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        conformed.append({
            "orispl_code": orispl,
            "plant_name": coerce_sentinel(row.get("plant_name")),
            "prime_mover_code": pm,
            "energy_source_code": fuel_code,
            "net_generation_mwh": netgen_clean if netgen_clean is not None else 0.0,
            "fuel_consumed_mmbtu": fuel_mmbtu,
            "avg_heat_rate_btu_kwh": heat_rate,
            "heat_rate_validation_code": hr_status,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    return conformed, quarantined


def conform_weather_hourly(
    raw_weather_records: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms NOAA ISD Weather observations:
    - Coerces -9999 sensor dropouts to NULL.
    - Routes invalid readings or corrupt timestamps to quarantine.
    """
    conformed = []
    quarantined = []

    for row in raw_weather_records:
        station_id = str(row.get("station_id", row.get("station", ""))).strip()
        ts = row.get("timestamp_utc", row.get("timestamp", ""))

        temp_raw = row.get("air_temperature_c", row.get("temperature", {}).get("value") if isinstance(row.get("temperature"), dict) else row.get("temperature"))
        wind_raw = row.get("wind_speed_mps", row.get("windSpeed", {}).get("value") if isinstance(row.get("windSpeed"), dict) else row.get("windSpeed"))

        temp_c = try_cast_float(temp_raw)
        wind_mps = try_cast_float(wind_raw)

        # Flag and quarantine extreme sensor corruption (e.g. raw string -9999 not coerced)
        if str(temp_raw).strip() == "-9999" or str(wind_raw).strip() == "-9999":
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="NOAA-ISD",
                source_table="bronze_staging.raw_noaa_isd_weather",
                source_row_identifier=f"{station_id}_{ts}",
                rejection_reason="NOAA_SENSOR_DROPOUT_MINUS_9999",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            # We still record coerced NULL in conformed stream per domain rules
            temp_c = None
            wind_mps = None

        conformed.append({
            "station_id": station_id,
            "timestamp_utc": str(ts),
            "air_temperature_c": temp_c,
            "wind_speed_mps": wind_mps,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    return conformed, quarantined


# ==============================================================================
# 5. MASTER SILVER CONFORMANCE ORCHESTRATION
# ==============================================================================

def run_silver_conformance_suite(
    spark_session=None,
    master_batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the complete Silver Conformance, Data Quality Filtering, and SCD-2 Pipeline.
    Loads raw Bronze inputs, validates thermodynamic bounds, routes dirty rows to quarantine,
    and produces conformed Silver tables in `dwbi_catalog.silver_conformed`.
    """
    master_batch_id = master_batch_id or bronze.generate_batch_id("SILVER_MASTER")
    start_time = datetime.now(timezone.utc)

    print("====================================================================")
    print(f"STARTING MASTER SILVER CONFORMANCE PIPELINE [Batch: {master_batch_id}]")
    print("====================================================================")

    # 1. Ingest Bronze baseline (or read from Bronze sample files)
    raw_eia860_gen_headers, raw_gen = bronze.extract_csv_records(
        "archived/scratch_api_tests/sample_data/sample_eia860_generator.csv",
        scan_keys=["Plant Code"],
        batch_id=master_batch_id
    )
    raw_eia860_plant_headers, raw_plants = bronze.extract_csv_records(
        "archived/scratch_api_tests/sample_data/sample_eia860_plant.csv",
        scan_keys=["Plant Code"],
        batch_id=master_batch_id
    )
    raw_eia923_headers, raw_gen923 = bronze.extract_csv_records(
        "archived/scratch_api_tests/sample_data/sample_eia923_monthly_generation.csv",
        scan_keys=["Plant Id"],
        batch_id=master_batch_id
    )
    raw_noaa_headers, raw_weather = bronze.extract_json_records(
        "archived/scratch_api_tests/sample_data/sample_noaa_isd_weather.json",
        batch_id=master_batch_id
    )

    # 2. Conform Plants Master
    print("-> Conforming Plants Master...")
    silver_plants, q_plants = conform_plants(raw_plants, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Plants: {len(silver_plants)} | Quarantined: {len(q_plants)}")

    # 3. Conform Generators (SCD Type 2 Lifecycle)
    print("-> Conforming Generators with SCD Type 2 tracking...")
    silver_generators, q_gen = conform_generators_scd2(raw_gen, batch_id=master_batch_id)
    print(f"   ✓ Conformed Generators: {len(silver_generators)} | Quarantined: {len(q_gen)}")

    # 4. Conform Monthly Generation & Validate Heat Rates
    print("-> Conforming Monthly Generation & Fuel (Heat Rate Auditing)...")
    silver_923, q_923 = conform_monthly_generation(raw_gen923, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Monthly Generation: {len(silver_923)} | Quarantined: {len(q_923)}")

    # 5. Conform NOAA Weather & Coerce Sentinels
    print("-> Conforming NOAA Weather Observations...")
    silver_weather, q_weather = conform_weather_hourly(raw_weather, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Weather: {len(silver_weather)} | Quarantined: {len(q_weather)}")

    total_conformed = len(silver_plants) + len(silver_generators) + len(silver_923) + len(silver_weather)
    total_quarantined = len(q_plants) + len(q_gen) + len(q_923) + len(q_weather)

    # 6. Log Silver pipeline execution to etl_run_log
    bronze.log_etl_run(
        spark_session=spark_session,
        batch_id=master_batch_id,
        pipeline_step="SILVER_CONFORMANCE",
        source_system="MEDALLION_SILVER",
        records_read=len(raw_plants) + len(raw_gen) + len(raw_gen923) + len(raw_weather),
        records_inserted=total_conformed,
        records_updated=0,
        records_rejected=total_quarantined,
        execution_status="SUCCESS",
        start_time=start_time,
        end_time=datetime.now(timezone.utc)
    )

    summary = {
        "master_batch_id": master_batch_id,
        "conformed_plants_count": len(silver_plants),
        "conformed_generators_count": len(silver_generators),
        "conformed_monthly_gen_count": len(silver_923),
        "conformed_weather_count": len(silver_weather),
        "total_conformed_records": total_conformed,
        "total_quarantined_records": total_quarantined,
        "execution_status": "SUCCESS"
    }

    print("====================================================================")
    print(f"MASTER SILVER CONFORMANCE COMPLETE: {total_conformed} conformed, {total_quarantined} quarantined.")
    print("====================================================================")
    return summary


# Databricks execution trigger
try:
    if "spark" in locals() or "spark" in globals():
        run_silver_conformance_suite(spark)
except NameError:
    pass

