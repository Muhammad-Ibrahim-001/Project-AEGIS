# Project Evolution, Architecture Transitions & Change History

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Technical Leads, Project Maintainers, Academic Auditors  
**Tracking Horizon:** Inception through Fall 2026 Knowledge Base Baseline  

---

## 1. Executive Summary & Evolutionary Trajectory

The project has undergone a significant architectural transformation from an exploratory academic template into an enterprise-grade cloud data lakehouse. 

### Major Milestones:
1. **Inception & Legacy Template:** Began with generic course project templates (originally titled "LogiTrack" / standard retail PostgreSQL templates).
2. **Domain Pivot to National Energy Infrastructure:** Pivoted to U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather, unifying EIA, EPA, and NOAA datasets.
3. **Exploratory API Scrapers & Micro-Sampling:** Authored initial exploratory scripts in `archived/scratch_api_tests/` to inspect REST APIs (EPA CAMPD, NOAA, EIA) and download sample datasets for Plant 3 (Barry, Alabama).
4. **Lakehouse Paradigm Shift (100% Databricks Serverless):** Fully superseded local PostgreSQL database designs in favor of the **Databricks Serverless Cloud Lakehouse** running on Apache Spark, Delta Lake, Unity Catalog (`dwbi_catalog`), and Liquid Clustering.
5. **Phase 1 Formal Academic Baseline:** Compiled master specifications, visual Star Schema, 7-tab data dictionary, and 11-stage architecture mapping conforming to APA 7th Edition.
6. **Master Lakehouse Configuration & Standardization:** Implemented `03_ETL/config.py`, locked the 4-year temporal horizon (2021–2024), defined dynamic header scanning rules, and created idempotent catalog setup routines.
7. **Technical Knowledge Base Establishment:** Established persistent technical compatibility documentation in `technical-knowledge/`.
8. **Independent Technical Audit & Validation (November 8, 2026):** Conducted rigorous audit (`KNOWLEDGE_AUDIT.md`), correcting Serverless Environment v5+ caching behavior, detailing identity column `UPDATE SET * EXCEPT` rules, flagging Foreign Key DDL omissions in `warehouse.sql`, exposing legacy artifacts in `schema_diagram_mermaid.md`, and mandating `TRY_CAST()` under ANSI SQL mode.

---

## 2. Git Version Control Commit Audit Trail

