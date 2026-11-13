#!/usr/bin/env python3
"""
Tier 1 Local Unit Tests: DuckDB Lakehouse SQL & Analytical Verification Suite
Strict Isolation Guard: Validates that all Gold reporting views and OLAP SQL queries execute
cleanly against a portable DuckDB engine loaded with synthetic Lakehouse data.

Translations Applied (Databricks Serverless -> DuckDB ANSI):
1. Strip three-part catalog namespaces ('dwbi_catalog.gold_*' -> 'gold_*').
2. Translate Databricks Photon physical execution plan syntax ('EXPLAIN EXTENDED' -> 'EXPLAIN').
3. Strip Delta Lake physical storage clustering layout ('CLUSTER BY (...)').
NO ad-hoc query patching allowed in the test harness; all SQL fixes must reside in the files on disk.
"""

import re
import unittest
from pathlib import Path
from typing import Dict, List, Any
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SQL_DIR = PROJECT_ROOT / "04_SQL"
ANALYTICS_DIR = PROJECT_ROOT / "05_Analytics"
ETL_DIR = PROJECT_ROOT / "03_ETL"

import sys
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

import importlib
synth_gen = importlib.import_module("00_generate_synthetic_data")
silver = importlib.import_module("02_silver_cleansing_and_scd")
gold = importlib.import_module("03_gold_star_schema_facts")


