"""
Tier 1 Local Unit Tests: Gold Kimball Star Schema & Multi-Grain Facts
Strict Isolation Guard: Does NOT instantiate SparkSession or require cloud credentials.
"""

import sys
import unittest
import importlib
from pathlib import Path

# Add project root and 03_ETL to sys.path for local discovery
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

gold = importlib.import_module("03_gold_star_schema_facts")


class TestDimDateGeneration(unittest.TestCase):
    """Verifies universal calendar generation, 4-year horizon, and climate stress flags."""

    def test_total_calendar_days_and_horizon(self):
        records = gold.generate_dim_date_records(2021, 2024)
        # 365 + 365 + 365 + 366 (leap year 2024) = 1,461 days
        self.assertEqual(len(records), 1461)
        self.assertEqual(records[0]["date_key"], 20210101)
        self.assertEqual(records[-1]["date_key"], 20241231)

    def test_leap_year_february_29(self):
        records = gold.generate_dim_date_records(2021, 2024)
        leap_days = [r for r in records if r["date_key"] == 20240229]
        self.assertEqual(len(leap_days), 1)
        self.assertEqual(leap_days[0]["calendar_date"], "2024-02-29")
        self.assertEqual(leap_days[0]["day_of_month"], 29)

    def test_climate_stress_flags(self):
        records = gold.generate_dim_date_records(2021, 2024)
        rec_map = {r["date_key"]: r for r in records}

        # Winter Storm Uri (Feb 15, 2021)
        self.assertTrue(rec_map[20210215]["is_winter_freeze"])
        self.assertEqual(rec_map[20210215]["season_name"], "Winter")

        # Summer Peak Heatwave (July 20, 2023)
        self.assertTrue(rec_map[20230720]["is_summer_peak"])
        self.assertEqual(rec_map[20230720]["season_name"], "Summer")


class TestGoldDimensionWarehouse(unittest.TestCase):
    """Verifies dimension default row seeding and surrogate key lookups."""

    def setUp(self):
        self.dw = gold.GoldDimensionWarehouse()

    def test_default_surrogate_key_seeding(self):
        # Default unknown records must be present with surrogate key -1
        self.assertEqual(self.dw.dim_plant[0]["plant_key"], -1)
        self.assertEqual(self.dw.dim_plant[0]["orispl_code"], -1)

        self.assertEqual(self.dw.dim_generator[0]["generator_key"], -1)
        self.assertEqual(self.dw.dim_generator[0]["orispl_code"], -1)

        self.assertEqual(self.dw.dim_balancing_authority[0]["ba_key"], -1)
        self.assertEqual(self.dw.dim_balancing_authority[0]["ba_code"], "UNKNOWN")

        self.assertEqual(self.dw.dim_weather_station[0]["station_key"], -1)
        self.assertEqual(self.dw.dim_weather_station[0]["station_id"], "UNKNOWN")

    def test_populate_dim_plant_and_surrogate_lookup(self):
        silver_plants = [
            {"orispl_code": 3, "plant_name": "Barry", "state_code": "AL", "utility_id": 195},
            {"orispl_code": 10, "plant_name": "Gorgas", "state_code": "AL", "utility_id": 195}
        ]
        self.dw.populate_dim_plant(silver_plants)
        self.assertIn(3, self.dw.plant_lookup)
        self.assertIn(10, self.dw.plant_lookup)
        self.assertGreater(self.dw.plant_lookup[3], 0)
        self.assertGreater(self.dw.plant_lookup[10], 0)

    def test_populate_dim_generator_and_lookup(self):
        silver_gens = [
            {"orispl_code": 3, "generator_id": "1", "prime_mover_code": "ST", "operating_status": "OP", "is_current": True},
            {"orispl_code": 3, "generator_id": "2", "prime_mover_code": "ST", "operating_status": "OP", "is_current": True}
        ]
        self.dw.populate_dim_generator(silver_gens)
        self.assertIn((3, "1"), self.dw.generator_lookup)
        self.assertIn((3, "2"), self.dw.generator_lookup)
        self.assertGreater(self.dw.generator_lookup[(3, "1")], 0)


