"""
Tier 1 Local Unit Tests: Pure Python Configuration and Parsing Logic
Strict Isolation Guard: Does NOT instantiate SparkSession or require cloud credentials.
"""

import sys
import unittest
from pathlib import Path

# Add project root and 03_ETL to sys.path for local discovery
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

import config  # noqa: E402


class TestCatalogConfiguration(unittest.TestCase):
    """Verifies Unity Catalog configuration contracts in config.py."""

    def test_catalog_identity(self):
        self.assertEqual(config.CATALOG_CONFIG["CATALOG_NAME"], "dwbi_catalog")
        self.assertTrue(config.CATALOG_CONFIG["USE_UNITY_CATALOG"])

    def test_medallion_schemas_defined(self):
        schemas = config.CATALOG_CONFIG["SCHEMAS"]
        expected_schemas = {
            "BRONZE": "bronze_staging",
            "SILVER": "silver_conformed",
            "GOLD_DW": "gold_warehouse",
            "GOLD_MARTS": "gold_marts",
            "QUARANTINE": "quarantine"
        }
        for key, expected_name in expected_schemas.items():
            self.assertIn(key, schemas)
            self.assertEqual(schemas[key], expected_name)

    def test_course_schema_aliases(self):
        aliases = config.CATALOG_CONFIG["COURSE_SCHEMA_ALIASES"]
        self.assertEqual(aliases.get("project_staging"), "bronze_staging")
        self.assertEqual(aliases.get("project_dw"), "gold_warehouse")
        self.assertEqual(aliases.get("project_reporting"), "gold_marts")

    def test_raw_landing_volume_path(self):
        vol = config.CATALOG_CONFIG["VOLUMES"]["RAW_LANDING"]
        self.assertEqual(vol, "/Volumes/dwbi_catalog/bronze_staging/raw_landing")


class TestNamingAndPathHelpers(unittest.TestCase):
    """Verifies 3-tier FQN naming and volume path generators."""

    def test_get_table_fqn(self):
        fqn = config.get_table_fqn("bronze_staging", "raw_eia923_monthly_generation")
        self.assertEqual(fqn, "dwbi_catalog.bronze_staging.raw_eia923_monthly_generation")

    def test_get_table_fqn_with_schema_key(self):
        fqn = config.get_table_fqn("GOLD_DW", "fact_monthly_plant_operations")
        self.assertEqual(fqn, "dwbi_catalog.gold_warehouse.fact_monthly_plant_operations")

    def test_get_volume_path(self):
        path = config.get_volume_path("eia860/2023/generator.xlsx")
        self.assertEqual(path, "/Volumes/dwbi_catalog/bronze_staging/raw_landing/eia860/2023/generator.xlsx")


class TestDataQualityRulesAndSentinels(unittest.TestCase):
    """Verifies domain rules, heat rate boundaries, and sentinels in config.py."""

    def test_string_sentinel_list(self):
        sentinels = config.DATA_QUALITY_RULES["SENTINEL_VALUES"]
        self.assertIn(".", sentinels)
        self.assertIn("NM", sentinels)
        self.assertIn("*", sentinels)
        self.assertIn("", sentinels)
        self.assertIn(-9999, sentinels)

    def test_thermodynamic_heat_rate_bounds(self):
        heat_bounds = config.DATA_QUALITY_RULES["HEAT_RATE_BOUNDS"]
        # Combined Cycle (CCGT): 5,000 to 14,000 Btu/kWh
        self.assertEqual(heat_bounds["CCGT"]["min"], 5000)
        self.assertEqual(heat_bounds["CCGT"]["max"], 14000)
        # Coal Steam Turbine: 8,500 to 18,000 Btu/kWh
        self.assertEqual(heat_bounds["COAL_ST"]["min"], 8500)
        self.assertEqual(heat_bounds["COAL_ST"]["max"], 18000)
        # Gas Turbine Peakers: 9,000 to 22,000 Btu/kWh
        self.assertEqual(heat_bounds["PEAKER_GT"]["min"], 9000)
        self.assertEqual(heat_bounds["PEAKER_GT"]["max"], 22000)

    def test_negative_net_generation_tolerance(self):
        # Negative net generation is a valid physical event (offline station auxiliary draw)
        allow_negative = config.DATA_QUALITY_RULES["ALLOW_NEGATIVE_NET_GENERATION"]
        self.assertTrue(allow_negative, "Negative NetGen must be allowed per domain engineering rules.")

    def test_auxiliary_load_ratio_bounds(self):
        aux_bounds = config.DATA_QUALITY_RULES["AUXILIARY_LOAD_RATIO"]
        self.assertEqual(aux_bounds["GAS_PLANT"]["min_ratio"], 0.01)
        self.assertEqual(aux_bounds["GAS_PLANT"]["max_ratio"], 0.12)
        self.assertEqual(aux_bounds["COAL_PLANT"]["min_ratio"], 0.04)
        self.assertEqual(aux_bounds["COAL_PLANT"]["max_ratio"], 0.16)


class TestDynamicHeaderDiscoveryKeys(unittest.TestCase):
    """Verifies signature keys used to scan shifting Excel headers."""

    def test_eia860_header_keys(self):
        eia860_keys = config.SOURCES_CONFIG["EIA_860"]["HEADER_SCAN_KEYS"]
        self.assertIn("Plant Code", eia860_keys)
        self.assertIn("Plant Id", eia860_keys)

    def test_eia923_header_keys(self):
        eia923_keys = config.SOURCES_CONFIG["EIA_923"]["HEADER_SCAN_KEYS"]
        self.assertIn("Plant Id", eia923_keys)
        self.assertIn("Plant Code", eia923_keys)


class TestSparkSessionIsolation(unittest.TestCase):
    """Verifies that config.py executes safely in non-Spark environments."""

    def test_init_without_spark_does_not_crash(self):
        # Passing None must exit gracefully without throwing exceptions
        result = config.init_databricks_environment(spark_session=None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
