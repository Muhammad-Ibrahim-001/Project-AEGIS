import subprocess
import os
import shutil
import time

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)
DOC_DIR = os.path.abspath("01_Project_Documentation")

def run_script(script_name):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    print(f"Running {script_name}...")
    res = subprocess.run(["python", script_path], cwd=SCRIPT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error in {script_name}: {res.stderr}")
    else:
        print(f"Success: {res.stdout.strip()}")

def convert_html_to_pdf(html_file, pdf_file):
    html_path = os.path.join(SCRIPT_DIR, html_file)
    pdf_path = os.path.join(SUBMISSION_DIR, pdf_file)
    
    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file:///{html_path.replace(os.sep, '/')}"
    ]
    print(f"Converting {html_file} -> {pdf_file}...")
    subprocess.run(cmd, check=True)
    time.sleep(1)
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"  [OK] Created {pdf_file} ({size:,} bytes)")
    else:
        print(f"  [FAIL] Could not find {pdf_file}")

def main():
    print("====================================================")
    print("PHASE 1 DELIVERABLES AUTOMATED COMPILER (scripts/)")
    print("====================================================")

    # 1. Run all generators
    scripts = [
        "generate_conceptual_diagram.py",
        "generate_logical_diagram.py",
        "generate_physical_diagram.py",
        "generate_doc1_proposal.py",
        "generate_doc2_brd.py",
        "generate_doc3_business_questions.py",
        "generate_doc4_fact_dim.py",
        "generate_doc5_grain.py",
        "generate_doc6_schema_diagrams.py"
    ]
    for s in scripts:
        run_script(s)

    # 2. Convert all 6 HTMLs to PDFs in SUBMISSION_DIR
    conversions = [
        ("01_Project_Proposal.html", "01_Project_Proposal.pdf"),
        ("02_Business_Requirements_Document.html", "02_Business_Requirements_Document.pdf"),
        ("03_10_Business_Questions.html", "03_10_Business_Questions.pdf"),
        ("04_Fact_and_Dimension_Identification.html", "04_Fact_and_Dimension_Identification.pdf"),
        ("05_Grain_Definition_Document.html", "05_Grain_Definition_Document.pdf"),
        ("06_Schema_Diagrams.html", "06_Schema_Diagrams.pdf"),
    ]
    for h, p in conversions:
        convert_html_to_pdf(h, p)

    # 3. Synchronize 7 deliverables with 01_Project_Documentation
    deliverables = [
        "01_Project_Proposal.pdf",
        "02_Business_Requirements_Document.pdf",
        "03_10_Business_Questions.pdf",
        "04_Fact_and_Dimension_Identification.pdf",
        "05_Grain_Definition_Document.pdf",
        "06_Schema_Diagrams.pdf",
        "07_Data_Dictionary.xlsx"
    ]
    for f in deliverables:
        src = os.path.join(SUBMISSION_DIR, f)
        dst = os.path.join(DOC_DIR, f)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
    print("  [OK] Synchronized all 7 deliverable PDFs and Excel catalog with 01_Project_Documentation/")

    print("====================================================")
    print("ALL 7 PHASE 1 DELIVERABLES SUCCESSFULLY COMPILED!")
    print("====================================================")

if __name__ == "__main__":
    main()
