"""
Tier 1 Local Unit Tests: Stage 5 Business Questions, Schema Documentation & View Verification
Strict Isolation Guard: Does NOT require active Databricks SparkSession or network.
"""

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestStage5BusinessQuestions(unittest.TestCase):
    """Verifies that Phase 1 & 2 design documents define >= 10 analytical questions,
    all required Kimball metadata fields, grain statements, hierarchies, and valid view references."""

    @classmethod
    def setUpClass(cls):
        cls.brd_path = PROJECT_ROOT / "01_Project_Documentation" / "Business_Requirements_Document.md"
        cls.req_path = PROJECT_ROOT / "01_Project_Documentation" / "Requirements.md"
        cls.views_sql_path = PROJECT_ROOT / "04_SQL" / "Views.sql"
        cls.marts_py_path = PROJECT_ROOT / "03_ETL" / "04_gold_reporting_marts.py"
        cls.olap_sql_path = PROJECT_ROOT / "05_Analytics" / "olap_queries.sql"

        with open(cls.brd_path, "r", encoding="utf-8") as f:
            cls.brd_content = f.read()

        with open(cls.views_sql_path, "r", encoding="utf-8") as f:
            cls.views_sql = f.read()

        with open(cls.marts_py_path, "r", encoding="utf-8") as f:
            cls.marts_py = f.read()

        with open(cls.olap_sql_path, "r", encoding="utf-8") as f:
            cls.olap_sql = f.read()

    def test_minimum_10_analytical_questions_in_brd(self):
        """Asserts that at least 10 business questions (BQ1 to BQ10) are formally specified."""
        bq_matches = re.findall(r"###\s+BQ(\d+):", self.brd_content)
        bq_numbers = [int(num) for num in bq_matches]
        self.assertGreaterEqual(len(bq_numbers), 10, f"Expected >= 10 BQs, found {len(bq_numbers)}")
        for expected_id in range(1, 11):
            self.assertIn(expected_id, bq_numbers, f"Missing BQ{expected_id} in BRD")

    def test_each_question_has_complete_kimball_metadata(self):
        """Asserts each BQ has: Question Statement, Business Intent, Fact Table, Dimension Tables, Measures, Grain, View/Query."""
        for bq_num in range(1, 11):
            section_match = re.search(
                rf"###\s+BQ{bq_num}:(.*?)(?=###\s+BQ\d+:|##\s+3\.|\Z)",
                self.brd_content,
                re.DOTALL
            )
            self.assertIsNotNone(section_match, f"Could not find section for BQ{bq_num}")
            section = section_match.group(1)

            self.assertIn("Question Statement:", section, f"BQ{bq_num} missing Question Statement")
            self.assertIn("Business Intent:", section, f"BQ{bq_num} missing Business Intent")
            self.assertTrue(
                "Fact Table" in section or "Dimension Table" in section,
                f"BQ{bq_num} missing Fact/Dimension Table"
            )
            self.assertIn("Measures:", section, f"BQ{bq_num} missing Measures")
            self.assertIn("Grain:", section, f"BQ{bq_num} missing Grain")
            self.assertIn("Matching Reporting View / Query:", section, f"BQ{bq_num} missing Matching View/Query")

    def test_specific_required_topics_covered(self):
        """Asserts coverage of the 3 specific topics required by the Stage 5 spec:
        - Extreme weather events vs regional grid dispatch / reserve deficits (BQ8)
        - Peak grid demand vs thermal dispatch by balancing authority (BQ9)
        - Multi-year generation trends and decarbonization by prime mover (BQ10)
        """
        self.assertIn("BQ8: Extreme Climatic Stress vs. Regional Grid Dispatch & Reserve Deficits", self.brd_content)
        self.assertIn("BQ9: Peak Grid Demand vs. Thermal Dispatch by Balancing Authority", self.brd_content)
        self.assertIn("BQ10: Multi-Year Generation Trends & Decarbonization by Prime Mover", self.brd_content)

    def test_all_referenced_views_exist_in_sql_and_python(self):
        """Asserts that all reporting views referenced across the documentation exist in Views.sql and 04_gold_reporting_marts.py."""
        expected_views = [
            "vw_emissions_intensity",
            "vw_plant_performance",
            "vw_grid_stress",
            "vw_monthly_generation_mix"
        ]

        for v in expected_views:
            # Check Views.sql
            self.assertIn(f"CREATE OR REPLACE VIEW gold_marts.{v}", self.views_sql, f"Missing {v} in Views.sql")
            # Check 04_gold_reporting_marts.py DDL
            self.assertIn(f"gold_marts.{v}", self.marts_py, f"Missing {v} in 04_gold_reporting_marts.py")
            # Check 04_gold_reporting_marts.py offline Python engine
            self.assertIn(f"def execute_{v}", self.marts_py, f"Missing execute_{v} in 04_gold_reporting_marts.py")

    def test_no_dangling_obsolete_view_references(self):
        """Asserts that obsolete broken view 'vw_monthly_generation' is nowhere in current docs or code."""
        doc_files = [
            self.brd_path,
            self.req_path,
            PROJECT_ROOT / "01_Project_Documentation" / "Project_Proposal.md",
            PROJECT_ROOT / "01_Project_Documentation" / "schema_diagram_mermaid.md",
            PROJECT_ROOT / "archived" / "Phase_1_Submission" / "Phase_1_Project_Proposal_and_Design_Document.md",
            PROJECT_ROOT / "archived" / "Phase_1_Submission" / "Phase_1_Architecture_and_Schema_Specification.md",
            PROJECT_ROOT / "archived" / "Phase_1_Submission" / "Phase_1_Data_Dictionary.md",
        ]

        pattern = re.compile(r"\bvw_monthly_generation\b")
        for path in doc_files:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                matches = pattern.findall(content)
                self.assertEqual(len(matches), 0, f"Found dangling 'vw_monthly_generation' in {path.name}")

    def test_olap_queries_sql_covers_all_questions(self):
        """Asserts olap_queries.sql contains 11 queries and explicitly maps to all 10 BQs."""
        for q_id in range(1, 12):
            self.assertIn(f"-- {q_id}.", self.olap_sql, f"Missing Query {q_id} in olap_queries.sql")

        for bq_num in range(1, 11):
            self.assertIn(f"BQ{bq_num}", self.olap_sql, f"Missing BQ{bq_num} reference in olap_queries.sql comments")

    def test_fact_grains_and_dimension_hierarchies_documented(self):
        """Asserts fact grains and dimension hierarchies for all 5 dimensions are explicitly defined."""
        # Grains
        self.assertIn("`fact_hourly_emissions_weather` Grain Statement:", self.brd_content)
        self.assertIn("`fact_monthly_plant_operations` Grain Statement:", self.brd_content)
        self.assertIn("`fact_regional_grid_demand` Grain Statement:", self.brd_content)

        # Hierarchies
        self.assertIn("Date Dimension Hierarchy", self.brd_content)
        self.assertIn("Geographic & Plant Hierarchy", self.brd_content)
        self.assertIn("Generator Asset & Technology Hierarchy", self.brd_content)
        self.assertIn("Balancing Authority Grid Hierarchy", self.brd_content)
        self.assertIn("Surface Weather Station Hierarchy", self.brd_content)


if __name__ == "__main__":
    unittest.main()
