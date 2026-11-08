# DL3004 DWBI Final Project: U.S. Power Generation, Smokestack Emissions & Synoptic Weather Lakehouse

> **🤖 AI AGENT OPERATIONAL DIRECTIVE:**  
> Before modifying or generating code, schemas, or analytics, **review [`AGENTS.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/AGENTS.md)** and follow these core rules:  
> 1. **DO NOT parse files inside `01_Project_Documentation/Team_Guides/`** (binary `.docx` human onboarding guides).  
> 2. **ALWAYS read and comply with `01_Project_Documentation/course_requirements/`** (official university grading rubrics).  
> 3. Architecture Ground Truth: The project is implemented exclusively on the **Databricks Serverless Cloud Lakehouse** governed under Unity Catalog (`dwbi_catalog`). Refer to **[`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md)** and **[`PROJECT_BLUEPRINT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md)**.

---

## 1. Executive Summary

This project implements an enterprise-grade, end-to-end cloud data lakehouse on **Databricks Serverless Compute** powered by **Apache Spark**, **Delta Lake**, **Unity Catalog**, and **Microsoft Power BI Desktop**. It analyzes the relationship between electrical grid dispatch, fossil-fuel power plant smokestack emissions, and synoptic weather stress events across the United States.

It replaces the default mock retail scenario with an uncompromised, real-world multi-source data ecosystem:
1. **EIA-860 / EIA-860M:** Generator asset inventory and the many-to-many `6_1_EnviroAssoc` Boiler-to-Generator topology.
2. **EIA-923:** Monthly net generation (`Netgen_MWh`), fuel consumption, delivered fuel prices, and plant-level fuel stocks.
3. **EIA-930:** Hourly Balancing Authority (BA) electrical demand, generation by fuel mix, and interconnector power flows.
4. **EPA CAMPD (CEMS):** Continuous Emission Monitoring System hourly smokestack measurements ($\text{SO}_2, \text{NO}_x, \text{CO}_2$, Gross MW, and Heat Input).
5. **EPA–EIA Crosswalk:** The official federal crosswalk bridging combustion boilers to electric generators.
6. **NOAA ISD (Integrated Surface Database):** Hourly synoptic meteorological observations (ambient temperature, wind speed, pressure).
7. **FERC Form 1:** Major electric utility financial ledger, O&M expenses, and joint-venture asset ownership.

---

## 2. Lakehouse Technology Stack

| Layer | Technology | Operational Mode / Engine | Purpose in Project |
| :--- | :--- | :--- | :--- |
| **Cloud Lakehouse Platform** | Databricks (`databricks.com`) | Managed Cloud Workspace | Unified platform for data engineering, governance, and SQL analytics. |
| **Processing Engine** | **Apache Spark 3.5+ / 4.x** | **Serverless Notebook Compute (Photon Engine)** | Distributed data processing, shifting-header Excel extraction, and SCD transformation. |
| **Warehouse & Query Engine**| **Databricks SQL (DB SQL)** | **Serverless SQL Warehouse** | Low-latency SQL query execution, analytical views, and live BI connectivity. |
| **Storage & Table Format** | **Delta Lake** | Open Parquet + ACID Log (`_delta_log`) | ACID transactions, time travel, schema evolution, and Liquid Clustering. |
| **Unified Governance & Lineage**| **Unity Catalog** | 3-Tier Namespace (`catalog.schema.table`) | Centralized data governance, raw landing volumes, and data contracts. |
| **Target Catalog** | **`dwbi_catalog`** | Dedicated Unity Catalog Container | Encapsulates all schemas (`bronze_staging`, `silver_conformed`, `gold_warehouse`, `gold_marts`, `quarantine`). |
| **Data Transformation (ELT)**| **PySpark & Databricks SQL** | Delta `MERGE INTO` & Serverless Pipelines | Automated Medallion processing (Bronze $\to$ Silver $\to$ Gold) and SCD Type 1 & 2. |
| **Business Intelligence (BI)** | **Microsoft Power BI Desktop** | Native Databricks Connector (DirectQuery) | Interactive 3-page dashboard connected live to `dwbi_catalog.gold_marts`. |

### 2.1 Approved Team-Wide Development Standard (Mandatory Baseline)

All four team members adhere to a strictly unified, 4-tier development and connectivity baseline:
1. **Remote Serverless Compute Version:** Azure/AWS Databricks **Serverless Environment Version 5** (Photon engine, remote Python 3.12.x container, Spark Connect gRPC).
2. **Local Python Version:** **Python 3.12.3** (`py -3.12`), installed in user scope. Strictly leaves host default Python (3.14/3.13) and system PATH untouched; provides exact minor-version parity with remote serverless compute for Python UDF support.
3. **Databricks Connect Package Version:** **`databricks-connect==18.3.7`** installed in the dedicated repository-root **`.venv-dbx`** virtual environment. **Strictly NO standalone `pyspark` or `delta-spark` packages are installed**. All code compiles to Spark Connect Protobuf plans.
4. **Individual Authentication Requirements:** Each member authenticates individually via Databricks CLI OAuth (`databricks auth login`) or Personal Access Token (PAT). Credentials reside strictly in the user's home profile (`~/.databrickscfg`) or in-memory session environment variables. **Zero credentials are stored in the Git repository**. Action and audit history in Unity Catalog attribute to individual teammate accounts (`current_user()`).

---

## 3. Unity Catalog Architecture (`dwbi_catalog`)

```
dwbi_catalog/
├── Volumes/
│   └── bronze_staging/
│       └── raw_landing/                     # Landing zone for raw EIA, EPA, NOAA files
│
├── Schemas:
│   ├── bronze_staging                       # Append-only raw Delta tables + etl_run_log
│   ├── silver_conformed                     # Cleansed, deduplicated, conformed tables
│   ├── gold_warehouse                       # Kimball Star Schema (5 Dims + 3 Multi-Grain Facts)
│   ├── gold_marts                           # Materialized reporting views for Power BI DirectQuery
│   └── quarantine                           # Dead-letter quarantine table (rejected_records)
```

---

## 4. 4-Person Division of Work (Phase 2 & Phase 3)

The project workload is split into four decoupled, modular work packages:

| Work Package | Lead Member | Scope & Key Deliverables | Viva / Evaluation Focus |
| :--- | :--- | :--- | :--- |
| **WP1: Ingestion & Bronze Lead** | Muhammad Ibrahim (24L-2602) | Raw landing volume setup, Bronze staging DDL, PySpark extractors, dynamic header discovery, and ETL run logging (`dwbi_catalog.bronze_staging.etl_run_log`). | Automated multi-source extraction, immutable raw landing tables, and pipeline error recovery. |
| **WP2: Data Quality & Silver Lead** | Rai Fahad Sultan (24L-2509) | Cleansing rules, sentinel coercion, dead-letter quarantine (`dwbi_catalog.quarantine.rejected_records`), SCD Type 2 tracking via `MERGE INTO`, and written DQ Report (PDF). | Defensive data validation, dead-letter quarantine pattern, and atomic SCD Type 2 updates. |
| **WP3: DW & Gold Architect** | Muhammad Ayyan (24L-2568) | Kimball Star Schema DDL, surrogate key lookups, 3 multi-grain fact tables, and Liquid Clustering (`CLUSTER BY`). | Dimensional modeling, handling multi-grain facts, surrogate key mapping, and storage optimization. |
| **WP4: Analytics, OLAP & BI Lead** | Taha Imran (24L-2560) | Gold reporting views (`dwbi_catalog.gold_marts.vw_*`), OLAP SQL (`ROLLUP`, `CUBE`), Serverless SQL query tuning, and 3-page Power BI Dashboard via DirectQuery. | DirectQuery Power BI performance, multi-dimensional OLAP slicing, and energy grid insights. |

---

## 5. Clean Repository Layout

```
DWBI-Final-Project/
├── AGENTS.md                         # AI Agent Operational Directives & Binding Rules
├── .gitignore                        # Git exclusion specifications
├── README.md                         # This master repository guide
├── DATABRICKS_SERVERLESS_ARCHITECTURE.md # Canonical Databricks Lakehouse Architecture Blueprint
├── PROJECT_BLUEPRINT.md              # Master System Specification & Dimensional Definitions
│
├── 01_Project_Documentation/
│   ├── Requirements.pdf              # Official university submission: Problem statement & scope
│   ├── Schema.pdf                    # Official university submission: Visual Star Schema diagram
│   ├── Data_Dictionary.xlsx          # Official university submission: Complete 7-tab data catalog
│   ├── Architecture.pdf / .png       # High-resolution pipeline architecture diagram
│   ├── Schema.png                    # High-resolution Star Schema raster diagram
│   ├── schema_diagram_mermaid.md     # Verified Mermaid code for Draw.io diagram rendering
│   ├── Requirements.md               # Markdown summary linking to preserved Phase 1 documents
│   ├── README.md                     # Documentation folder index and guidelines
│   ├── course_requirements/          # ⚠️ MANDATORY: University syllabus, rubrics, architecture
│   └── Team_Guides/                  # ⛔ HUMAN ONBOARDING: Word .docx guides (DO NOT PARSE)
│
├── 02_Data/
│   ├── raw_data/                     # Raw bulk archives (EIA-860/923, EPA CAMPD, NOAA ISD)
│   └── cleaned_data/                 # Cleaned CSV outputs ready for Silver/Gold loading
│
├── 03_ETL/
│   └── config.py                     # ⭐ Master Lakehouse Configuration & Catalog Setup (Databricks)
│
├── 04_SQL/                           # Production Databricks SQL DDL (warehouse, staging, views, quality checks)
│
├── 05_Analytics/                     # Analytical SQL, OLAP queries (ROLLUP/CUBE) & views
│
└── archived/                         # 🗄️ Preserved Historical Artifacts & Early Drafts
    ├── Phase_1_Submission/           # Complete formal academic Phase 1 package
    ├── early_sql_drafts/             # Initial staging, warehouse, and OLAP SQL drafts
    └── scratch_api_tests/            # Preliminary test scrapers & micro-samples
```

---

## 6. Key Engineering Gotchas Handled

1. **Shifting Excel Headers:** EIA-860 headers are on Row 2; EIA-923 headers are on Row 6. Handled via programmatic header discovery scanning for `'Plant Code'` / `'Plant Id'`.
2. **Missing Value Sentinels:** Coerces literal strings (`"."`, `"NM"`, `"*"`, `""`) and NOAA's integer `-9999` to `NULL`, extracting sensor quality flags into separate indicators.
3. **Negative Net Generation:** Defensive rules allow negative net generation in EIA-923 caused by power plants consuming station auxiliary power during maintenance shutdowns.
4. **Thermodynamic Physical Bounds:** Heat rate sanity checks apply realistic technology-specific thresholds (CCGT: 5,000–14,000 Btu/kWh; Coal: 8,500–18,000 Btu/kWh; Peakers: 9,000–22,000 Btu/kWh), routing anomalies to `dwbi_catalog.quarantine.rejected_records`.
5. **Physical Auxiliary Reconciliation:** Validates that $\text{Net Generation (EIA-923)} \le \text{Gross Generation (EPA CAMPD)}$ with auxiliary load ratios between $3\%$ and $14\%$.
6. **Liquid Clustering:** Delta tables replace legacy B-Tree indexes and manual table partitioning with automatic partition pruning and Z-order clustering via `CLUSTER BY (date_key, plant_key)`.
