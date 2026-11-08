"""
Tier 1 Local Unit Tests: Bronze Ingestion Logic & Shifting Header Discovery
Strict Isolation Guard: Does NOT instantiate SparkSession or require cloud credentials.
"""

import sys
import unittest
from pathlib import Path

import importlib

# Add project root and 03_ETL to sys.path for local discovery
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

bronze = importlib.import_module("01_bronze_ingestion")


class TestBatchIdGeneration(unittest.TestCase):
    """Verifies batch ID generation formatting, timestamping, and uniqueness."""

    def test_batch_id_format(self):
        batch_id = bronze.generate_batch_id("TEST_BATCH")
        self.assertTrue(batch_id.startswith("TEST_BATCH_"))
        parts = batch_id.split("_")
        # Structure: TEST, BATCH, YYYYMMDD, HHMMSS, rand_hex
        self.assertGreaterEqual(len(parts), 4)

    def test_batch_id_uniqueness(self):
        id_1 = bronze.generate_batch_id()
        id_2 = bronze.generate_batch_id()
        self.assertNotEqual(id_1, id_2)


class TestColumnNameSanitization(unittest.TestCase):
    """Verifies that raw column names are converted to safe, clean Delta Lake identifiers."""

    def test_basic_spaces_and_case(self):
        self.assertEqual(bronze.clean_column_name("Plant Code"), "plant_code")
        self.assertEqual(bronze.clean_column_name("Utility ID"), "utility_id")

    def test_newlines_and_special_characters(self):
        # Simulates EIA-923 raw newline column
        self.assertEqual(
            bronze.clean_column_name("Combined Heat And\nPower Plant"),
            "combined_heat_and_power_plant"
        )
        self.assertEqual(
            bronze.clean_column_name("Netgen\r\nJanuary"),
            "netgen_january"
        )
        self.assertEqual(
            bronze.clean_column_name("SO2 Mass (lbs)"),
            "so2_mass_lbs"
        )

    def test_empty_and_null_names(self):
        self.assertEqual(bronze.clean_column_name(""), "unnamed_column")
        self.assertEqual(bronze.clean_column_name(None), "unnamed_column")


class TestDynamicHeaderDiscovery(unittest.TestCase):
    """Verifies dynamic scanning for shifting header rows."""

    def test_header_at_row_zero(self):
        csv_data = [
            ["Plant Code", "Plant Name", "State"],
            ["3", "Barry", "AL"],
            ["10", "Gorgas", "AL"]
        ]
        row_idx, headers = bronze.find_header_row_csv(csv_data, scan_keys=["Plant Code"])
        self.assertEqual(row_idx, 0)
        self.assertEqual(headers, ["plant_code", "plant_name", "state"])

    def test_header_at_row_two_eia860_pattern(self):
        # Simulates EIA-860 with title on Row 1 (index 0), headers on Row 2 (index 1)
        csv_data = [
            ["Form EIA-860 2023 Annual Generator Report", "", ""],
            ["Utility ID", "Plant Code", "Generator ID"],
            ["195", "3", "1"]
        ]
        row_idx, headers = bronze.find_header_row_csv(csv_data, scan_keys=["Plant Code"])
        self.assertEqual(row_idx, 1)
        self.assertIn("plant_code", headers)
        self.assertIn("utility_id", headers)

    def test_header_at_row_six_eia923_pattern(self):
        # Simulates EIA-923 with metadata rows 1-5 (indices 0-4), header on row 6 (index 5)
        csv_data = [
            ["EIA-923 Monthly Generation and Fuel Report", "", "", ""],
            ["Year: 2023", "", "", ""],
            ["Confidentiality: Public", "", "", ""],
            ["", "", "", ""],
            ["Categorical Group Header", "", "", ""],
            ["Plant Id", "Combined Heat And Power Plant", "Nuclear Unit Id", "Netgen January"],
            ["3", "N", ".", "125430.2"]
        ]
        row_idx, headers = bronze.find_header_row_csv(csv_data, scan_keys=["Plant Id"])
        self.assertEqual(row_idx, 5)
        self.assertEqual(headers[0], "plant_id")
        self.assertIn("netgen_january", headers)


class TestExtractionWithLineageMetadata(unittest.TestCase):
    """Verifies file record extraction and metadata tagging."""

    def test_extract_csv_sample(self):
        sample_path = PROJECT_ROOT / "archived" / "scratch_api_tests" / "sample_data" / "sample_eia860_generator.csv"
        headers, records = bronze.extract_csv_records(str(sample_path), scan_keys=["Plant Code"])
        self.assertGreater(len(records), 0)
        self.assertIn("_batch_id", headers)
        self.assertIn("_source_file", headers)
        self.assertIn("_ingested_at", headers)

        # Inspect first record
        first_row = records[0]
        self.assertIn("_batch_id", first_row)
        self.assertEqual(first_row["_source_file"], "sample_eia860_generator.csv")
        self.assertIn("plant_code", first_row)

    def test_extract_json_sample(self):
        sample_path = PROJECT_ROOT / "archived" / "scratch_api_tests" / "sample_data" / "sample_eia930_hourly_grid.json"
        headers, records = bronze.extract_json_records(str(sample_path))
        self.assertGreater(len(records), 0)
        self.assertIn("_batch_id", headers)
        self.assertIn("_source_file", headers)
        self.assertIn("_ingested_at", headers)
        self.assertIn("ba_code", headers)
        self.assertEqual(records[0]["ba_code"], "SOCO")


class TestMasterIngestionSuiteOffline(unittest.TestCase):
    """Verifies that the entire 9-source suite runs in offline/test mode and records audit logs."""

    def test_run_all_extractors_offline(self):
        bronze.RUN_LOG_HISTORY.clear()
        summary = bronze.run_bronze_ingestion_suite(spark_session=None)

        self.assertEqual(summary["total_sources_attempted"], 9)
        self.assertEqual(summary["total_sources_successful"], 9)
        self.assertGreater(summary["total_records_ingested"], 0)

        # Verify audit history
        self.assertEqual(len(bronze.RUN_LOG_HISTORY), 9)
        for log in bronze.RUN_LOG_HISTORY:
            self.assertEqual(log["execution_status"], "SUCCESS")
            self.assertGreater(log["records_inserted"], 0)


if __name__ == "__main__":
    unittest.main()
