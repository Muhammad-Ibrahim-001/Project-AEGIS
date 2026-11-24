# 01_Project_Documentation

This directory is the master academic documentation repository for the **DL3004 Data Warehousing & Business Intelligence (DWBI)** Final Project: *U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Lakehouse*.

The folder is structured into dedicated phase directories, technical specifications, and mandatory syllabus requirements.

---

## Directory Organization & Index

```
01_Project_Documentation/
├── README.md                                # Master documentation index & navigation guide
├── Architecture.png                         # Master pipeline architecture diagram (PNG)
├── Architecture.pdf                         # Master pipeline architecture diagram (PDF)
│
├── course_requirements/                     # ⚠️ Official Syllabus & Phase Grading Rubrics (MANDATORY)
│   ├── DWBI Final Project Overview.pdf
│   ├── DWBI Lab Phase 1.pdf
│   ├── DWBI Lab Phase 2.pdf
│   ├── DWBI Lab Phase 3.pdf
│   ├── README.md
│   └── Sample Project Architecture Diagram.png
│
├── phase_1/                                 # Phase 1: Dimensional Modeling & Requirements
│   ├── 01_Project_Proposal.pdf              # Official Deliverable 1: Proposal & Lakehouse blueprint
│   ├── 02_Business_Requirements_Document.pdf# Official Deliverable 2: Enterprise BRD (FRs, NFRs, SLAs)
│   ├── 03_10_Business_Questions.pdf         # Official Deliverable 3: 12 Analytical Business Questions
│   ├── 04_Fact_and_Dimension_Identification.pdf # Official Deliverable 4: Kimball Bus Matrix & catalogs
│   ├── 05_Grain_Definition_Document.pdf     # Official Deliverable 5: Atomic Grains & measure additivity
│   ├── 06_Schema_Diagrams.pdf               # Official Deliverable 6: 3-Tier Schema Diagrams
│   ├── 07_Data_Dictionary.xlsx              # Official Deliverable 7: 7-Tab Enterprise Excel Catalog
│   ├── Project_Proposal.md                  # Source markdown specification
│   ├── Business_Requirements_Document.md    # Source markdown specification
│   ├── Business_Questions.md                # Source markdown specification (BQ1–BQ12)
│   ├── Grain_Definitions.md                 # Source markdown specification
│   ├── Requirements.md                      # Source markdown requirements mapping
│   └── schema_diagram_mermaid.md            # Mermaid ER & Star Schema diagrams
│
├── phase_2/                                 # Phase 2: Data Quality, Cleansing & ETL
│   ├── Data_Cleaning_Report.pdf             # Official Data Cleaning Audit Report (ReportLab)
│   └── Data_Quality_Report.pdf              # Official 6-Category Data Quality Report (ReportLab)
│
├── phase_3/                                 # Phase 3: Analytics, Optimization & BI
│   ├── Indexing_Report.pdf                  # Official 8-Page Databricks Query Profile Report
│   ├── Indexing_Report.html                 # Publication HTML template (Microsoft Edge engine)
│   ├── analytical_queries_plan.md           # Analytical & OLAP query execution roadmap
│   └── screenshots/                         # Authentic Databricks Query Profile execution proofs (16 files)
│
├── specifications/                          # Technical Specifications & Data Catalogs
│   ├── DATA_SOURCES_MASTER_SPECIFICATION.md # 633-line federal data source catalog & schemas
│   ├── column_removal_map.md                # Silver -> Gold 343-column pruning reference
│   ├── Silver_Layer_Architecture_and_Concepts.md # Silver conformance architecture
│   ├── Silver_Layer_Detailed_Guide.md       # Comprehensive silver transformation guide
│   └── Silver_Layer_Functions_and_Pipeline_Reference.md # Pipeline method signatures & contracts
│
└── Team_Guides/                             # 👥 Human Onboarding Guides (.docx, off-limits to AI)
```

---

