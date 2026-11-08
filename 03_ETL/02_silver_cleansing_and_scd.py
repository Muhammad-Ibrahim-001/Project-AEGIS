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
import csv
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


def standardize_text(value: Any, mode: str = "title") -> Optional[str]:
    """
    Standardizes string text:
    - Strips leading and trailing whitespace.
    - Collapses multiple internal whitespace characters into a single space.
    - Coerces sentinel values and empty strings to None.
    - If mode == 'title': Converts words to Title Case (e.g. ' lahore ' and 'LAHORE' -> 'Lahore').
    - If mode == 'upper': Converts string to UPPERCASE (e.g. ' pjm ' -> 'PJM').
    - If mode == 'lower': Converts string to lowercase.
    """
    if is_sentinel(value):
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    collapsed = re.sub(r"\s+", " ", val_str)
    if not collapsed:
        return None
    if mode == "title":
        return collapsed.title()
    elif mode == "upper":
        return collapsed.upper()
    elif mode == "lower":
        return collapsed.lower()
    return collapsed


# Global cleaning step log history
CLEANING_STEP_LOG: List[Dict[str, Any]] = []


def record_cleaning_step(
    batch_id: str,
    step_name: str,
    target_table: str,
    rows_in: int,
    rows_changed: int,
    rows_removed: int,
    rows_quarantined: int,
    rows_out: Optional[int] = None,
    spark_session=None
) -> Dict[str, Any]:
    """
    Logs data cleansing metrics (in, changed, removed, quarantined, out)
    to dwbi_catalog.silver_conformed.cleaning_step_log in Databricks
    or to 02_Data/cleaned_data/cleaning_step_log.csv when running offline.
    """
    if rows_out is None:
        rows_out = rows_in - rows_removed - rows_quarantined

    entry = {
        "batch_id": batch_id,
        "step_name": step_name,
        "target_table": target_table,
        "rows_in": rows_in,
        "rows_changed": rows_changed,
        "rows_removed": rows_removed,
        "rows_quarantined": rows_quarantined,
        "rows_out": rows_out,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    CLEANING_STEP_LOG.append(entry)

    # Persist to local CSV
    try:
        out_dir = MODULE_DIR.parent / "02_Data" / "cleaned_data"
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_file = out_dir / "cleaning_step_log.csv"
        file_exists = csv_file.exists()
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "batch_id", "step_name", "target_table", "rows_in",
                "rows_changed", "rows_removed", "rows_quarantined", "rows_out", "logged_at"
            ])
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry)
    except Exception as e:
        print(f"[WARN] Failed to write cleaning step log to CSV: {e}")

    if spark_session is not None:
        try:
            from pyspark.sql import Row
            log_table = config.get_table_fqn("SILVER", "cleaning_step_log")
            df_log = spark_session.createDataFrame([Row(**entry)])
            df_log.write.format("delta").mode("append").saveAsTable(log_table)
        except Exception as e:
            print(f"[WARN] Failed to write cleaning step log to Spark Delta table: {e}")

    return entry


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
    Standardizes text (plant_name, county_name, utility_name in Title Case; state_code, ba_code in Uppercase).
    Deduplicates on orispl_code, keeping latest, counting duplicates.
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_plants)
    rows_changed = 0
    rows_removed = 0
    seen_plants = {}  # orispl -> index in conformed

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

        raw_name = row.get("plant_name", "UNKNOWN")
        std_name = standardize_text(raw_name, mode="title") or "Unknown Plant"
        raw_county = row.get("county", row.get("county_name"))
        std_county = standardize_text(raw_county, mode="title")
        raw_util = row.get("utility_name")
        std_util = standardize_text(raw_util, mode="title")

        raw_state = str(row.get("state", row.get("state_code", "")))
        std_state = (standardize_text(raw_state, mode="upper") or "")[:2]
        raw_ba = row.get("balancing_authority_code") or row.get("balancing_auth_code") or row.get("ba_code")
        std_ba = standardize_text(raw_ba, mode="upper")

        if (std_name != raw_name or std_county != raw_county or 
            std_util != raw_util or std_state != raw_state or std_ba != raw_ba):
            rows_changed += 1

        chp_flag = str(row.get("is_combined_heat_power", "")).strip().upper()
        plant_rec = {
            "orispl_code": orispl,
            "plant_name": std_name,
            "utility_id": try_cast_int(row.get("utility_id")),
            "utility_name": std_util,
            "state_code": std_state,
            "county_name": std_county,
            "latitude": try_cast_float(row.get("latitude")),
            "longitude": try_cast_float(row.get("longitude")),
            "ba_code": std_ba,
            "is_combined_heat_power": chp_flag in ["Y", "YES", "TRUE", "1"],
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        if orispl in seen_plants:
            rows_removed += 1
            conformed[seen_plants[orispl]] = plant_rec
        else:
            seen_plants[orispl] = len(conformed)
            conformed.append(plant_rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_PLANTS",
        target_table="silver_plants",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
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
    - Deduplicates on (orispl_code, generator_id) within incoming batch, keeping latest.
    - Standardizes codes and text to uppercase.
    """
    effective_timestamp = effective_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    open_infinity = "9999-12-31 23:59:59"
    rows_in = len(raw_generators)
    rows_changed = 0
    rows_removed = 0

    # Index existing current records by (orispl, gen_id)
    existing_map = {}
    if existing_dim_records:
        for rec in existing_dim_records:
            if rec.get("is_current", True):
                k = (rec.get("orispl_code"), str(rec.get("generator_id")).strip().upper())
                existing_map[k] = dict(rec)

    # First pass: Deduplicate incoming batch by natural key (orispl, gen_id), keeping latest
    deduped_raw = {}
    quarantined = []
    for row in raw_generators:
        raw_code = row.get("plant_code") or row.get("plant_id")
        orispl = try_cast_int(raw_code)
        gen_id = standardize_text(row.get("generator_id", ""), mode="upper")

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

        nat_key = (orispl, gen_id)
        if nat_key in deduped_raw:
            rows_removed += 1
        deduped_raw[nat_key] = row

    conformed_updates = []
    conformed_inserts = []

    for (orispl, gen_id), row in deduped_raw.items():
        raw_status = row.get("status", row.get("operating_status", "OP"))
        std_status = standardize_text(raw_status, mode="upper") or "OP"
        capacity_mw = try_cast_float(row.get("nameplate_capacity_mw"))
        pm = standardize_text(row.get("prime_mover", row.get("prime_mover_code", "")), mode="upper") or ""
        energy = standardize_text(row.get("energy_source_1", row.get("primary_energy_source", "")), mode="upper") or ""

        if std_status != raw_status or pm != row.get("prime_mover") or energy != row.get("energy_source_1"):
            rows_changed += 1

        nat_key = (orispl, gen_id)
        if nat_key in existing_map:
            prior = existing_map[nat_key]
            prior_status = str(prior.get("operating_status", "")).strip().upper()
            prior_cap = try_cast_float(prior.get("nameplate_capacity_mw"))

            # Check if tracked attributes evolved
            if prior_status != std_status or (capacity_mw is not None and prior_cap != capacity_mw):
                # Close the prior version (SCD-2 Expiration)
                prior["valid_to"] = effective_timestamp
                prior["is_current"] = False
                conformed_updates.append(prior)

                # Insert new active version
                new_version = dict(prior)
                new_version["operating_status"] = std_status
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
                "prime_mover_code": pm,
                "primary_energy_source": energy,
                "nameplate_capacity_mw": capacity_mw,
                "operating_status": std_status,
                "operating_year": try_cast_int(row.get("operating_year")),
                "planned_retirement_year": try_cast_int(row.get("retirement_year", row.get("planned_retirement_year"))),
                "valid_from": effective_timestamp,
                "valid_to": open_infinity,
                "is_current": True,
                "_batch_id": batch_id
            })

    all_conformed = conformed_updates + conformed_inserts
    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_GENERATORS_SCD2",
        target_table="silver_generators",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(all_conformed)
    )
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
    - Standardizes text (plant_name in Title Case; prime_mover_code, energy_source_code in Uppercase).
    - Computes snapshot month_start_date_key (YYYYMMDD).
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_gen_records)
    rows_changed = 0
    rows_removed = 0

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

        raw_name = row.get("plant_name")
        std_name = standardize_text(raw_name, mode="title")
        raw_pm = row.get("reported_prime_mover") or row.get("prime_mover_code") or ""
        pm = standardize_text(raw_pm, mode="upper") or ""
        raw_fuel = row.get("reported_fuel_type_code") or row.get("reported_fuel_type") or row.get("energy_source_code") or ""
        fuel_code = standardize_text(raw_fuel, mode="upper") or ""

        # In EIA-923, each record contains monthly quantities and netgen
        qty_val = row.get("quantity_january")
        netgen_val = row.get("netgen_january")

        # Coerce sentinels
        qty_clean = try_cast_float(qty_val)
        netgen_clean = try_cast_float(netgen_val)
        sentinel_coerced = is_sentinel(qty_val) or is_sentinel(netgen_val)

        if (std_name != raw_name or pm != str(raw_pm).strip() or 
            fuel_code != str(raw_fuel).strip() or sentinel_coerced):
            rows_changed += 1

        year_val = try_cast_int(row.get("YEAR") or row.get("year")) or 2023
        month_val = try_cast_int(row.get("MONTH") or row.get("month")) or 1
        month_start_date_key = year_val * 10000 + (month_val * 100) + 1

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
            "plant_name": std_name,
            "prime_mover_code": pm,
            "energy_source_code": fuel_code,
            "year": year_val,
            "month_start_date_key": month_start_date_key,
            "net_generation_mwh": netgen_clean if netgen_clean is not None else 0.0,
            "fuel_consumed_mmbtu": fuel_mmbtu,
            "avg_heat_rate_btu_kwh": heat_rate,
            "heat_rate_validation_code": hr_status,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_MONTHLY_GENERATION",
        target_table="silver_monthly_generation",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined


def conform_weather_hourly(
    raw_weather_records: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms NOAA ISD Weather observations:
    - Coerces -9999 sensor dropouts to NULL.
    - Standardizes station_id to uppercase.
    - Routes invalid readings or corrupt timestamps to quarantine.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_weather_records)
    rows_changed = 0
    rows_removed = 0

    for row in raw_weather_records:
        raw_station = row.get("station_id", row.get("station", ""))
        station_id = standardize_text(raw_station, mode="upper") or "UNKNOWN"
        ts = row.get("timestamp_utc", row.get("timestamp", ""))

        # Check for corrupt timestamps or missing station
        if not ts or "BAD" in str(ts) or "CORRUPT" in str(ts) or station_id == "UNKNOWN":
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="NOAA-ISD",
                source_table="bronze_staging.raw_noaa_isd_weather",
                source_row_identifier=f"{station_id}_{ts}",
                rejection_reason="INVALID_OR_CORRUPT_TIMESTAMP",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        temp_raw = row.get("air_temperature_c", row.get("temperature", {}).get("value") if isinstance(row.get("temperature"), dict) else row.get("temperature"))
        wind_raw = row.get("wind_speed_mps", row.get("windSpeed", {}).get("value") if isinstance(row.get("windSpeed"), dict) else row.get("windSpeed"))

        temp_c = try_cast_float(temp_raw)
        wind_mps = try_cast_float(wind_raw)

        # Domain rule: -9999 is NOAA missing value sentinel, coerced to NULL
        is_temp_sentinel = str(temp_raw).strip() in ["-9999", "-9999.0"] or is_sentinel(temp_raw)
        is_wind_sentinel = str(wind_raw).strip() in ["-9999", "-9999.0"] or is_sentinel(wind_raw)

        if is_temp_sentinel:
            temp_c = None
        if is_wind_sentinel:
            wind_mps = None

        if station_id != str(raw_station).strip() or is_temp_sentinel or is_wind_sentinel:
            rows_changed += 1

        conformed.append({
            "station_id": station_id,
            "timestamp_utc": str(ts),
            "air_temperature_c": temp_c,
            "wind_speed_mps": wind_mps,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_WEATHER_HOURLY",
        target_table="silver_weather_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined


def conform_emissions_hourly(
    raw_emissions: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EPA CAMPD Hourly Smokestack Emissions:
    - Sentinel coercion on all numeric metrics (gross load, heat input, SO2, NOx, CO2).
    - Date format validation (YYYY-MM-DD -> date_key YYYYMMDD); invalid dates routed to quarantine.
    - Hour validation (0-23); invalid or out-of-bounds hours routed to quarantine.
    - Facility and unit key validation; missing keys routed to quarantine.
    - Deduplication on (orispl_code, unit_id, date_key, hour_of_day), keeping latest.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_emissions)
    rows_changed = 0
    rows_removed = 0
    seen_keys = {}  # (orispl, unit, date_key, hour) -> index in conformed

    for row in raw_emissions:
        raw_code = (row.get("oris_code") or row.get("facilityid") or row.get("facilityId") or 
                    row.get("plant_code") or row.get("facility_id"))
        orispl = try_cast_int(raw_code)

        if orispl is None or orispl <= 0:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_PLANT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_unit = row.get("unit_id") or row.get("unitid") or row.get("unitId")
        unit_id = standardize_text(raw_unit, mode="upper")
        if not unit_id:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_UNKNOWN_UNIT",
                rejection_reason="MISSING_UNIT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Parse date
        raw_date = row.get("date_observed") or row.get("date")
        date_key = None
        if raw_date is not None:
            clean_date_str = str(raw_date).strip().replace("-", "")
            if len(clean_date_str) == 8 and clean_date_str.isdigit():
                date_key = try_cast_int(clean_date_str)

        if date_key is None or date_key < 19000101 or date_key > 21000101:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_{unit_id}_{raw_date}",
                rejection_reason="INVALID_DATE_FORMAT",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Parse hour
        raw_hour = row.get("hour_observed") if row.get("hour_observed") is not None else row.get("hour")
        hour_of_day = try_cast_int(raw_hour)
        if hour_of_day is None or hour_of_day < 0 or hour_of_day > 23:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_{unit_id}_{date_key}_{raw_hour}",
                rejection_reason="INVALID_HOUR_RANGE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Clean measures
        gross_load = try_cast_float(row.get("gross_load_mw") if row.get("gross_load_mw") is not None else (row.get("grossload") if row.get("grossload") is not None else row.get("grossLoad")))
        heat_input = try_cast_float(row.get("heat_input_mmbtu") if row.get("heat_input_mmbtu") is not None else (row.get("heatinput") if row.get("heatinput") is not None else row.get("heatInput")))
        so2_mass = try_cast_float(row.get("so2_mass_lbs") if row.get("so2_mass_lbs") is not None else (row.get("so2mass") if row.get("so2mass") is not None else row.get("so2Mass")))
        nox_mass = try_cast_float(row.get("nox_mass_lbs") if row.get("nox_mass_lbs") is not None else (row.get("noxmass") if row.get("noxmass") is not None else row.get("noxMass")))
        co2_mass = try_cast_float(row.get("co2_mass_tons") if row.get("co2_mass_tons") is not None else (row.get("co2mass") if row.get("co2mass") is not None else row.get("co2Mass")))

        if (is_sentinel(gross_load) or is_sentinel(heat_input) or 
            is_sentinel(so2_mass) or is_sentinel(nox_mass) or is_sentinel(co2_mass)):
            rows_changed += 1

        rec = {
            "orispl_code": orispl,
            "unit_id": unit_id,
            "date_key": date_key,
            "hour_of_day": hour_of_day,
            "gross_load_mw": gross_load,
            "heat_input_mmbtu": heat_input,
            "so2_mass_lbs": so2_mass,
            "nox_mass_lbs": nox_mass,
            "co2_mass_tons": co2_mass,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        # Deduplication check
        dedup_key = (orispl, unit_id, date_key, hour_of_day)
        if dedup_key in seen_keys:
            rows_removed += 1
            conformed[seen_keys[dedup_key]] = rec
        else:
            seen_keys[dedup_key] = len(conformed)
            conformed.append(rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_EMISSIONS_HOURLY",
        target_table="silver_emissions_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined


def conform_grid_hourly(
    raw_grid: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EIA-930 Hourly Balancing Authority Grid Telemetry:
    - Sentinel coercion on power flow and generation mix metrics.
    - Standardizes ba_code (uppercase) and ba_name (Title Case).
    - Timestamp parsing (extracts date_key YYYYMMDD and hour_of_day 0-23); invalid timestamps quarantined.
    - Deduplication on (ba_code, date_key, hour_of_day), keeping latest.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_grid)
    rows_changed = 0
    rows_removed = 0
    seen_keys = {}  # (ba_code, date_key, hour) -> index in conformed

    for row in raw_grid:
        raw_ba = row.get("ba_code", row.get("balancing_auth_code"))
        ba_code = standardize_text(raw_ba, mode="upper")
        if not ba_code:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-930",
                source_table="bronze_staging.raw_eia930_hourly_grid",
                source_row_identifier=f"UNKNOWN_BA_{row.get('timestamp_utc')}",
                rejection_reason="MISSING_BA_CODE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_ba_name = row.get("ba_name")
        ba_name = standardize_text(raw_ba_name, mode="title") or ba_code

        # Parse timestamp
        raw_ts = row.get("timestamp_utc", row.get("timestamp"))
        date_key = None
        hour_of_day = None
        if raw_ts is not None:
            try:
                dt = datetime.fromisoformat(str(raw_ts).strip().replace("Z", "+00:00"))
                date_key = int(dt.strftime("%Y%m%d"))
                hour_of_day = dt.hour
            except Exception:
                pass

        if date_key is None or hour_of_day is None:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-930",
                source_table="bronze_staging.raw_eia930_hourly_grid",
                source_row_identifier=f"{ba_code}_{raw_ts}",
                rejection_reason="INVALID_GRID_TIMESTAMP",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        demand_mw = try_cast_float(row.get("demand_mw"))
        forecast_mw = try_cast_float(row.get("demand_forecast_mw"))
        gen_coal = try_cast_float(row.get("gen_coal_mw"))
        gen_gas = try_cast_float(row.get("gen_natgas_mw", row.get("gen_gas_mw")))
        gen_nuclear = try_cast_float(row.get("gen_nuclear_mw"))
        gen_hydro = try_cast_float(row.get("gen_hydro_mw"))
        gen_wind = try_cast_float(row.get("gen_wind_mw"))
        gen_solar = try_cast_float(row.get("gen_solar_mw"))
        interchange = try_cast_float(row.get("net_interchange_mw"))

        if (ba_name != raw_ba_name or ba_code != raw_ba or
            is_sentinel(row.get("demand_mw")) or is_sentinel(row.get("demand_forecast_mw"))):
            rows_changed += 1

        rec = {
            "ba_code": ba_code,
            "ba_name": ba_name,
            "interconnect": str(row.get("interconnect", "Unknown")).strip(),
            "timestamp_utc": str(raw_ts),
            "date_key": date_key,
            "hour_of_day": hour_of_day,
            "demand_mw": demand_mw,
            "demand_forecast_mw": forecast_mw,
            "gen_coal_mw": gen_coal,
            "gen_natgas_mw": gen_gas,
            "gen_nuclear_mw": gen_nuclear,
            "gen_hydro_mw": gen_hydro,
            "gen_wind_mw": gen_wind,
            "gen_solar_mw": gen_solar,
            "net_interchange_mw": interchange,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        dedup_key = (ba_code, date_key, hour_of_day)
        if dedup_key in seen_keys:
            rows_removed += 1
            conformed[seen_keys[dedup_key]] = rec
        else:
            seen_keys[dedup_key] = len(conformed)
            conformed.append(rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_GRID_HOURLY",
        target_table="silver_grid_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined


# ==============================================================================
# 5. MASTER SILVER CONFORMANCE ORCHESTRATION
# ==============================================================================

def run_silver_conformance_suite(
    spark_session=None,
    master_batch_id: Optional[str] = None,
    raw_inputs: Optional[Dict[str, Any]] = None
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

    # 1. Ingest Bronze baseline (use supplied raw inputs or read from sample files)
    raw_weather_stations = None
    if raw_inputs:
        raw_gen = raw_inputs.get("raw_generators", [])
        raw_plants = raw_inputs.get("raw_plants", [])
        raw_gen923 = raw_inputs.get("raw_gen923_monthly", [])
        raw_weather = raw_inputs.get("raw_weather_hourly", [])
        raw_cems = raw_inputs.get("raw_cems_hourly", [])
        raw_grid = raw_inputs.get("raw_grid_hourly", [])
        raw_weather_stations = raw_inputs.get("raw_weather_stations")
    else:
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
        _, raw_cems = bronze.extract_json_records(
            "archived/scratch_api_tests/sample_data/sample_epa_hourly_emissions.json",
            batch_id=master_batch_id
        )
        _, raw_grid = bronze.extract_json_records(
            "archived/scratch_api_tests/sample_data/sample_eia930_hourly_grid.json",
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

    # 6. Conform EPA Hourly Emissions
    print("-> Conforming EPA Hourly Emissions Telemetry...")
    silver_emissions, q_emissions = conform_emissions_hourly(raw_cems, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Emissions: {len(silver_emissions)} | Quarantined: {len(q_emissions)}")

    # 7. Conform EIA-930 Grid Telemetry
    print("-> Conforming EIA-930 Hourly Grid Telemetry...")
    silver_grid, q_grid = conform_grid_hourly(raw_grid, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Grid Telemetry: {len(silver_grid)} | Quarantined: {len(q_grid)}")

    total_conformed = (len(silver_plants) + len(silver_generators) + len(silver_923) + 
                       len(silver_weather) + len(silver_emissions) + len(silver_grid))
    total_quarantined = (len(q_plants) + len(q_gen) + len(q_923) + 
                         len(q_weather) + len(q_emissions) + len(q_grid))
    total_raw_read = (len(raw_plants) + len(raw_gen) + len(raw_gen923) + 
                      len(raw_weather) + len(raw_cems) + len(raw_grid))

    # 8. Log Silver pipeline execution to etl_run_log
    bronze.log_etl_run(
        spark_session=spark_session,
        batch_id=master_batch_id,
        pipeline_step="SILVER_CONFORMANCE",
        source_system="MEDALLION_SILVER",
        records_read=total_raw_read,
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
        "conformed_emissions_count": len(silver_emissions),
        "conformed_grid_count": len(silver_grid),
        "total_conformed_records": total_conformed,
        "total_quarantined_records": total_quarantined,
        "execution_status": "SUCCESS",
        "silver_data": {
            "silver_plants": silver_plants,
            "silver_generators": silver_generators,
            "silver_monthly_generation": silver_923,
            "silver_weather_hourly": silver_weather,
            "silver_emissions_hourly": silver_emissions,
            "silver_grid_hourly": silver_grid,
            "raw_weather_stations": raw_weather_stations
        }
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

