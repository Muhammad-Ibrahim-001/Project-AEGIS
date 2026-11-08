"""
Tier 1 Local Unit Tests: Silver Conformance, Data Quality & SCD-2 Tracking
Strict Isolation Guard: Does NOT instantiate SparkSession or require cloud credentials.
"""

import sys
import unittest
import importlib
from pathlib import Path

# Add project root and 03_ETL to sys.path for local discovery
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

silver = importlib.import_module("02_silver_cleansing_and_scd")


class TestSentinelCoercion(unittest.TestCase):
    """Verifies federal sentinel coercion and ANSI TRY_CAST simulation."""

    def test_string_sentinels_coerced_to_none(self):
        self.assertIsNone(silver.coerce_sentinel("."))
        self.assertIsNone(silver.coerce_sentinel("NM"))
        self.assertIsNone(silver.coerce_sentinel("*"))
        self.assertIsNone(silver.coerce_sentinel(""))
        self.assertIsNone(silver.coerce_sentinel("   "))
        self.assertIsNone(silver.coerce_sentinel("-9999"))
        self.assertIsNone(silver.coerce_sentinel(-9999))

    def test_clean_values_preserved(self):
        self.assertEqual(silver.coerce_sentinel("Barry"), "Barry")
        self.assertEqual(silver.coerce_sentinel("AL"), "AL")
        self.assertEqual(silver.coerce_sentinel(1250.5), 1250.5)

    def test_try_cast_float(self):
        self.assertEqual(silver.try_cast_float("125430.2"), 125430.2)
        self.assertEqual(silver.try_cast_float("1,250.5"), 1250.5)
        self.assertIsNone(silver.try_cast_float("."))
        self.assertIsNone(silver.try_cast_float("NM"))
        self.assertIsNone(silver.try_cast_float("-9999"))
        self.assertIsNone(silver.try_cast_float("corrupt_string"))

    def test_try_cast_int(self):
        self.assertEqual(silver.try_cast_int("3"), 3)
        self.assertEqual(silver.try_cast_int("003"), 3)
        self.assertIsNone(silver.try_cast_int("."))
        self.assertIsNone(silver.try_cast_int("-9999"))


class TestThermodynamicHeatRateValidation(unittest.TestCase):
    """Verifies heat rate physical boundary checks and maintenance outage tolerance."""

    def test_valid_ccgt_heat_rate(self):
        # 7,000 MMBtu fuel, 1,000 MWh netgen -> 7,000 Btu/kWh (within CCGT 5,000 - 14,000)
        hr, is_valid, code = silver.calculate_and_validate_heat_rate(7000.0, 1000.0, "CC")
        self.assertTrue(is_valid)
        self.assertEqual(hr, 7000.0)
        self.assertEqual(code, "PHYSICALLY_VALID")

    def test_out_of_bounds_heat_rate_flagged(self):
        # 1,000 MMBtu fuel, 1,000 MWh netgen -> 1,000 Btu/kWh (violates 2nd law of thermodynamics, below 5,000)
        hr, is_valid, code = silver.calculate_and_validate_heat_rate(1000.0, 1000.0, "CC")
        self.assertFalse(is_valid)
        self.assertTrue("HEAT_RATE_OUT_OF_BOUNDS" in code)

    def test_negative_net_generation_maintenance_draw_allowed(self):
        # In EIA-923, negative NetGen represents offline plant drawing auxiliary station power
        hr, is_valid, code = silver.calculate_and_validate_heat_rate(50.0, -125.5, "ST")
        self.assertTrue(is_valid, "Negative net generation must NOT be rejected as a physical violation.")
        self.assertEqual(code, "STATION_SERVICE_EXCEEDS_OUTPUT")
        self.assertIsNone(hr)


class TestGeneratorSCDType2Lifecycle(unittest.TestCase):
    """Verifies SCD Type 2 state tracking for generator operational status evolution."""

    def test_initial_generator_seeding(self):
        raw_gens = [{
            "plant_code": "3",
            "generator_id": "1",
            "prime_mover": "ST",
            "status": "OP",
            "nameplate_capacity_mw": "153.0"
        }]
        conformed, q = silver.conform_generators_scd2(raw_gens, batch_id="BATCH_01", effective_timestamp="2021-01-01 00:00:00")
        self.assertEqual(len(q), 0)
        self.assertEqual(len(conformed), 1)
        rec = conformed[0]
        self.assertEqual(rec["orispl_code"], 3)
        self.assertEqual(rec["generator_id"], "1")
        self.assertEqual(rec["operating_status"], "OP")
        self.assertEqual(rec["valid_from"], "2021-01-01 00:00:00")
        self.assertEqual(rec["valid_to"], "9999-12-31 23:59:59")
        self.assertTrue(rec["is_current"])

    def test_scd2_status_transition_op_to_retired(self):
        initial_dim = [{
            "orispl_code": 3,
            "generator_id": "1",
            "prime_mover_code": "ST",
            "operating_status": "OP",
            "nameplate_capacity_mw": 153.0,
            "valid_from": "2021-01-01 00:00:00",
            "valid_to": "9999-12-31 23:59:59",
            "is_current": True
        }]
        # New incoming record reports generator has retired
        updated_raw = [{
            "plant_code": "3",
            "generator_id": "1",
            "prime_mover": "ST",
            "status": "RE",
            "nameplate_capacity_mw": "153.0"
        }]
        conformed, q = silver.conform_generators_scd2(
            raw_generators=updated_raw,
            batch_id="BATCH_02",
            existing_dim_records=initial_dim,
            effective_timestamp="2023-06-01 00:00:00"
        )
        self.assertEqual(len(conformed), 2)
        # Prior version closed
        closed = [r for r in conformed if not r["is_current"]][0]
        self.assertEqual(closed["operating_status"], "OP")
        self.assertEqual(closed["valid_to"], "2023-06-01 00:00:00")
        self.assertFalse(closed["is_current"])

        # Active version opened
        active = [r for r in conformed if r["is_current"]][0]
        self.assertEqual(active["operating_status"], "RE")
        self.assertEqual(active["valid_from"], "2023-06-01 00:00:00")
        self.assertEqual(active["valid_to"], "9999-12-31 23:59:59")
        self.assertTrue(active["is_current"])


class TestMasterSilverConformanceSuiteOffline(unittest.TestCase):
    """Verifies the complete end-to-end Silver conformance suite runs offline."""

    def test_run_silver_conformance_offline(self):
        silver.QUARANTINE_HISTORY.clear()
        summary = silver.run_silver_conformance_suite(spark_session=None)

        self.assertEqual(summary["execution_status"], "SUCCESS")
        self.assertGreater(summary["conformed_plants_count"], 0)
        self.assertGreater(summary["conformed_generators_count"], 0)
        self.assertGreater(summary["conformed_monthly_gen_count"], 0)
        self.assertGreater(summary["conformed_weather_count"], 0)
        self.assertGreater(summary["total_conformed_records"], 0)


if __name__ == "__main__":
    unittest.main()