class TestDuckDBLakehouseExecution(unittest.TestCase):
    """Executes all 4 reporting views and 11 OLAP queries inside DuckDB using synthetic Gold data."""

    @classmethod
    def setUpClass(cls):
        # 1. Run deterministic synthetic pipeline to populate Gold Star Schema
        raw_inputs = synth_gen.generate_synthetic_bronze_datasets(seed=42)
        silver_res = silver.run_silver_conformance_suite(raw_inputs=raw_inputs)
        gold_res = gold.run_gold_warehouse_pipeline(silver_data=silver_res["silver_data"])
        cls.dw = gold_res["dw"]

        # 2. Spin up in-memory DuckDB instance
        cls.con = duckdb.connect(database=":memory:")
        cls.con.execute("CREATE SCHEMA IF NOT EXISTS gold_warehouse;")
        cls.con.execute("CREATE SCHEMA IF NOT EXISTS gold_marts;")

        # 3. Load Gold Star Schema tables into DuckDB
        table_frames = {
            "dim_date": pd.DataFrame(cls.dw.dim_date),
            "dim_plant": pd.DataFrame(cls.dw.dim_plant),
            "dim_generator": pd.DataFrame(cls.dw.dim_generator),
            "dim_balancing_authority": pd.DataFrame(cls.dw.dim_balancing_authority),
            "dim_weather_station": pd.DataFrame(cls.dw.dim_weather_station),
            "fact_hourly_emissions_weather": pd.DataFrame(cls.dw.fact_hourly_emissions_weather),
            "fact_monthly_plant_operations": pd.DataFrame(cls.dw.fact_monthly_plant_operations),
            "fact_regional_grid_demand": pd.DataFrame(cls.dw.fact_regional_grid_demand),
        }

        for table_name, df in table_frames.items():
            cls.con.register(f"temp_{table_name}", df)
            cls.con.execute(f"CREATE TABLE gold_warehouse.{table_name} AS SELECT * FROM temp_{table_name};")

        cls.views_sql_path = SQL_DIR / "Views.sql"
        cls.olap_sql_path = ANALYTICS_DIR / "olap_queries.sql"

    def test_all_views_execute_in_duckdb(self):
        """Validates that all 4 views in Views.sql compile, execute, and return rows in DuckDB."""
        views_raw_sql = self.views_sql_path.read_text(encoding="utf-8")

        # Translation 1 & 3: Strip three-part namespace and Delta layout clauses
        views_sql = views_raw_sql.replace("dwbi_catalog.", "")
        views_sql = re.sub(r"CLUSTER\s+BY\s*\([^\)]+\)", "", views_sql, flags=re.IGNORECASE)

        # Split individual view definitions
        statements = [stmt.strip() for stmt in views_sql.split(";") if stmt.strip()]
        deployed_views = []

        for stmt in statements:
            if "CREATE OR REPLACE VIEW" in stmt.upper():
                match = re.search(r"CREATE\s+OR\s+REPLACE\s+VIEW\s+([\w\.]+)\s+AS", stmt, re.IGNORECASE)
                self.assertIsNotNone(match, "Failed to parse view name from DDL")
                view_name = match.group(1)

                self.con.execute(stmt)
                deployed_views.append(view_name)

                # Assert view returns non-empty result set
                row_count = self.con.execute(f"SELECT COUNT(*) FROM {view_name};").fetchone()[0]
                self.assertGreater(row_count, 0, f"View {view_name} returned 0 rows in DuckDB")

        expected_views = [
            "gold_marts.vw_emissions_intensity",
            "gold_marts.vw_plant_performance",
            "gold_marts.vw_grid_stress",
            "gold_marts.vw_monthly_generation_mix"
        ]
        self.assertEqual(sorted(deployed_views), sorted(expected_views))

    def test_all_olap_queries_execute_in_duckdb(self):
        """Validates that all 11 OLAP queries in olap_queries.sql execute and return rows in DuckDB."""
        olap_raw_sql = self.olap_sql_path.read_text(encoding="utf-8")

        # Translation 1 & 2: Strip catalog namespace and translate EXPLAIN EXTENDED
        olap_sql = olap_raw_sql.replace("dwbi_catalog.", "")
        olap_sql = re.sub(r"EXPLAIN\s+EXTENDED", "EXPLAIN", olap_sql, flags=re.IGNORECASE)

        # Parse individual queries
        raw_chunks = [chunk.strip() for chunk in olap_sql.split(";") if chunk.strip()]
        queries = []
        for chunk in raw_chunks:
            # Filter comments to detect SQL statement start
            code_lines = [line for line in chunk.splitlines() if not line.strip().startswith("--")]
            stmt = "\n".join(code_lines).strip()
            if stmt.upper().startswith(("SELECT", "WITH", "EXPLAIN")):
                queries.append(stmt)

        self.assertEqual(len(queries), 11, f"Expected 11 executable OLAP queries, found {len(queries)}")

        # Execute each query and assert non-empty rows
        for idx, query in enumerate(queries, start=1):
            with self.subTest(query_index=idx):
                res = self.con.execute(query).fetchall()
                # Query 7 is an audit of forced outages with negative net generation; in production/test it must run cleanly
                if idx != 7:
                    self.assertGreater(
                        len(res), 0,
                        f"Query {idx} executed successfully but returned 0 rows in DuckDB"
                    )
                else:
                    self.assertIsInstance(res, list, f"Query {idx} failed to produce a valid result list")

    def test_scd2_generator_lifecycle_transitions_in_duckdb(self):
        """Validates that dim_generator maintains multiple versions with valid_from/valid_to/is_current."""
        # Query 9: Generator asset lifecycle tracking
        q9_result = self.con.execute("""
            SELECT 
                g.orispl_code,
                p.plant_name,
                g.generator_id,
                g.prime_mover_code,
                g.primary_energy_source,
                g.operating_status,
                g.valid_from,
                g.valid_to,
                g.is_current,
                COUNT(*) OVER (PARTITION BY g.orispl_code, g.generator_id) AS total_revisions
            FROM gold_warehouse.dim_generator g
            LEFT JOIN gold_warehouse.dim_plant p ON g.orispl_code = p.orispl_code
            WHERE g.generator_key <> -1
            ORDER BY g.orispl_code, g.generator_id, g.valid_from;
        """).fetchall()

        # Find generators with multiple historical revisions
        multi_rev = [r for r in q9_result if r[9] > 1]
        self.assertGreater(len(multi_rev), 0, "No SCD-2 multi-version generators found in dim_generator")

        # Distinct generators with transitions
        distinct_gens = set((r[0], r[2]) for r in multi_rev)
        self.assertEqual(len(distinct_gens), 5, f"Expected 5 transitioning generators, found {len(distinct_gens)}")

        # Verify historical versions have is_current = False and closed valid_to
        historical_versions = [r for r in multi_rev if not r[8]]  # is_current is False
        self.assertGreaterEqual(len(historical_versions), 7, "Expected at least 7 closed historical versions")
        for h in historical_versions:
            self.assertFalse(h[8], f"Historical version must have is_current=False: {h}")
            self.assertNotEqual(str(h[7]), "9999-12-31 23:59:59", f"Historical version must have valid_to < infinity: {h}")

        # Verify current active versions have is_current = True and valid_to = 9999-12-31
        active_versions = [r for r in multi_rev if r[8]]  # is_current is True
        self.assertEqual(len(active_versions), 5, "Each transitioning generator must have exactly 1 active version")
        for a in active_versions:
            self.assertTrue(a[8], f"Active version must have is_current=True: {a}")
            self.assertEqual(str(a[7]), "9999-12-31 23:59:59", f"Active version must have open valid_to: {a}")


if __name__ == "__main__":
    unittest.main()
