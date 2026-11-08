"""
Tier 1 Local Unit Tests: Gold Reporting Marts & Analytical Views
Strict Isolation Guard: Does NOT instantiate SparkSession or require cloud credentials.
"""

import sys
import unittest
import importlib
from pathlib import Path

# Add project root and 03_ETL to sys.path for local discovery
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

marts = importlib.import_module("04_gold_reporting_marts")
gold = importlib.import_module("03_gold_star_schema_facts")


class TestGoldReportingMarts(unittest.TestCase):
    """Verifies analytical views simulation, metric formulas, and status alerts."""

    def setUp(self):
        self.dw = gold.GoldDimensionWarehouse()
        self.dw.populate_dim_plant([{"orispl_code": 3, "plant_name": "Barry", "state_code": "AL"}])
        self.dw.populate_dim_ba([{"ba_code": "SOCO", "ba_name": "Southern Company", "region": "Eastern"}])

    def test_vw_emissions_intensity_metrics(self):
        fact_hourly = [{
            "date_key": 20230101,
            "hour_of_day": 5,
            "plant_key": self.dw.plant_lookup[3],
            "gross_load_mw": 200.0,
            "co2_mass_tons": 160.0,
            "so2_mass_lbs": 25.0,
            "nox_mass_lbs": 30.0,
            "ambient_temp_celsius": 12.5
        }]
        view_rows = marts.execute_vw_emissions_intensity(fact_hourly, self.dw)
        self.assertEqual(len(view_rows), 1)
        r = view_rows[0]
        self.assertEqual(r["plant_name"], "Barry")
        self.assertEqual(r["total_gross_mw"], 200.0)
        self.assertEqual(r["total_co2_tons"], 160.0)
        # 160.0 tons / 200.0 MW = 0.8 tons/MW
        self.assertEqual(r["co2_intensity_tons_per_mw"], 0.8)
        self.assertEqual(r["avg_ambient_temp_celsius"], 12.5)

    def test_vw_plant_performance_efficiency_flags(self):
        fact_monthly = [
            # High efficiency baseload (< 7,000 Btu/kWh)
            {
                "month_start_date_key": 20230101,
                "plant_key": self.dw.plant_lookup[3],
                "prime_mover_code": "CC",
                "energy_source_code": "NG",
                "net_generation_mwh": 100000.0,
                "fuel_consumed_mmbtu": 650000.0,
                "avg_heat_rate_btu_kwh": 6500.0
            },
            # Maintenance outage auxiliary load (NetGen < 0)
            {
                "month_start_date_key": 20230101,
                "plant_key": self.dw.plant_lookup[3],
                "prime_mover_code": "ST",
                "energy_source_code": "BIT",
                "net_generation_mwh": -150.0,
                "fuel_consumed_mmbtu": 50.0,
                "avg_heat_rate_btu_kwh": None
            }
        ]
        view_rows = marts.execute_vw_plant_performance(fact_monthly, self.dw)
        self.assertEqual(len(view_rows), 2)
        status_map = {r["prime_mover_code"]: r["operational_efficiency_status"] for r in view_rows}
        self.assertEqual(status_map["CC"], "HIGH_EFFICIENCY_BASELOAD")
        self.assertEqual(status_map["ST"], "STATION_OUTAGE_AUXILIARY_LOAD")

    def test_vw_grid_stress_renewable_penetration_and_alerts(self):
        fact_grid = [{
            "date_key": 20230101,
            "hour_of_day": 12,
            "ba_key": self.dw.ba_lookup["SOCO"],
            "demand_mw": 25000.0,
            "demand_forecast_mw": 23500.0,  # 1500 MW underforecast (> 1000 MW stress alert)
            "net_gen_coal_mw": 5000.0,
            "net_gen_gas_mw": 10000.0,
            "net_gen_nuclear_mw": 4000.0,
            "net_gen_hydro_mw": 1000.0,
            "net_gen_wind_mw": 3000.0,
            "net_gen_solar_mw": 2000.0,
            "net_interchange_mw": 0.0
        }]
        view_rows = marts.execute_vw_grid_stress(fact_grid, self.dw)
        self.assertEqual(len(view_rows), 1)
        r = view_rows[0]
        self.assertEqual(r["demand_forecast_error_mw"], 1500.0)
        # Total gen = 25,000 MW; Renewables = 5,000 MW (20.0%)
        self.assertEqual(r["total_generation_mw"], 25000.0)
        self.assertEqual(r["total_renewable_generation_mw"], 5000.0)
        self.assertEqual(r["renewable_penetration_pct"], 20.0)
        self.assertEqual(r["grid_stress_alert_level"], "SEVERE_UNDERFORECAST_STRESS")

    def test_run_reporting_marts_suite_offline(self):
        summary = marts.run_reporting_marts_suite(spark_session=None)
        self.assertEqual(summary["execution_status"], "SUCCESS")
        self.assertEqual(len(summary["views_deployed"]), 3)
        self.assertGreater(summary["vw_emissions_intensity_rows"], 0)
        self.assertGreater(summary["vw_plant_performance_rows"], 0)
        self.assertGreater(summary["vw_grid_stress_rows"], 0)


if __name__ == "__main__":
    unittest.main()

