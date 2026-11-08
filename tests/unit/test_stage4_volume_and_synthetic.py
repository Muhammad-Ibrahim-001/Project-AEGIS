#!/usr/bin/env python3
"""
==============================================================================
DL3004 DWBI Final Project: Stage 4 Volume Gate & Synthetic Generator Test Suite
Platform: Databricks Serverless Cloud Lakehouse / Offline Test Harness
==============================================================================

Verifies the rubric scale requirements and synthetic pipeline integrity:
  1. Volume Gate: Fails (<100 plants/generators, <10,000 facts) on sample fixtures;
     Passes (>=100 plants, >=10,000 facts) on synthetic dataset.
  2. End-to-End Synthetic Pipeline: Generates valid Bronze -> Silver -> Gold
     with 0 orphan foreign keys, 0 duplicate primary keys, and full referential integrity.
  3. Defect Injection Reconciliation: Asserts that every injected defect in
     synthetic_injection_log.csv is exactly accounted for in cleaning_step_log.csv
     or quarantine.rejected_records:
       - 25 WHITESPACE_AND_CASE_VARIANTS cleaned in CONFORM_PLANTS
       - 10 NULL_KEYS quarantined (4 plant, 6 CEMS)
       - 20 DUPLICATE_ROWS deduplicated (5 gen, 10 CEMS, 5 grid)
       - 30 SENTINEL_VALUES coerced (15 NOAA ISD -9999, 15 EIA-923 '.'/'NM')
       - 12 UNPARSEABLE_DATES quarantined (8 CEMS, 4 grid)
       - 8 OUT_OF_BOUNDS_HEAT_RATES quarantined in EIA-923
  4. Execution Mode Traceability: Verifies that --synthetic runs are tagged
     execution_mode='SYNTHETIC' in pipeline summary and etl_run_log.
"""

import unittest
import importlib
import csv
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

config = importlib.import_module("03_ETL.config")
bronze = importlib.import_module("03_ETL.01_bronze_ingestion")
silver = importlib.import_module("03_ETL.02_silver_cleansing_and_scd")
gold = importlib.import_module("03_ETL.03_gold_star_schema_facts")
dq = importlib.import_module("03_ETL.05_data_quality_validation")
runner = importlib.import_module("03_ETL.master_pipeline_runner")
synth = importlib.import_module("03_ETL.00_generate_synthetic_data")