class TestMultiGrainFactBuilders(unittest.TestCase):
    """Verifies multi-grain Kimball fact table generation and Liquid Clustering attributes."""

    def setUp(self):
        self.dw = gold.GoldDimensionWarehouse()
        # Seed Plant 3 (Barry) with coordinates
        self.dw.populate_dim_plant([{
            "orispl_code": 3,
            "plant_name": "Barry",
            "state_code": "AL",
            "latitude": 31.0069,
            "longitude": -88.0103
        }])
        self.dw.populate_dim_ba([{"ba_code": "SOCO", "ba_name": "Southern Company", "interconnect": "Eastern"}])
        self.dw.populate_dim_weather_station([{
            "icao": "KMOB",
            "station_name": "Mobile Regional Airport",
            "state": "AL",
            "lat": 30.687,
            "lon": -88.242
        }])

    def test_fact_hourly_emissions_weather(self):
        raw_cems = [{
            "facilityId": 3,
            "unitId": "1",
            "date": "2023-01-01",
            "hour": 5,
            "grossLoad": "125.5",
            "heatInput": "1250.0",
            "so2Mass": "15.2",
            "noxMass": "22.4",
            "co2Mass": "110.8"
        }]
        raw_weather = [{
            "timestamp": "2023-01-01T05:00:00Z",
            "temperature": {"value": 14.5},
            "windSpeed": {"value": 4.2}
        }]
        facts = gold.build_fact_hourly_emissions_weather(raw_cems, raw_weather, self.dw)
        self.assertEqual(len(facts), 1)
        f = facts[0]
        self.assertEqual(f["date_key"], 20230101)
        self.assertEqual(f["hour_of_day"], 5)
        self.assertEqual(f["plant_key"], self.dw.plant_lookup[3])
        self.assertEqual(f["station_key"], self.dw.station_lookup["KMOB"])
        self.assertEqual(f["gross_load_mw"], 125.5)
        self.assertEqual(f["ambient_temp_celsius"], 14.5)
        self.assertEqual(f["wind_speed_mps"], 4.2)

    def test_fact_monthly_plant_operations(self):
        silver_gen = [{
            "orispl_code": 3,
            "prime_mover_code": "ST",
            "energy_source_code": "BIT",
            "net_generation_mwh": 142500.0,
            "fuel_consumed_mmbtu": 1425000.0,
            "avg_heat_rate_btu_kwh": 10000.0
        }]
        facts = gold.build_fact_monthly_plant_operations(silver_gen, self.dw)
        self.assertEqual(len(facts), 1)
        f = facts[0]
        self.assertEqual(f["month_start_date_key"], 20230101)
        self.assertEqual(f["plant_key"], self.dw.plant_lookup[3])
        self.assertEqual(f["net_generation_mwh"], 142500.0)
        self.assertEqual(f["avg_heat_rate_btu_kwh"], 10000.0)

    def test_fact_regional_grid_demand(self):
        raw_grid = [{
            "ba_code": "SOCO",
            "timestamp_utc": "2023-01-01T06:00:00Z",
            "demand_mw": "20920.0",
            "demand_forecast_mw": "21150.0",
            "gen_coal_mw": "5100.0",
            "gen_natgas_mw": "10950.0",
            "gen_nuclear_mw": "3950.0",
            "gen_hydro_mw": "1000.0",
            "gen_solar_mw": "0.0",
            "gen_wind_mw": "350.0",
            "net_interchange_mw": "430.0"
        }]
        facts = gold.build_fact_regional_grid_demand(raw_grid, self.dw)
        self.assertEqual(len(facts), 1)
        f = facts[0]
        self.assertEqual(f["date_key"], 20230101)
        self.assertEqual(f["hour_of_day"], 6)
        self.assertEqual(f["ba_key"], self.dw.ba_lookup["SOCO"])
        self.assertEqual(f["demand_mw"], 20920.0)
        self.assertEqual(f["net_gen_coal_mw"], 5100.0)


class TestMasterGoldWarehousePipelineOffline(unittest.TestCase):
    """Verifies the complete end-to-end Gold warehouse pipeline runs offline."""

    def test_run_gold_pipeline_offline(self):
        summary = gold.run_gold_warehouse_pipeline(spark_session=None)

        self.assertEqual(summary["execution_status"], "SUCCESS")
        self.assertEqual(summary["dim_date_count"], 1461)
        self.assertGreater(summary["dim_plant_count"], 1)
        self.assertGreater(summary["dim_generator_count"], 1)
        self.assertGreater(summary["dim_ba_count"], 1)
        self.assertGreater(summary["dim_station_count"], 1)
        self.assertGreater(summary["fact_hourly_emissions_count"], 0)
        self.assertGreater(summary["fact_monthly_operations_count"], 0)
        self.assertGreater(summary["fact_regional_grid_count"], 0)
        self.assertGreater(summary["total_fact_rows"], 0)


if __name__ == "__main__":
    unittest.main()

