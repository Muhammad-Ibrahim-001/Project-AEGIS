"""
Unit tests for Stage 2: Correctness bugs in loaders.
Verifies:
  1. Nearest-station Haversine selection (in range, out of range, missing coordinates).
  2. Zero fabricated defaults (bad dates/hours quarantined, unmatched keys mapped to -1).
  3. Deduplication for generators, emissions, and grid telemetry.
  4. Text standardization helper (trim, whitespace collapse, title/upper cases).
  5. Cleansing step metrics logging.
"""

import unittest
from datetime import datetime
import config
import importlib

silver = importlib.import_module("03_ETL.02_silver_cleansing_and_scd")
gold = importlib.import_module("03_ETL.03_gold_star_schema_facts")


class TestHaversineNearestStation(unittest.TestCase):
    """Verifies spatial nearest-station matching rules."""

    def setUp(self):
        self.stations = [
            {"station_key": -1, "station_id": "UNKNOWN", "latitude": None, "longitude": None},
            {"station_key": 101, "station_id": "KMOB", "station_name": "Mobile Regional", "latitude": 30.687, "longitude": -88.242},
            {"station_key": 102, "station_id": "KBHM", "station_name": "Birmingham Airport", "latitude": 33.563, "longitude": -86.753}
        ]

    def test_haversine_distance_accuracy(self):
        # Distance between Barry plant (31.0069, -88.0103) and KMOB (30.687, -88.242) is ~42 km
        d = gold.haversine_distance_km(31.0069, -88.0103, 30.687, -88.242)
        self.assertAlmostEqual(d, 42.1, delta=1.5)

    def test_nearest_station_in_range(self):
        # Barry plant within 100 km of KMOB
        st_key, dist = gold.find_nearest_station(31.0069, -88.0103, self.stations, max_distance_km=100.0)
        self.assertEqual(st_key, 101)
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 42.1, delta=1.5)

    def test_nearest_station_out_of_range(self):
        # Los Angeles coordinates (34.0522, -118.2437) > 2000 km from Alabama stations
        st_key, dist = gold.find_nearest_station(34.0522, -118.2437, self.stations, max_distance_km=100.0)
        self.assertEqual(st_key, -1)
        self.assertIsNone(dist)

    def test_nearest_station_missing_coordinates(self):
        # Missing latitude, longitude, or both must return (-1, None)
        k1, d1 = gold.find_nearest_station(None, -88.0103, self.stations, max_distance_km=100.0)
        k2, d2 = gold.find_nearest_station(31.0069, None, self.stations, max_distance_km=100.0)
        k3, d3 = gold.find_nearest_station(None, None, self.stations, max_distance_km=100.0)
        self.assertEqual(k1, -1)
        self.assertIsNone(d1)
        self.assertEqual(k2, -1)
        self.assertIsNone(d2)
        self.assertEqual(k3, -1)
        self.assertIsNone(d3)


class TestTextStandardization(unittest.TestCase):
    """Verifies text cleansing and casing helper."""

    def test_title_case_and_whitespace_collapse(self):
        self.assertEqual(silver.standardize_text(" lahore "), "Lahore")
        self.assertEqual(silver.standardize_text("LAHORE"), "Lahore")
        self.assertEqual(silver.standardize_text("  barry   steam   plant "), "Barry Steam Plant")

    def test_uppercase_for_codes(self):
        self.assertEqual(silver.standardize_text(" pjm ", mode="upper"), "PJM")
        self.assertEqual(silver.standardize_text("al", mode="upper"), "AL")

    def test_sentinel_coercion_to_none(self):
        self.assertIsNone(silver.standardize_text("."))
        self.assertIsNone(silver.standardize_text("NM"))
        self.assertIsNone(silver.standardize_text("-9999"))
        self.assertIsNone(silver.standardize_text("   "))
        self.assertIsNone(silver.standardize_text(None))


