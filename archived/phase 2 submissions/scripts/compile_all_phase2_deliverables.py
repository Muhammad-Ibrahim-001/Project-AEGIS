import subprocess
import os
import shutil
import time
from pathlib import Path

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SCRIPT_DIR = Path(__file__).resolve().parent
SUBMISSION_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SUBMISSION_DIR.parent.parent
DOC_DIR = PROJECT_ROOT / "01_Project_Documentation"

def run_script(script_name):
    script_path = SCRIPT_DIR / script_name
    print(f"Running {script_name}...")
    res = subprocess.run(["python", str(script_path)], cwd=str(SCRIPT_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  [ERROR] in {script_name}: {res.stderr}")
    else:
        print(f"  [OK] {res.stdout.strip()}")

def convert_html_to_pdf(html_file, pdf_file):
    html_path = SCRIPT_DIR / html_file
    pdf_path = SUBMISSION_DIR / pdf_file
    
    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file:///{str(html_path).replace(os.sep, '/')}"
    ]
    print(f"Converting {html_file} -> {pdf_file}...")
    subprocess.run(cmd, check=True)
    time.sleep(1)
    if pdf_path.exists():
        size = pdf_path.stat().st_size
        print(f"  [OK] Created {pdf_file} ({size:,} bytes)")
    else:
        print(f"  [FAIL] Could not find {pdf_file}")

def create_submission_zip():
    zip_base = SUBMISSION_DIR / "Phase_2_Submission"
    print(f"Creating submission zip: {zip_base}.zip...")
    
    # We create zip of SUBMISSION_DIR excluding zip itself and __pycache__
    files_to_zip = [
        "01_Staging_Schema.sql",
        "02_DW_Schema.sql",
        "03_Dimension_Load_Scripts.sql",
        "04_Fact_Load_Scripts.sql",
        "05_Database_Implementation_PostgreSQL_and_Databricks.sql",
        "06_Data_Cleaning_Report.pdf",
        "07_Data_Quality_Report.pdf",
        "08_Physical_DW_and_ETL_Executive_Summary.pdf",
        "Phase_2_Executive_Summary_and_Checklist.md",
        "Phase_2_ETL_Pipeline_Architecture.md"
    ]
    
    import zipfile
    with zipfile.ZipFile(f"{zip_base}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files_to_zip:
            p = SUBMISSION_DIR / f
            if p.exists():
                zf.write(p, arcname=f)
                print(f"  [ZIP] Added {f}")
        
        # Add scripts/etl
        etl_dir = SUBMISSION_DIR / "scripts" / "etl"
        if etl_dir.exists():
            for pyfile in etl_dir.glob("*.py"):
                zf.write(pyfile, arcname=f"scripts/etl/{pyfile.name}")
                print(f"  [ZIP] Added scripts/etl/{pyfile.name}")
                
    zip_size = Path(f"{zip_base}.zip").stat().st_size
    print(f"  [OK] Phase_2_Submission.zip created successfully ({zip_size:,} bytes)")

def main():
    print("====================================================")
    print("PHASE 2 DELIVERABLES AUTOMATED COMPILER")
    print("====================================================")

    # 1. Run all HTML generators
    generators = [
        "generate_cleaning_report.py",
        "generate_dq_report.py",
        "generate_executive_summary.py"
    ]
    for g in generators:
        run_script(g)

    # 2. Convert HTMLs to PDFs in SUBMISSION_DIR
    conversions = [
        ("Data_Cleaning_Report.html", "06_Data_Cleaning_Report.pdf"),
        ("Data_Quality_Report.html", "07_Data_Quality_Report.pdf"),
        ("Phase_2_Executive_Summary.html", "08_Physical_DW_and_ETL_Executive_Summary.pdf")
    ]
    for h, p in conversions:
        convert_html_to_pdf(h, p)

    # 3. Synchronize with 01_Project_Documentation
    shutil.copyfile(SUBMISSION_DIR / "06_Data_Cleaning_Report.pdf", DOC_DIR / "Data_Cleaning_Report.pdf")
    shutil.copyfile(SUBMISSION_DIR / "07_Data_Quality_Report.pdf", DOC_DIR / "Data_Quality_Report.pdf")
    print("  [OK] Synchronized reports with 01_Project_Documentation/")

    # 4. Create submission zip
    create_submission_zip()

    print("====================================================")
    print("ALL PHASE 2 DELIVERABLES SUCCESSFULLY COMPILED!")
    print("====================================================")

if __name__ == "__main__":
    main()