The repository version history reflects the following recorded transitions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                GIT COMMIT AUDIT TRAIL                                  │
├─────────┬──────────────────────────────────────────────────┬───────────────────────────┤
│ Hash    │ Commit Message                                   │ Architectural Significance│
├─────────┼──────────────────────────────────────────────────┼───────────────────────────┤
│ 08341ca │ feat(architecture): initialize Databricks        │ Implemented config.py,    │
│         │ Lakehouse config, 4-year horizon, and clean      │ locked 2021-2024 window,  │
│         │ project structure                                │ and defined schemas.      │
├─────────┼──────────────────────────────────────────────────┼───────────────────────────┤
│ 1256d7b │ chore: clean repository, purge scripts and       │ Purged exploratory       │
│         │ research folders, and standardize on Databricks  │ scratch notes and legacy  │
│         │ Lakehouse                                        │ unneeded files.           │
├─────────┼──────────────────────────────────────────────────┼───────────────────────────┤
│ 40cbb38 │ refactor: standardize 100% on Databricks         │ Deprecated dual-stack;    │
│         │ Serverless Lakehouse & Delta Lake                │ standardized on Delta/UC. │
├─────────┼──────────────────────────────────────────────────┼───────────────────────────┤
│ fc59c77 │ Replace LogiTrack with DWBI Final Project        │ Formal introduction of U.S│
│         │ Lakehouse                                        │ Energy/Emissions domain.  │
├─────────┼──────────────────────────────────────────────────┼───────────────────────────┤
│ 598c5c0 │ first commit                                     │ Initial repository setup. │
└─────────┴──────────────────────────────────────────────────┴───────────────────────────┘
```

---

## 3. Detailed Architectural Evolution

### 3.1 Transition from Local PostgreSQL Stack to Databricks Lakehouse
* **Initial Concept (Course Syllabus Default):** Local PostgreSQL instances running schemas `project_staging`, `project_dw`, and `project_reporting`, loaded via Python `psycopg2` or `pgcopy`.
* **Identified Architectural Bottlenecks:**
  * National 4-year hourly emissions and weather datasets exceed **35,064 hourly periods across thousands of facilities**, generating tens of millions of records.
  * Local relational databases suffer severe I/O bottlenecks during complex multi-table analytical joins and multi-dimensional OLAP queries (`CUBE` and `ROLLUP`).
  * Lack of built-in ACID transaction log, time travel, and automated file-skipping.
* **Modern Lakehouse Solution:**
  * Replaced PostgreSQL tables with **Delta Lake** tables running on **Databricks Serverless Compute (Photon Engine)**.
  * Replaced manual B-Tree indexes and static partitioning with Delta Lake **Liquid Clustering** (`CLUSTER BY`).
  * Replaced local CSV imports with **Unity Catalog Volumes** (`/Volumes/dwbi_catalog/bronze_staging/raw_landing`).
  * Preserved course grading compatibility by defining schema aliases in `03_ETL/config.py`:
    ```python
    "COURSE_SCHEMA_ALIASES": {
        "project_staging": "bronze_staging",
        "project_dw": "gold_warehouse",
        "project_reporting": "gold_marts"
    }
    ```

### 3.2 Evolution of Ingestion & Header Handling Strategy
* **Initial Scratch Phase:** `archived/scratch_api_tests/fetch_and_save_samples.py` used hardcoded row index offsets:
  ```python
  # Hardcoded offset in early test script:
  df_gen = pd.read_excel(f, header=1) # EIA-860
  df_923 = pd.read_excel(f, header=5) # EIA-923
  ```
* **Production Lakehouse Defensive Pattern:** Upstream federal releases occasionally shift row positions due to title notes or metadata insertions. The architecture transitioned to **dynamic header scanning**:
  * Scans the initial 10 rows for signature strings (`'Plant Code'`, `'Plant Id'`).
  * Standardized in `03_ETL/config.py#L100` and `03_ETL/config.py#L110` (`HEADER_SCAN_KEYS`).

### 3.3 Evolution of Data Quality & Quarantine Policy
* **Early Draft Phase:** Initial drafts intended to reject any record with missing values or negative numbers.
* **Domain Discovery & Refinement:**
  * Discovery: Offline power plants consume auxiliary grid power during maintenance shutdowns, resulting in legitimate **negative net generation** (e.g., `-3,555 MWh` at Plant 26 Gaston).
  * Discovery: Universal Carnot heat-rate bounds fail to distinguish between high-efficiency CCGT baseload plants (5,000–14,000 Btu/kWh) and low-efficiency peaker gas turbines (9,000–22,000 Btu/kWh).
* **Current Baseline:** Implemented technology-specific heat-rate bounds and explicit allowance for negative net generation with audit tagging in `quarantine.rejected_records`.

---

## 4. Change Governance & Compatibility Verification Guidelines

To preserve compatibility and prevent regressions during future development sprints, developers and autonomous agents must adhere to the following governance rules:

