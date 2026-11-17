# Phase 2: Physical Data Warehouse Implementation & ETL Pipeline
## Executive Summary & Syllabus Deliverables Checklist

**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)  
**Institution:** FAST National University of Computer and Emerging Sciences  
**Academic Semester:** Fall 2026  
**Phase:** 2 — Physical DW Implementation & ETL Pipeline (Weightage: 40% / 40 Marks)  
**Primary Cloud Target:** Databricks Serverless Cloud Lakehouse (`dwbi_catalog`)  
**Secondary Syllabus Benchmark:** PostgreSQL (`project_staging`, `project_dw`, `project_reporting`)  
**GitHub Repository:** [https://github.com/Muhammad-Ibrahim-001/LogiTrack.git](https://github.com/Muhammad-Ibrahim-001/LogiTrack.git)

---

## 1. 4-Person Modular Division of Work

| Student Name | Roll Number | Work Package Role | Core Deliverable Responsibilities |
| :--- | :--- | :--- | :--- |
| **Muhammad Ibrahim** | 24L-2602 | **WP1 Lead: Bronze & Ingestion** | Raw Volumes, dynamic Excel header scanning (EIA-860/923), Bronze staging DDL, append-only landing, `etl_run_log` auditing. |
| **Rai Fahad Sultan** | 24L-2509 | **WP2 Lead: Data Quality & Silver** | Data cleansing engine, whitespace trimming, sentinel coercion, dead-letter quarantine (`quarantine.rejected_records`), 6-category DQ test suite. |
| **Muhammad Ayyan** | 24L-2568 | **WP3 Lead: DW & Gold Architect** | Kimball Star Schema DDL, surrogate key lookups, SCD Type 2 unit lifecycle tracking, 3 multi-grain fact tables, Liquid Clustering (`CLUSTER BY`). |
| **Taha Imran** | 24L-2560 | **WP4 Lead: Analytics & BI** | Reporting views (`gold_marts.vw_*`), OLAP SQL queries (`ROLLUP`, `CUBE`), Power BI DirectQuery model, physical query plan optimization. |

---

## 2. Phase 2 Deliverables Matrix (Syllabus PDF Verification)

As specified in `DWBI Lab Phase 2.pdf`, the following deliverables are required and provided:

| Deliverable (per Course PDF) | File Name in Submission Package | Description & Marks Contribution |
| :--- | :--- | :--- |
| **1. Staging Schema SQL** | `01_Staging_Schema.sql` | Staging DDL for Databricks Delta Lake (`bronze_staging`) and PostgreSQL (`project_staging`), audit log, and quarantine table. |
| **2. DW Schema SQL** | `02_DW_Schema.sql` | Kimball Star Schema DDL: 5 Conformed Dimensions + 3 Multi-Grain Fact Tables with Liquid Clustering and foreign key constraints. |
| **3. Dimension Load Scripts SQL** | `03_Dimension_Load_Scripts.sql` | SQL extracting and transforming raw entities, surrogate key generation via `IDENTITY`, SCD Type 2 merge logic, and `-1` unknown member seeding. |
| **4. Fact Load Scripts SQL** | `04_Fact_Load_Scripts.sql` | Business key to surrogate key resolution joins, spatial proximity lookups, and multi-grain fact population with zero orphan FKs. |
| **5. PostgreSQL Database SQL Scripts** | `05_Database_Implementation_PostgreSQL_and_Databricks.sql` | Complete end-to-end database implementation for both PostgreSQL and Databricks with verification and integrity checks. |
| **6. Data Cleaning Report PDF** | `06_Data_Cleaning_Report.pdf` | Formal PDF report documenting text normalization, federal sentinel coercion, negative netgen handling, heat rate bounds, and defect recovery. |
| **7. Data Quality Report PDF** | `07_Data_Quality_Report.pdf` | Formal PDF report evaluating 66 checks across all 6 quality dimensions (Completeness, Accuracy, Integrity, Uniqueness, Row Conservation, Date Coverage). |
| **8. Master Architecture Specification** | `08_Physical_DW_and_ETL_Executive_Summary.pdf` | Executive summary PDF detailing complete physical lakehouse architecture and 40-mark rubric checklist. |
| **9. ETL Scripts SQL/Python** | `scripts/etl/*.py` | Modular 5-stage automated Python ETL pipeline runnable in local workstations, CI/CD, and Databricks Serverless clusters. |
| **10. GitHub Repository Link** | Embedded in all files & README | `https://github.com/Muhammad-Ibrahim-001/LogiTrack.git` |

---

## 3. Rubric Evaluation Scorecard (40 / 40 Marks)

### Section 1: Database Implementation (10 Marks)
- [x] **PostgreSQL & Databricks Schemas:** Staging (`bronze_staging` / `project_staging`), Warehouse (`gold_warehouse` / `project_dw`), Reporting (`gold_marts` / `project_reporting`), and Quarantine (`quarantine`).
- [x] **Primary & Foreign Key Integrity:** Natural business keys mapped to surrogate primary keys; 0 orphan foreign key records across all 3 facts.
- [x] **Table Constraints:** NOT NULL constraints, identity columns, decimal precision clamping, and check bounds.

### Section 2: ETL Pipeline (15 Marks)
- [x] **Multi-Source Ingestion:** Ingests 9 federal datasets (EIA-860, EIA-923, EPA CAMPD, NOAA ISD, EIA-930, Crosswalk).
- [x] **Dynamic Header Discovery:** Programmatically scans shifting rows for Excel headers (Row 2 for EIA-860, Row 6 for EIA-923).
- [x] **Data Transformations:** Whitespace trimming, uppercase folding, coordinate geocoding, and date parsing.
- [x] **Dead-Letter Quarantine:** Isolates corrupt records with reason classification and raw JSON payloads.

### Section 3: Surrogate Key Implementation (5 Marks)
- [x] **Surrogate Key Generation:** Auto-incrementing BIGINT IDENTITY keys for `dim_plant`, `dim_generator`, `dim_balancing_authority`, `dim_weather_station`, and integer `date_key` (`YYYYMMDD`).
- [x] **Business-to-Surrogate Key Mapping:** Fact loading executes joins to substitute business identifiers with integer surrogate keys.
- [x] **SCD Type 2 Tracking:** Tracks unit operational transitions with `valid_from`, `valid_to`, and `is_current`.
- [x] **Default Unknown Member:** Pre-seeded `-1` surrogate keys handle unmapped or missing natural keys.

### Section 4: Data Quality Validation (10 Marks)
- [x] **Completeness:** 40/40 checks pass; 0.00% nulls on surrogate and natural keys.
- [x] **Accuracy & Reconciliation:** Auxiliary load ratio reconciled (9.75%); Silver-to-Gold measure conservation variance is 0.000%.
- [x] **Referential Integrity:** 8/8 checks pass; 0 orphan fact records.
- [x] **Uniqueness:** 8/8 checks pass; 0 duplicate primary or natural keys.
- [x] **Row Count Conservation:** $\text{Rows In} = \text{Rows Out} + \text{Quarantined} + \text{Deduplicated}$; 0 unexplained variances.
- [x] **Date Coverage:** Universal calendar contains all 1,461 calendar days (2021-2024); 0 missing dates.
- [x] **Volume Gate:** Dimensions contain 382 rows (exceeds $\ge 100$ rubric gate); Fact contains 12,500 rows (exceeds $\ge 10,000$ rubric gate); Total fact rows = 16,182.
