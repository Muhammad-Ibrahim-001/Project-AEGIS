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
from typing import Dict, List, Any, Optional

# Add project root and 03_ETL to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ETL_DIR = PROJECT_ROOT / "03_ETL"
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

import config
import importlib

bronze = importlib.import_module("01_bronze_ingestion")
silver = importlib.import_module("02_silver_cleansing_and_scd")
gold = importlib.import_module("03_gold_star_schema_facts")
marts = importlib.import_module("04_gold_reporting_marts")
dq = importlib.import_module("05_data_quality_validation")


def run_full_lakehouse_pipeline(spark_session=None) -> Dict[str, Any]:
    """
    Executes the entire end-to-end Lakehouse pipeline and produces
    a consolidated multi-stage audit summary.
    """
    master_batch_id = bronze.generate_batch_id("MASTER_PIPELINE")
    pipeline_start = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()

    print("=" * 80)
    print(f"DL3004 DWBI FINAL PROJECT: END-TO-END LAKEHOUSE PIPELINE")
    print(f"Platform:     Databricks Serverless Cloud Lakehouse (dwbi_catalog)")
    print(f"Master Batch: {master_batch_id}")
    print(f"Started At:   {start_iso}")
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
    print("\n>>> STAGE 1: Bronze Staging Ingestion (9 Federal Sources)...")
    t1_start = time.time()
    try:
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
            master_batch_id=master_batch_id
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
            master_batch_id=master_batch_id
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

    total_pipeline_time = round(time.time() - pipeline_start, 3)

    # --------------------------------------------------------------------------
    # MASTER PIPELINE AUDIT REPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MASTER LAKEHOUSE PIPELINE EXECUTION SUMMARY")
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
        source_system="MEDALLION_ORCHESTRATOR",
        records_read=100,
        records_inserted=100,
        records_updated=0,
        records_rejected=0,
        execution_status="COMPLETED" if all_success else "PARTIAL_FAILURE",
        start_time=datetime.fromisoformat(start_iso),
        end_time=datetime.now(timezone.utc)
    )

    return {
        "master_batch_id": master_batch_id,
        "total_runtime_sec": total_pipeline_time,
        "pipeline_status": "COMPLETED" if all_success else "PARTIAL_FAILURE",
        "stages": stages_summary
    }


if __name__ == "__main__":
    # If run in Databricks, detect spark
    spark = None
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
    except Exception:
        pass

    run_full_lakehouse_pipeline(spark_session=spark)