1. **Verify Before Coding:** Never implement new notebooks or SQL pipelines without referencing [`COMPATIBILITY_BASELINE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/COMPATIBILITY_BASELINE.md).
2. **Maintain Delta Protocol Integrity:** Do not introduce legacy partitioning (`PARTITIONED BY`) on tables already defined with Liquid Clustering (`CLUSTER BY`).
3. **Respect Identity Column Invariants:**
   * Never execute `MERGE INTO` with `UPDATE SET *` on tables containing identity columns without using `EXCEPT (<identity_col>)`.
   * In `INSERT` clauses, ensure source datasets do not supply conflicting values to `GENERATED ALWAYS` columns.
   * If default surrogate rows (`-1 = Unknown`) are required, change the column specification to `GENERATED BY DEFAULT AS IDENTITY`.
4. **Observe Serverless Compute Boundaries:**
   * Do not write `%scala` or `%r` notebook cells.
   * Do not use SQL `CACHE TABLE` or `df.checkpoint()` (though `df.cache()` is permitted in Serverless Environment v5+ as an eager disk snapshot).
   * Do not attempt to dynamically load external Maven JARs via cluster UI; parse Excel files via driver Python `openpyxl`/`pandas`.
5. **Preserve Directory Boundaries:**
   * Never parse binary files in `01_Project_Documentation/Team_Guides/` (mandated by [`.agents`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/.agents)).
   * Do not alter historical artifacts in `archived/`.

---

## 5. Task 02 Audit Log & Corrections (November 8, 2026)

* **`KNOWLEDGE_AUDIT.md` Created:** Master audit report detailing 8 core technical findings and 6 cross-document contradictions.
* **`ENVIRONMENT.md` Updated:** Corrected Serverless Compute DataFrame caching capability (Env v5+ support for `df.cache()`).
* **`IMPLEMENTED_TECHNOLOGIES.md` Updated:** Added Enforced Constraints (`NOT NULL`), clarified omission of Foreign Keys in `warehouse.sql`, and detailed `TRY_CAST()` under ANSI mode.
* **`COMPATIBILITY_BASELINE.md` Updated:** Added comprehensive compatibility entries for ANSI SQL `TRY_CAST()`, Serverless Excel extraction, and ANSI timestamp literal syntax.
* **`PROJECT_PROFILE.md` Updated:** Added explicit audit warning regarding legacy types and schema names in `schema_diagram_mermaid.md`.
* **`OFFICIAL_SOURCES.md` Updated:** Added official citations for Serverless DataFrame caching, ANSI mode compliance, and Databricks constraint classifications.

---

## 6. Stage 2: Local Development Setup with Databricks Connect (November 8, 2026)

* **Team Technology Decision Implemented:** Standardized local client setup on Python 3.12.3 and Databricks Connect 18.3.7 to interface with Azure Databricks Serverless Environment Version 5.
* **Side-by-Side Python 3.12.3:** Installed via WinGet in user scope (`C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe`) without altering host default Python 3.14.5, Python 3.13.3, or system PATH.
* **Isolated Environment `.venv-dbx`:** Created via `py -3.12 -m venv .venv-dbx` at repository root.
* **Databricks Connect Client Installed:** Installed `databricks-connect==18.3.7` with all required dependencies (`databricks-sdk 0.162.0`, `grpcio 1.85.1`, `pandas 2.3.3`, `pyarrow 24.0.0`). Verified absence of standalone `pyspark` and `delta-spark`. Verified successful import of `databricks.connect` and Spark Connect stubs.
* **Repository Configuration:** Updated `.gitignore` to exclude `.venv*` and `.venv-dbx/`.
* **Documentation Updated:** Documented setup instructions and verification matrix in `ENVIRONMENT.md` Section 3.3 and `SESSION_CONTEXT.md` Section 4.

---

## 7. Approval of 4-Tier Development Standard & Preparation for Stage 3 (November 8, 2026)

* **Team-Wide Standard Formally Approved:** The team approved the mandatory development standard across all four members, explicitly decoupling four architectural dimensions:
  1. *Remote Compute:* Databricks Serverless Environment Version 5 (remote Python 3.12.x, Photon engine).
  2. *Local Python Interpreter:* Python 3.12.3 installed in user scope.
  3. *Client Library:* `databricks-connect==18.3.7` in dedicated `.venv-dbx` (strictly no standalone PySpark or delta-spark).
  4. *Authentication Architecture:* Individual authentication per teammate (OAuth / PAT outside repository in `~/.databrickscfg`; zero credentials in Git).
* **Repository Defensive Guard:** Updated `.gitignore` to explicitly exclude `.databrickscfg`, `.env*`, `*.token`, `*.pem`, `*.key`, and `credentials.json`.
* **Documentation Synchronization:** Updated `ENVIRONMENT.md`, `SESSION_CONTEXT.md`, `README.md`, and `DATABRICKS_SERVERLESS_ARCHITECTURE.md` to reflect the 4-tier separation matrix.
* **Stage 3 Prepared:** Formulated non-credential-bearing test harness (`tests/test_remote_connection.py`) and detailed individual authentication workflows pending explicit user authorization.


