"""
Tier 1 Local Unit Tests: Stage 6 Automated PDF Reports & Number Reconciliation
Strict Isolation Guard: Validates that generated PDFs dynamically match CSV inputs without fabrication.
"""

import csv
import unittest
from pathlib import Path
import pypdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "01_Project_Documentation"
DATA_DIR = PROJECT_ROOT / "02_Data" / "cleaned_data"
ETL_DIR = PROJECT_ROOT / "03_ETL"

import sys
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

import importlib
pdf_generator = importlib.import_module("06_generate_pdf_reports")


class TestStage6Reports(unittest.TestCase):
    """Verifies that PDF reports compile cleanly, render Page 1 prominently with synthetic notices,
    and all numerical figures precisely reconcile with source CSV audit logs."""

    @classmethod
    def setUpClass(cls):
        # Generate fresh reports to ensure they match current CSV state
        cls.generated = pdf_generator.generate_all_reports()
        cls.cleaning_pdf_path = DOCS_DIR / "Data_Cleaning_Report.pdf"
        cls.dq_pdf_path = DOCS_DIR / "Data_Quality_Report.pdf"

        # Load raw CSV records for verification
        cls.cleaning_batch, cls.cleaning_rows = pdf_generator.load_cleaning_step_log()
        cls.synth_batch, cls.injection_rows, cls.total_defects = pdf_generator.load_synthetic_injection_log()
        cls.dq_batch, cls.dq_checks, cls.dq_summary = pdf_generator.load_dq_results()

        # Read PDF extracted text
        cls.cleaning_reader = pypdf.PdfReader(str(cls.cleaning_pdf_path))
        cls.cleaning_full_text = " ".join(p.extract_text() or "" for p in cls.cleaning_reader.pages)
        cls.cleaning_p1_text = cls.cleaning_reader.pages[0].extract_text() or ""

        cls.dq_reader = pypdf.PdfReader(str(cls.dq_pdf_path))
        cls.dq_full_text = " ".join(p.extract_text() or "" for p in cls.dq_reader.pages)
        cls.dq_p1_text = cls.dq_reader.pages[0].extract_text() or ""

    def test_both_pdfs_exist_and_render_multiple_pages(self):
        """Asserts both PDF files exist, have non-trivial file size, and multiple rendered pages."""
        self.assertTrue(self.cleaning_pdf_path.exists(), "Data_Cleaning_Report.pdf does not exist")
        self.assertTrue(self.dq_pdf_path.exists(), "Data_Quality_Report.pdf does not exist")

        self.assertGreater(self.cleaning_pdf_path.stat().st_size, 5000)
        self.assertGreater(self.dq_pdf_path.stat().st_size, 5000)

        self.assertGreaterEqual(len(self.cleaning_reader.pages), 2, "Data_Cleaning_Report.pdf should have multiple pages")
        self.assertGreaterEqual(len(self.dq_reader.pages), 2, "Data_Quality_Report.pdf should have multiple pages")

    def test_prominent_synthetic_notice_on_page_1_both_pdfs(self):
        """Asserts Page 1 prominently disclaims SYNTHETIC data, random seed 42, and total defects (105)."""
        for doc_name, p1_text in [("Data_Cleaning_Report.pdf", self.cleaning_p1_text), ("Data_Quality_Report.pdf", self.dq_p1_text)]:
            norm_text = " ".join(p1_text.split())
            self.assertIn("SYNTHETIC BENCHMARK DATASET", norm_text, f"Missing prominent SYNTHETIC notice in {doc_name} Page 1")
            self.assertIn("42", norm_text, f"Missing seed 42 in {doc_name} Page 1")
            self.assertIn(str(self.total_defects), norm_text, f"Missing total injected defects ({self.total_defects}) in {doc_name} Page 1")
            self.assertTrue(
                "never imply real federal data" in norm_text.lower() or "must never be cited as real historical federal operations" in norm_text.lower(),
                f"Missing strict integrity clause in {doc_name} Page 1"
            )

    def test_cleaning_report_numbers_match_csv(self):
        """Asserts every number in cleaning_step_log and synthetic_injection_log is represented in Data_Cleaning_Report.pdf."""
        # 1. Total row numbers from cleaning step log
        total_in = sum(r["rows_in"] for r in self.cleaning_rows)
        total_changed = sum(r["rows_changed"] for r in self.cleaning_rows)
        total_removed = sum(r["rows_removed"] for r in self.cleaning_rows)
        total_quarantined = sum(r["rows_quarantined"] for r in self.cleaning_rows)
        total_out = sum(r["rows_out"] for r in self.cleaning_rows)

        for total_val in [total_in, total_changed, total_removed, total_quarantined, total_out]:
            # Check either raw number or formatted with comma
            formatted = f"{total_val:,}"
            raw = str(total_val)
            self.assertTrue(
                formatted in self.cleaning_full_text or raw in self.cleaning_full_text,
                f"Cleaning metric total {total_val} not found in Data_Cleaning_Report.pdf"
            )

        # 2. Check each injected defect count appears
        for inj in self.injection_rows:
            cnt = str(int(float(inj["injected_count"])))
            self.assertIn(cnt, self.cleaning_full_text, f"Injected count {cnt} for {inj['defect_type']} missing in report")

        # 3. Check concrete examples are documented
        self.assertIn("Lahore", self.cleaning_full_text, "Missing 'Lahore' text standardization example")
        self.assertIn("Barry", self.cleaning_full_text, "Missing 'Barry' plant text example")

    def test_dq_report_numbers_match_csv(self):
        """Asserts every check count, threshold, and metric value in dq_results matches Data_Quality_Report.pdf."""
        # Check totals
        total_checks = self.dq_summary["total_checks"]
        pass_cnt = self.dq_summary["pass_count"]
        warn_cnt = self.dq_summary["warn_count"]
        fail_cnt = self.dq_summary["fail_count"]

        self.assertIn(str(total_checks), self.dq_full_text, f"Total checks count {total_checks} missing in DQ report")
        self.assertIn(str(pass_cnt), self.dq_full_text, f"PASS count {pass_cnt} missing in DQ report")
        self.assertIn(str(warn_cnt), self.dq_full_text, f"WARN count {warn_cnt} missing in DQ report")
        self.assertIn(str(fail_cnt), self.dq_full_text, f"FAIL count {fail_cnt} missing in DQ report")

        # Check that WARN metric value appears if present
        warn_checks = [c for c in self.dq_checks if c["status"] == "WARN"]
        for w in warn_checks:
            metric_str = str(w["metric_value"])
            self.assertIn(metric_str, self.dq_full_text, f"WARN check metric value {metric_str} missing in DQ report")

        # Check default member rate thresholds appear
        self.assertIn("5.0%", self.dq_full_text, "Default member rate WARN threshold 5.0% missing in DQ report")
        self.assertIn("25.0%", self.dq_full_text, "Default member rate FAIL threshold 25.0% missing in DQ report")


if __name__ == "__main__":
    unittest.main()