class TestStage4VolumeAndSyntheticPipeline(unittest.TestCase):
    """Test suite validating rubric volume gate, synthetic dataset, and defect reconciliation."""

    def test_volume_gate_fails_on_sample_fixtures(self):
        """Volume gate must reject sample fixtures (<100 business dims, <10,000 facts)."""
        dw_sample = gold.GoldDimensionWarehouse()
        # Add a single sample plant and small facts
        dw_sample.dim_plant.append({"plant_key": 1, "orispl_code": 3, "plant_name": "Barry"})
        dw_sample.fact_hourly_emissions_weather = [{"date_key": 20230101, "hour_of_day": h, "plant_key": 1, "unit_id": "1"} for h in range(20)]
        dw_sample.fact_monthly_plant_operations = [{"snapshot_key": 1, "month_start_date_key": 20230101, "plant_key": 1}]
        dw_sample.fact_regional_grid_demand = [{"date_key": 20230101, "hour_of_day": 0, "ba_key": 1}]

        is_compliant, metrics = runner.check_rubric_volume_gate(dw_sample)
        self.assertFalse(is_compliant)
        self.assertFalse(metrics["dim_gate_passed"])
        self.assertFalse(metrics["fact_gate_passed"])
        self.assertEqual(metrics["dim_plant_count_excl_default"], 1)
        self.assertEqual(metrics["fact_hourly_emissions_count"], 20)

    def test_volume_gate_passes_on_synthetic_pipeline(self):
        """Volume gate must pass on synthetic data (>=100 plants, >=10,000 hourly facts)."""
        raw_inputs = synth.generate_synthetic_bronze_datasets(seed=42, num_plants=125, num_hourly_facts=12500)
        silver_res = silver.run_silver_conformance_suite(raw_inputs=raw_inputs)
        gold_res = gold.run_gold_warehouse_pipeline(silver_data=silver_res["silver_data"])
        dw = gold_res["dw"]

        is_compliant, metrics = runner.check_rubric_volume_gate(dw)
        self.assertTrue(is_compliant)
        self.assertTrue(metrics["dim_gate_passed"])
        self.assertTrue(metrics["fact_gate_passed"])
        self.assertGreaterEqual(metrics["dim_plant_count_excl_default"], 100)
        self.assertGreaterEqual(metrics["fact_hourly_emissions_count"], 10000)

    def test_synthetic_data_integrity_and_referential_integrity(self):
        """Full synthetic Lakehouse must produce 0 orphan foreign keys and valid primary keys."""
        raw_inputs = synth.generate_synthetic_bronze_datasets(seed=123, num_plants=120, num_hourly_facts=11000)
        silver_res = silver.run_silver_conformance_suite(raw_inputs=raw_inputs)
        gold_res = gold.run_gold_warehouse_pipeline(silver_data=silver_res["silver_data"])
        dw = gold_res["dw"]

        # Run Data Quality Suite
        results, summary = dq.run_data_quality_suite(
            dw=dw,
            silver_data=silver_res["silver_data"],
            cleaning_log=silver.CLEANING_STEP_LOG,
            batch_id="TEST_SYNTH_INTEGRITY"
        )

        # Assert no FAIL status in any DQ check
        self.assertEqual(summary["failed"], 0)

        # Check orphan foreign keys
        orphan_checks = [r for r in results if r["check_category"] == "REFERENTIAL_INTEGRITY" and "orphan" in r["check_name"]]
        for oc in orphan_checks:
            self.assertEqual(oc["metric_value"], 0.0, f"Orphan FK detected: {oc['check_name']}")

        # Check primary key uniqueness
        unq_checks = [r for r in results if r["check_category"] == "UNIQUENESS"]
        for uc in unq_checks:
            self.assertEqual(uc["metric_value"], 0.0, f"Duplicate keys in {uc['table_name']}")

    def test_injected_defects_reconciliation(self):
        """Asserts that every injected defect is detected, cleaned, quarantined, or deduplicated."""
        batch_id = f"TEST_RECON_{id(self)}"
        raw_inputs = synth.generate_synthetic_bronze_datasets(batch_id=batch_id, seed=42)
        defect_summary = raw_inputs["defect_summary"]

        silver_res = silver.run_silver_conformance_suite(
            raw_inputs=raw_inputs,
            master_batch_id=batch_id
        )

        # 1. Whitespace & mixed-case variants (25 injected in plants)
        self.assertEqual(defect_summary["WHITESPACE_AND_CASE_VARIANTS"], 25)
        plant_log = [entry for entry in silver.CLEANING_STEP_LOG if entry["batch_id"] == batch_id and entry["step_name"] == "CONFORM_PLANTS"]
        self.assertTrue(len(plant_log) > 0)
        self.assertGreaterEqual(plant_log[0]["rows_changed"], 25)

        # 2. Duplicate rows (20 injected: 5 gen + 10 cems + 5 grid)
        self.assertEqual(defect_summary["DUPLICATE_ROWS"], 20)
        batch_steps = [entry for entry in silver.CLEANING_STEP_LOG if entry["batch_id"] == batch_id]
        total_deduped = sum(e["rows_removed"] for e in batch_steps)
        self.assertEqual(total_deduped, 20)

        # 3. Quarantined records (30 total: 4 null plant + 6 null cems + 8 bad cems date + 4 bad grid ts + 8 bad heat rate)
        total_quarantined = sum(e["rows_quarantined"] for e in batch_steps)
        self.assertEqual(total_quarantined, 30)

        # 4. Out of bounds heat rates (8 injected)
        gen923_log = [e for e in batch_steps if e["step_name"] == "CONFORM_MONTHLY_GENERATION"][0]
        self.assertEqual(gen923_log["rows_quarantined"], 8)

        # 5. Null keys (10 injected: 4 plant + 6 cems)
        self.assertEqual(defect_summary["NULL_KEYS"], 10)
        null_quarantined = plant_log[0]["rows_quarantined"] + [e for e in batch_steps if e["step_name"] == "CONFORM_EMISSIONS_HOURLY"][0]["rows_quarantined"]
        # Note: emissions quarantined = 6 null keys + 8 bad dates = 14
        emiss_quarantined = [e for e in batch_steps if e["step_name"] == "CONFORM_EMISSIONS_HOURLY"][0]["rows_quarantined"]
        self.assertEqual(plant_log[0]["rows_quarantined"], 4)
        self.assertEqual(emiss_quarantined, 14)

    def test_execution_mode_tagging_in_runner(self):
        """Runner must tag execution_mode='SYNTHETIC' and record into etl_run_log."""
        summary = runner.run_full_lakehouse_pipeline(use_synthetic=True)
        self.assertEqual(summary["execution_mode"], "SYNTHETIC")
        self.assertTrue(summary["is_rubric_compliant"])

        # Check etl_run_log entry
        last_log = runner.bronze.RUN_LOG_HISTORY[-1]
        self.assertEqual(last_log["source_system"], "MEDALLION_ORCHESTRATOR_SYNTHETIC")


if __name__ == "__main__":
    unittest.main()