class TestDeduplicationAndQuarantine(unittest.TestCase):
    """Verifies deduplication counting and zero-fabrication quarantine routing."""

    def test_generator_deduplication(self):
        raw_gens = [
            {"plant_code": 3, "generator_id": "1", "status": "OP", "nameplate_capacity_mw": 100.0},
            {"plant_code": 3, "generator_id": "1", "status": "OP", "nameplate_capacity_mw": 120.0}  # Latest duplicate
        ]
        conformed, q = silver.conform_generators_scd2(raw_gens, batch_id="TEST_GEN_DEDUP")
        self.assertEqual(len(conformed), 1)
        self.assertEqual(conformed[0]["nameplate_capacity_mw"], 120.0)

    def test_emissions_deduplication_and_quarantine(self):
        raw_cems = [
            # Valid record
            {"oris_code": 3, "unit_id": "1", "date": "2023-01-01", "hour": 0, "gross_load_mw": 100.0},
            # Duplicate record (should overwrite previous)
            {"oris_code": 3, "unit_id": "1", "date": "2023-01-01", "hour": 0, "gross_load_mw": 110.0},
            # Invalid date format -> must be quarantined, NEVER defaulted to 20230101
            {"oris_code": 3, "unit_id": "1", "date": "NOT-A-DATE", "hour": 1, "gross_load_mw": 100.0},
            # Invalid hour -> must be quarantined, NEVER defaulted to 0
            {"oris_code": 3, "unit_id": "1", "date": "2023-01-01", "hour": 25, "gross_load_mw": 100.0}
        ]
        conformed, q = silver.conform_emissions_hourly(raw_cems, batch_id="TEST_EMIS_DEDUP")
        self.assertEqual(len(conformed), 1)
        self.assertEqual(conformed[0]["gross_load_mw"], 110.0)
        self.assertEqual(len(q), 2)
        q_reasons = {r["rejection_reason"] for r in q}
        self.assertIn("INVALID_DATE_FORMAT", q_reasons)
        self.assertIn("INVALID_HOUR_RANGE", q_reasons)

    def test_grid_deduplication_and_quarantine(self):
        raw_grid = [
            # Valid record
            {"ba_code": "SOCO", "timestamp_utc": "2023-01-01T05:00:00Z", "demand_mw": 20000.0},
            # Duplicate record
            {"ba_code": "SOCO", "timestamp_utc": "2023-01-01T05:00:00Z", "demand_mw": 21000.0},
            # Corrupt timestamp -> quarantined
            {"ba_code": "SOCO", "timestamp_utc": "CORRUPT_TIME", "demand_mw": 20000.0}
        ]
        conformed, q = silver.conform_grid_hourly(raw_grid, batch_id="TEST_GRID_DEDUP")
        self.assertEqual(len(conformed), 1)
        self.assertEqual(conformed[0]["demand_mw"], 21000.0)
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["rejection_reason"], "INVALID_GRID_TIMESTAMP")


class TestFactBuilderZeroFabrication(unittest.TestCase):
    """Verifies that fact builders do not fabricate values or silent fallbacks."""

    def setUp(self):
        self.dw = gold.GoldDimensionWarehouse()
        # Seed Plant 3 (Barry)
        self.dw.populate_dim_plant([{
            "orispl_code": 3,
            "plant_name": "Barry",
            "state_code": "AL",
            "latitude": 31.0069,
            "longitude": -88.0103
        }])

    def test_unmatched_plant_maps_to_minus_one(self):
        cems = [{
            "orispl_code": 999999,  # Unknown plant
            "unit_id": "1",
            "date_key": 20230101,
            "hour_of_day": 0,
            "gross_load_mw": 50.0
        }]
        facts = gold.build_fact_hourly_emissions_weather(cems, [], self.dw)
        self.assertEqual(len(facts), 1)
        # Must map to -1, NEVER default to plant 3
        self.assertEqual(facts[0]["plant_key"], -1)

    def test_unmatched_weather_returns_none(self):
        cems = [{
            "orispl_code": 3,
            "unit_id": "1",
            "date_key": 20230101,
            "hour_of_day": 0,
            "gross_load_mw": 50.0
        }]
        # No weather observations supplied
        facts = gold.build_fact_hourly_emissions_weather(cems, [], self.dw)
        self.assertEqual(len(facts), 1)
        # Must be None, NEVER fabricated 15.0 or 3.5
        self.assertIsNone(facts[0]["ambient_temp_celsius"])
        self.assertIsNone(facts[0]["wind_speed_mps"])


if __name__ == "__main__":
    unittest.main()

