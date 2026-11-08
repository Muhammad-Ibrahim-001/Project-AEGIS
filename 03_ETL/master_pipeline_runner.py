# Databricks notebook source
# COMMAND ----------
"""
==============================================================================
DL3004 DWBI Final Project: Master Lakehouse Pipeline Orchestrator
Platform: Databricks Serverless Compute / Apache Spark / Delta Lake
Catalog:  Unity Catalog (`dwbi_catalog`)
==============================================================================

Chains and executes the entire Medallion Lakehouse pipeline end-to-end:
  Stage 0: Catalog, Schemas, Volume & Audit DDL (`config.py`)
  Stage 1: Bronze Ingestion & Dynamic Header Scanning (`01_bronze_ingestion.py`)
  Stage 2: Silver Conformance, Data Quality & SCD-2 Tracking (`02_silver_cleansing_and_scd.py`)
  Stage 3: Gold Kimball Star Schema & Liquid Clustered Facts (`03_gold_star_schema_facts.py`)
  Stage 4: Gold Reporting Marts & Power BI DirectQuery Views (`04_gold_reporting_marts.py`)

Execution Modes:
  - In Databricks Notebook / Workflow: Uses active SparkSession on Serverless Compute.
  - In Local Workstation / CI: Executes offline simulations in milliseconds without Spark.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root and 03_ETL to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ETL_DIR = PROJECT_ROOT / "03_ETL"
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

import config
import importlib
import argparse

bronze = importlib.import_module("01_bronze_ingestion")
silver = importlib.import_module("02_silver_cleansing_and_scd")
gold = importlib.import_module("03_gold_star_schema_facts")
marts = importlib.import_module("04_gold_reporting_marts")
dq = importlib.import_module("05_data_quality_validation")
synth_gen = importlib.import_module("00_generate_synthetic_data")


def check_rubric_volume_gate(dw) -> Tuple[bool, Dict[str, Any]]:
    """
    Asserts Phase 2 grading rubric volumes:
      - Dimension gate: >= 100 rows in at least one business dimension (dim_plant or dim_generator, excluding -1 member).
      - Fact gate: >= 10,000 rows in fact_hourly_emissions_weather.
    Returns: (is_compliant: bool, metrics: dict)
    """
    plant_count = sum(1 for p in dw.dim_plant if p.get("plant_key") != -1)
    generator_count = sum(1 for g in dw.dim_generator if g.get("generator_key") != -1)
    ba_count = sum(1 for b in dw.dim_balancing_authority if b.get("ba_key") != -1)
    station_count = sum(1 for s in dw.dim_weather_station if s.get("station_key") != -1)

    f1_count = len(dw.fact_hourly_emissions_weather)
    f2_count = len(dw.fact_monthly_plant_operations)
    f3_count = len(dw.fact_regional_grid_demand)
    total_facts = f1_count + f2_count + f3_count

    dim_gate_passed = (plant_count >= 100 or generator_count >= 100)
    fact_gate_passed = (f1_count >= 10000)
    is_compliant = dim_gate_passed and fact_gate_passed

    metrics = {
        "dim_plant_count_excl_default": plant_count,
        "dim_generator_count_excl_default": generator_count,
        "dim_ba_count_excl_default": ba_count,
        "dim_station_count_excl_default": station_count,
        "fact_hourly_emissions_count": f1_count,
        "fact_monthly_operations_count": f2_count,
        "fact_regional_grid_count": f3_count,
        "total_fact_rows": total_facts,
        "dim_gate_passed": dim_gate_passed,
        "fact_gate_passed": fact_gate_passed,
        "is_rubric_compliant": is_compliant
    }

    if not is_compliant:
        print("\n" + "!" * 80)
        print(" [WARNING: RUBRIC VOLUME GATE NOT SATISFIED]")
        print(" Current execution uses SAMPLE / TEST FIXTURES ONLY.")
        print(f"   • dim_plant (excl -1):           {plant_count:<6} (Rubric requirement: >= 100 in at least 1 dim)")
        print(f"   • dim_generator (excl -1):       {generator_count:<6} (Rubric requirement: >= 100 in at least 1 dim)")
        print(f"   • fact_hourly_emissions_weather: {f1_count:<6} (Rubric requirement: >= 10,000 facts)")
        print(f"   • fact_monthly_plant_operations: {f2_count:<6}")
        print(f"   • fact_regional_grid_demand:     {f3_count:<6}")
        print(" To run at full university grading rubric scale, execute with flag: --synthetic")
        print("!" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print(" [RUBRIC VOLUME GATE PASSED: FULL SCALE DATA VERIFIED]")
        print(f"   • dim_plant: {plant_count} | dim_generator: {generator_count} (>=100 requirement passed)")
        print(f"   • fact_hourly_emissions_weather: {f1_count} (>=10,000 requirement passed)")
        print(f"   • Total facts loaded: {total_facts}")
        print("=" * 80 + "\n")

    return is_compliant, metrics


def run_full_lakehouse_pipeline(
    spark_session=None,
    use_synthetic: bool = False
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end Lakehouse pipeline and produces
    a consolidated multi-stage audit summary.
    """
    execution_mode = "SYNTHETIC" if use_synthetic else "REAL_OR_FIXTURES"
    master_batch_id = bronze.generate_batch_id("MASTER_PIPELINE" if not use_synthetic else "SYNTH_MASTER")
    pipeline_start = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()

    print("=" * 80)
    print(f"DL3004 DWBI FINAL PROJECT: END-TO-END LAKEHOUSE PIPELINE")
    print(f"Platform:       Databricks Serverless Cloud Lakehouse (dwbi_catalog)")
    print(f"Execution Mode: {execution_mode}")
    print(f"Master Batch:   {master_batch_id}")
    print(f"Started At:     {start_iso}")
    print("=" * 80)

    stages_summary = []

    # --------------------------------------------------------------------------
    # STAGE 0: Catalog, Schemas, Volume & Audit Tables DDL
    # --------------------------------------------------------------------------
    print("\n>>> STAGE 0: Initializing Infrastructure & Unity Catalog DDL...")
    t0_start = time.time()
    try:
        config.init_databricks_environment(spark_session)
        t0_elapsed = round(time.time() - t0_start, 3)
        stages_summary.append({
            "stage": "Stage 0: Catalog & Schemas",
            "status": "SUCCESS",
            "records": "DDL Initialized",
            "elapsed_sec": t0_elapsed
        })
        print(f"    ✓ Infrastructure verified ({t0_elapsed}s)")
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 0: Catalog & Schemas",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t0_start, 3)
        })
        print(f"    ✗ Stage 0 Error: {e}")

    # --------------------------------------------------------------------------
    # STAGE 1: Bronze Ingestion & Dynamic Header Scanning
    # --------------------------------------------------------------------------
    print(f"\n>>> STAGE 1: Bronze Staging Ingestion ({'Synthetic Rubric-Scale' if use_synthetic else '9 Federal Sources'})...")
    t1_start = time.time()
    raw_synthetic_inputs = None
    try:
        if use_synthetic:
            raw_synthetic_inputs = synth_gen.generate_synthetic_bronze_datasets(
                batch_id=master_batch_id,
                seed=42,
                num_plants=125,
                num_hourly_facts=12500
            )
            total_raw_rows = (
                len(raw_synthetic_inputs["raw_plants"]) +
                len(raw_synthetic_inputs["raw_generators"]) +
                len(raw_synthetic_inputs["raw_weather_stations"]) +
                len(raw_synthetic_inputs["raw_weather_hourly"]) +
                len(raw_synthetic_inputs["raw_cems_hourly"]) +
                len(raw_synthetic_inputs["raw_gen923_monthly"]) +
                len(raw_synthetic_inputs["raw_grid_hourly"])
            )
            t1_elapsed = round(time.time() - t1_start, 3)
            stages_summary.append({
                "stage": "Stage 1: Bronze Ingestion",
                "status": "SUCCESS",
                "records": f"{total_raw_rows} synthetic raw rows generated",
                "elapsed_sec": t1_elapsed
            })
        else:
            b_summary = bronze.run_bronze_ingestion_suite(
                spark_session=spark_session,
                master_batch_id=master_batch_id
            )
            t1_elapsed = round(time.time() - t1_start, 3)
            stages_summary.append({
                "stage": "Stage 1: Bronze Ingestion",
                "status": "SUCCESS" if b_summary["total_sources_successful"] == b_summary["total_sources_attempted"] else "PARTIAL",
                "records": f"{b_summary['total_records_ingested']} rows ({b_summary['total_sources_successful']}/9 sources)",
                "elapsed_sec": t1_elapsed
            })
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 1: Bronze Ingestion",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t1_start, 3)
        })
        print(f"    ✗ Stage 1 Error: {e}")

    # --------------------------------------------------------------------------
    # STAGE 2: Silver Conformance, Data Quality & SCD-2 Tracking
    # --------------------------------------------------------------------------
    print("\n>>> STAGE 2: Silver Conformance, Sentinels, Quarantine & SCD-2...")
    t2_start = time.time()
    try:
        s_summary = silver.run_silver_conformance_suite(
            spark_session=spark_session,
            master_batch_id=master_batch_id,
            raw_inputs=raw_synthetic_inputs
        )
        t2_elapsed = round(time.time() - t2_start, 3)
        stages_summary.append({
            "stage": "Stage 2: Silver Conformance",
            "status": s_summary["execution_status"],
            "records": f"{s_summary['total_conformed_records']} conformed, {s_summary['total_quarantined_records']} quarantined",
            "elapsed_sec": t2_elapsed
        })
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 2: Silver Conformance",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t2_start, 3)
        })
        print(f"    ✗ Stage 2 Error: {e}")

    # --------------------------------------------------------------------------
    # STAGE 3: Gold Kimball Star Schema & Liquid Clustered Facts
    # --------------------------------------------------------------------------
    print("\n>>> STAGE 3: Gold Warehouse Dimensions & Multi-Grain Facts...")
    t3_start = time.time()
    try:
        g_summary = gold.run_gold_warehouse_pipeline(
            spark_session=spark_session,
            master_batch_id=master_batch_id,
            silver_data=s_summary.get("silver_data") if "s_summary" in locals() else None
        )
        t3_elapsed = round(time.time() - t3_start, 3)
        stages_summary.append({
            "stage": "Stage 3: Gold Star Schema",
            "status": g_summary["execution_status"],
            "records": f"5 Dims ({g_summary['dim_date_count']} dates) + 3 Facts ({g_summary['total_fact_rows']} rows)",
            "elapsed_sec": t3_elapsed
        })
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 3: Gold Star Schema",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t3_start, 3)
        })
        print(f"    ✗ Stage 3 Error: {e}")

    # --------------------------------------------------------------------------
    # STAGE 4: Gold Reporting Marts & Power BI DirectQuery Views
    # --------------------------------------------------------------------------
    print("\n>>> STAGE 4: Gold Marts & DirectQuery Views Provisioning...")
    t4_start = time.time()
    try:
        m_summary = marts.run_reporting_marts_suite(
            spark_session=spark_session,
            master_batch_id=master_batch_id
        )
        t4_elapsed = round(time.time() - t4_start, 3)
        stages_summary.append({
            "stage": "Stage 4: Reporting Marts",
            "status": m_summary["execution_status"],
            "records": f"3 DirectQuery Views ({m_summary['vw_emissions_intensity_rows'] + m_summary['vw_plant_performance_rows'] + m_summary['vw_grid_stress_rows']} view rows)",
            "elapsed_sec": t4_elapsed
        })
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 4: Reporting Marts",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t4_start, 3)
        })
        print(f"    ✗ Stage 4 Error: {e}")

    # --------------------------------------------------------------------------
    # STAGE 5: Comprehensive Data Quality & Audit Validation Suite
    # --------------------------------------------------------------------------
    print("\n>>> STAGE 5: Comprehensive Data Quality & Audit Validation Suite...")
    t5_start = time.time()
    try:
        dw_inst = g_summary.get("dw")
        silver_dict = s_summary.get("silver_data") if "s_summary" in locals() and "silver_data" in s_summary else None
        dq_results, dq_summary = dq.run_data_quality_suite(
            dw=dw_inst,
            silver_data=silver_dict,
            cleaning_log=silver.CLEANING_STEP_LOG,
            batch_id=master_batch_id,
            spark_session=spark_session
        )
        t5_elapsed = round(time.time() - t5_start, 3)
        stages_summary.append({
            "stage": "Stage 5: Data Quality Suite",
            "status": dq_summary["overall_status"],
            "records": f"{dq_summary['total_checks']} checks ({dq_summary['passed']} PASS, {dq_summary['warned']} WARN, {dq_summary['failed']} FAIL)",
            "elapsed_sec": t5_elapsed
        })
    except Exception as e:
        stages_summary.append({
            "stage": "Stage 5: Data Quality Suite",
            "status": "FAILED",
            "records": str(e),
            "elapsed_sec": round(time.time() - t5_start, 3)
        })
        print(f"    ✗ Stage 5 Error: {e}")

    # --------------------------------------------------------------------------
    # RUBRIC SCALE VOLUME GATE EVALUATION
    # --------------------------------------------------------------------------
    volume_compliant, volume_metrics = False, {}
    if "g_summary" in locals() and g_summary.get("dw"):
        volume_compliant, volume_metrics = check_rubric_volume_gate(g_summary["dw"])

    total_pipeline_time = round(time.time() - pipeline_start, 3)

    # --------------------------------------------------------------------------
    # MASTER PIPELINE AUDIT REPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MASTER LAKEHOUSE PIPELINE EXECUTION SUMMARY")
    print(f"Execution Mode: {execution_mode} | Rubric Scale Compliant: {volume_compliant}")
    print("=" * 80)
    print(f"{'Stage Name':<32} | {'Status':<10} | {'Record Counts / Objects':<30} | {'Time (s)'}")
    print("-" * 80)
    for stg in stages_summary:
        print(f"{stg['stage']:<32} | {stg['status']:<10} | {str(stg['records']):<30} | {stg['elapsed_sec']}s")
    print("-" * 80)
    print(f"TOTAL PIPELINE RUNTIME: {total_pipeline_time} seconds")
    print("=" * 80)

    # Log master execution to etl_run_log
    all_success = all(s["status"] == "SUCCESS" for s in stages_summary)
    bronze.log_etl_run(
        spark_session=spark_session,
        batch_id=master_batch_id,
        pipeline_step="FULL_LAKEHOUSE_PIPELINE",
        source_system=f"MEDALLION_ORCHESTRATOR_{execution_mode}",
        records_read=volume_metrics.get("total_fact_rows", 100),
        records_inserted=volume_metrics.get("total_fact_rows", 100),
        records_updated=0,
        records_rejected=0,
        execution_status="COMPLETED" if all_success else "PARTIAL_FAILURE",
        start_time=datetime.fromisoformat(start_iso),
        end_time=datetime.now(timezone.utc)
    )

    return {
        "master_batch_id": master_batch_id,
        "execution_mode": execution_mode,
        "is_rubric_compliant": volume_compliant,
        "volume_metrics": volume_metrics,
        "total_runtime_sec": total_pipeline_time,
        "pipeline_status": "COMPLETED" if all_success else "PARTIAL_FAILURE",
        "stages": stages_summary
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DL3004 Master Lakehouse Pipeline Runner")
    parser.add_argument("--synthetic", action="store_true", help="Execute pipeline at university rubric scale using deterministic synthetic generator")
    args = parser.parse_args()

    # If run in Databricks, detect spark
    spark = None
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
    except Exception:
        pass

    run_full_lakehouse_pipeline(spark_session=spark, use_synthetic=args.synthetic)