## 1. Official Phase 1 Deliverables (`phase_1/`)
1. **[`phase_1/01_Project_Proposal.pdf`](phase_1/01_Project_Proposal.pdf)**: 8-chapter project proposal, Medallion architecture blueprint, Kimball dimensional design, and execution roadmap.
2. **[`phase_1/02_Business_Requirements_Document.pdf`](phase_1/02_Business_Requirements_Document.pdf)**: Enterprise Business Requirements Document (stakeholder personas, FR1–FR12, NFR1–NFR8, SLAs, governance).
3. **[`phase_1/03_10_Business_Questions.pdf`](phase_1/03_10_Business_Questions.pdf)**: 12 analytical business questions (BQ1–BQ12) with mathematical metric formulas, ANSI SQL sketches, and Power BI visual mappings.
4. **[`phase_1/04_Fact_and_Dimension_Identification.pdf`](phase_1/04_Fact_and_Dimension_Identification.pdf)**: Kimball Dimensional Bus Matrix, 5 conformed dimensions (including `dim_generator` SCD Type 2), and 3 multi-grain fact tables.
5. **[`phase_1/05_Grain_Definition_Document.pdf`](phase_1/05_Grain_Definition_Document.pdf)**: Atomic grain declarations, measure additivity classification rules, and physical unit standardization.
6. **[`phase_1/06_Schema_Diagrams.pdf`](phase_1/06_Schema_Diagrams.pdf)**: 3-tier modeling diagrams (Conceptual Model, Logical Kimball Star Schema, and Physical Delta Lake DDL Model with Liquid Clustering).
7. **[`phase_1/07_Data_Dictionary.xlsx`](phase_1/07_Data_Dictionary.xlsx)**: Authoritative 7-tab enterprise data catalog (Overview, Bronze Tables, Dimensions, Facts, Quarantine, Reporting Marts, Code Lists).

*(Note: Raw diagram generation scripts and submission bundles reside untouched in [`../archived/Phase_1_Submission/`](../archived/Phase_1_Submission/).)*

---

## 2. Official Phase 2 Deliverables (`phase_2/`)
1. **[`phase_2/Data_Cleaning_Report.pdf`](phase_2/Data_Cleaning_Report.pdf)**: Automated cleaning audit report covering shifting header discovery, sentinel coercion, thermodynamic heat rate pruning, and dead-letter quarantine routing.
2. **[`phase_2/Data_Quality_Report.pdf`](phase_2/Data_Quality_Report.pdf)**: Comprehensive 6-category data quality audit (Completeness, Accuracy, Referential Integrity, Uniqueness, Row Reconciliation, Date Coverage) generated dynamically via `03_ETL/06_generate_pdf_reports.py`.

---

## 3. Official Phase 3 Deliverables (`phase_3/`)
1. **[`phase_3/Indexing_Report.pdf`](phase_3/Indexing_Report.pdf)**: Formal publication-grade 8-page query optimization and indexing benchmark report featuring authentic Databricks Query Profiles, execution DAGs, Photon metrics, and NVMe cache hit ratios.
2. **[`phase_3/Indexing_Report.html`](phase_3/Indexing_Report.html)**: Clean HTML/CSS document compiled into PDF via headless Microsoft Edge.
3. **[`phase_3/screenshots/`](phase_3/screenshots/)**: 16 high-resolution execution proofs extracted directly from the Databricks SQL Warehouse Query History.

---

## 4. Master Technical Specifications (`specifications/`)
* **[`specifications/DATA_SOURCES_MASTER_SPECIFICATION.md`](specifications/DATA_SOURCES_MASTER_SPECIFICATION.md)**: Exhaustive 633-line technical specification for all 6 federal datasets (EIA-860/923/930, EPA CAMPD, EPA–EIA Crosswalk, NOAA ISD).
* **[`specifications/column_removal_map.md`](specifications/column_removal_map.md)**: Source-by-source Silver-to-Gold column pruning reference (343 raw physical columns across 10 datasets).
* **[`specifications/Silver_Layer_Architecture_and_Concepts.md`](specifications/Silver_Layer_Architecture_and_Concepts.md)**: Comprehensive architectural guide for conformed Silver tables and SCD Type 2 tracking.
* **[`specifications/Silver_Layer_Detailed_Guide.md`](specifications/Silver_Layer_Detailed_Guide.md)**: Step-by-step transformation specifications.
* **[`specifications/Silver_Layer_Functions_and_Pipeline_Reference.md`](specifications/Silver_Layer_Functions_and_Pipeline_Reference.md)**: Function signatures, parameter types, and validation rules.

---

## 5. Mandatory Academic Reference Directories
* **[`course_requirements/`](course_requirements/) — ⚠️ MANDATORY GROUND TRUTH:**  
  Official university syllabus, phase grading rubrics (`DWBI Lab Phase 1.pdf`, `DWBI Lab Phase 2.pdf`, `DWBI Lab Phase 3.pdf`), and reference architecture. All code and schema implementations adhere strictly to these rubrics.
* **[`Team_Guides/`](Team_Guides/) — 👥 HUMAN ONBOARDING ONLY:**  
  Formatted Microsoft Word guides (`.docx`) detailing the 4-person work packages (WP1–WP4) for human team members. *(Strictly off-limits to AI agents per [`AGENTS.md`](../AGENTS.md).)*
