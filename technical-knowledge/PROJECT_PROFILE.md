# Project Profile: U.S. Bulk Power Generation, Smokestack Air Emissions & Synoptic Weather Lakehouse

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Data Engineers, Technical Architects, Academic Evaluators, Autonomous AI Agents  
**Project Workspace:** `d:\Semester Projects\DWBI LAB Project`  

---

## 1. Executive Summary & Project Identity

### 1.1 Project Identity & Academic Context
* **Project Title:** Integrated Analysis of U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather
* **Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)
* **Academic Institution:** FAST National University of Computer and Emerging Sciences
* **Academic Term:** Fall 2026
* **Collaborative Team Structure (4-Person Decoupled Modules):**
  * **Muhammad Ibrahim (24L-2602):** Work Package 1 — Ingestion & Bronze Lakehouse Lead
  * **Rai Fahad Sultan (24L-2509):** Work Package 2 — Data Quality & Silver Conformance Lead
  * **Muhammad Ayyan (24L-2568):** Work Package 3 — Dimensional Warehouse & Gold Layer Architect
  * **Taha Imran (24L-2560):** Work Package 4 — Analytics, OLAP, Power BI & Performance Lead
* **Primary Architectural Blueprint Documents:**
  * Master System Blueprint: [`PROJECT_BLUEPRINT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md)
  * Serverless Lakehouse Runbook: [`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md)
  * AI Agent Operational Directives: [`.agents`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/.agents)
  * Master Configuration Module: [`03_ETL/config.py`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py)
  * Master Data Specification: [`01_Project_Documentation/DATA_SOURCES_MASTER_SPECIFICATION.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/01_Project_Documentation/DATA_SOURCES_MASTER_SPECIFICATION.md)

### 1.2 Domain Mission & Business Objectives
The project builds an enterprise-grade cloud analytical platform to ingest, cleanse, conform, and analyze multi-source United States industrial energy infrastructure data. Historically, electrical generation, smokestack flue-gas pollution, and meteorological data have operated in isolated silos across federal regulatory bodies:
1. **U.S. Energy Information Administration (EIA):** Collects facility-level generator inventories, operating statuses, monthly fuel consumption, net generation, and balancing authority grid telemetry.
2. **U.S. Environmental Protection Agency (EPA):** Monitors continuous emissions from individual smokestack units (CEMS) measuring hourly gross load, heat input, and emissions ($\text{CO}_2$, $\text{SO}_2$, $\text{NO}_x$).
3. **National Oceanic and Atmospheric Administration (NOAA NCEI):** Records synoptic surface weather observations (hourly ambient temperature, wind speed, pressure, dew point).

**Core Business & Analytical Questions:**
* What is the empirical thermodynamic heat rate (efficiency in Btu/kWh) across different generating technologies (Combined Cycle vs. Peakers vs. Coal Steam Turbines) under varying load conditions?
* How do extreme climatic stress events (e.g., Winter Storm Uri 2021, Winter Storm Elliott 2022, 2023–2024 summer heatwaves) impact regional grid demand, reserve margins, and emissions intensity?
* How does the auxiliary load ratio ($\text{Gross Load} - \text{Net Generation}$) vary between baseload coal scrubbers and gas turbines?

---

## 2. Alignment with Course Requirements & 11-Stage Architecture

The project maps directly to the official university syllabus ([`01_Project_Documentation/course_requirements/README.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/01_Project_Documentation/course_requirements/README.md)). While the course syllabus presents a conceptual retail scenario ("CampusCart"), this project substitutes an industrial climate dataset while maintaining an exact 1-to-1 correspondence with the mandated 11-stage pipeline architecture:

| Stage # | Course Pipeline Component | Project Implementation in Databricks Lakehouse | Project Artifact Reference |
| :---: | :--- | :--- | :--- |
| **1** | **Multiple Data Sources** | 6 heterogeneous federal sources (EIA-860, EIA-923, EIA-930, EPA CAMPD, EPA-EIA Crosswalk, NOAA ISD). | [`03_ETL/config.py#L88-L143`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L88-L143) |
| **2** | **Pipeline Orchestration** | Sequenced Databricks Serverless Python notebooks: Ingest $\to$ Validate $\to$ Conformed Silver $\to$ Star Schema Facts $\to$ Marts $\to$ Audit. | [`DATABRICKS_SERVERLESS_ARCHITECTURE.md#L248-L254`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md#L248-L254) |
| **3** | **Bronze Layer (Landing)** | Immutable append-only Delta tables with ingestion metadata (`batch_id`, `ingested_at`) fed from Unity Catalog Volume. | [`03_ETL/config.py#L56-L66`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L56-L66), [`archived/early_sql_drafts/staging.sql#L51-L134`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L51-L134) |
| **4** | **Data Quality & Quarantine** | Rejection rules routing dirty data (sentinels `"."`, `"NM"`, `-9999`, heat rate violations) to dead-letter table `quarantine.rejected_records`. | [`03_ETL/config.py#L341-L356`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L341-L356), [`archived/early_sql_drafts/quality_checks.sql#L1-L84`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/quality_checks.sql#L1-L84) |
| **5** | **Silver Layer (Conformance)** | Deduplicated ORISPL plant codes, standardized physical units (MWh, MMBtu, lbs, tons), spatial Haversine joins. | [`03_ETL/config.py#L42`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L42), [`PROJECT_BLUEPRINT.md#L220-L226`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L220-L226) |
| **SCD** | **SCD Processing** | SCD Type 1 for plant metadata updates; SCD Type 2 for generator operational status (`Operating` $\to$ `Standby` $\to$ `Retired`) with `valid_from`, `valid_to`, `is_current`. | [`PROJECT_BLUEPRINT.md#L152-L159`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L152-L159), [`archived/early_sql_drafts/warehouse.sql#L61-L74`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L61-L74) |
| **6** | **Dimensional Warehouse** | Kimball Star Schema: 5 conformed dimensions + 3 multi-grain fact tables (Transactional, Periodic Snapshot, Aggregate Grid). | [`PROJECT_BLUEPRINT.md#L115-L181`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L115-L181), [`archived/early_sql_drafts/warehouse.sql#L1-L141`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L1-L141) |
| **7** | **Warehouse Performance** | Delta Lake Liquid Clustering (`CLUSTER BY`), eliminating legacy partitioning and manual Z-order optimizations. | [`03_ETL/config.py#L7`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L7), [`archived/early_sql_drafts/warehouse.sql#L108-L141`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L108-L141) |
| **8** | **Gold Layer (Marts)** | Materialized reporting views in `gold_marts` (`vw_emissions_intensity`, `vw_plant_performance`, `vw_grid_stress`). | [`archived/early_sql_drafts/Views.sql#L1-L115`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/Views.sql#L1-L115) |
| **9** | **Analytics & BI** | Analytical SQL queries (`GROUP BY CUBE`, `GROUP BY ROLLUP`, window functions `LAG`/`LEAD`) + 3-Page Power BI report. | [`archived/early_sql_drafts/OLAP.sql#L1-L74`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/OLAP.sql#L1-L74) |
| **10** | **Audit & Reconciliation** | Automated pipeline audit table (`bronze_staging.etl_run_log`) logging execution times, rows read/inserted/rejected, and thermodynamic energy balance checks. | [`03_ETL/config.py#L321-L340`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L321-L340), [`PROJECT_BLUEPRINT.md#L213-L219`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L213-L219) |
| **11** | **Metadata & Governance** | Unity Catalog 3-tier namespace (`dwbi_catalog`), data dictionary, column contracts, and lineage tracing. | [`03_ETL/config.py#L32-L66`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L32-L66), [`01_Project_Documentation/Data_Dictionary.xlsx`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/01_Project_Documentation/Data_Dictionary.xlsx) |

---

## 3. Repository Structure & Artifact Classification

### 3.1 Workspace Directory Tree
```
d:\Semester Projects\DWBI LAB Project\
├── .agents                                      # Operational directives & file access restrictions
├── .gitignore                                   # Version control exclusion rules
├── DATABRICKS_SERVERLESS_ARCHITECTURE.md        # Master Databricks Cloud Lakehouse architecture
├── PROJECT_BLUEPRINT.md                         # Master Kimball DW blueprint & domain logic
├── README.md                                    # Repository overview & team division of work
│
├── 01_Project_Documentation/
│   ├── Architecture.pdf / Architecture.png      # High-resolution pipeline architecture diagram
│   ├── Data_Dictionary.xlsx                     # Complete 7-tab enterprise data dictionary
│   ├── DATA_SOURCES_MASTER_SPECIFICATION.md     # 633-line federal data source catalog & schemas
│   ├── README.md                                # Documentation directory index
│   ├── Requirements.md                          # Phase 1 requirements summary
│   ├── Requirements.pdf                         # Formal Phase 1 requirements submission
│   ├── Schema.pdf / Schema.png                  # Visual Star Schema entity-relationship diagram
│   ├── schema_diagram_mermaid.md                # Verified Mermaid diagram code for Draw.io
│   ├── course_requirements/                     # MANDATORY: Official syllabus & grading rubrics
│   │   ├── DWBI Final Project Overview.pdf
│   │   ├── DWBI Lab Phase 2.pdf
│   │   ├── DWBI Lab Phase 3.pdf
│   │   ├── README.md
│   │   └── Sample Project Architecture Diagram.png
│   └── Team_Guides/                             # PROHIBITED: Binary .docx coordination guides
│       ├── 01_Project_Introduction_and_Overview.docx
│       ├── 02_Data_Sources_and_Connections_Guide.docx
│       └── 03_Technical_Data_Engineering_Deep_Dive.docx
│
├── 02_Data/
│   ├── cleaned_data/
│   │   └── README.txt                           # Storage directory description for cleaned data
│   └── raw_data/
│       └── README.txt                           # Storage directory description for raw archives
│
├── 03_ETL/
│   ├── __pycache__/
│   │   └── config.cpython-314.pyc               # Python 3.14 bytecode cache
│   └── config.py                                # ⭐ MASTER LAKEHOUSE CONFIG & CATALOG SETUP
│
├── 05_Analytics/                                # Target directory for analytical SQL & OLAP scripts
│
├── archived/                                    # Historical artifacts & exploratory scripts
│   ├── early_sql_drafts/                        # Standalone SQL drafts for Databricks Lakehouse
│   │   ├── OLAP.sql                             # Analytical OLAP queries (CUBE, ROLLUP, LAG)
│   │   ├── quality_checks.sql                   # Data quality & quarantine DML queries
│   │   ├── staging.sql                          # Bronze staging & quarantine DDL
│   │   ├── Views.sql                            # Gold reporting marts view DDL
│   │   └── warehouse.sql                        # Kimball Star Schema dimensions & facts DDL
│   ├── Phase_1_Submission/                      # Formal academic Phase 1 package (APA 7th)
│   │   ├── Architecture.pdf / Architecture_Pipeline_Diagram.png
│   │   ├── Data_Dictionary.xlsx
│   │   ├── Phase_1_Architecture_and_Schema_Specification.md
│   │   ├── Phase_1_Data_Dictionary.md
│   │   ├── Phase_1_Executive_Summary_and_Checklist.md
│   │   ├── Phase_1_Project_Execution_Plan.md
│   │   ├── Phase_1_Project_Proposal_and_Design_Document.md
│   │   ├── Requirements.pdf
│   │   └── Schema.pdf / Schema_Diagram.jpg
│   └── scratch_api_tests/                       # Exploratory scraper tests & micro-samples
│       ├── fetch_and_save_samples.py            # Micro-scraper for EPA, Crosswalk, NOAA, EIA
│       ├── fetch_remaining_sources.py           # Micro-scraper for EIA-860, EIA-923, ISD history
│       └── sample_data/                         # Preserved micro-sample files for Plant 3 (Barry)
│           ├── sample_eia860_enviro_assoc.csv
│           ├── sample_eia860_generator.csv
│           ├── sample_eia860_plant.csv
│           ├── sample_eia923_monthly_generation.csv
│           ├── sample_eia930_hourly_grid.json
│           ├── sample_epa_eia_crosswalk.csv
│           ├── sample_epa_hourly_emissions.json
│           ├── sample_noaa_isd_station_history.csv
│           └── sample_noaa_isd_weather.json
│
└── technical-knowledge/                         # 🧠 THIS KNOWLEDGE BASE REPOSITORY
    ├── PROJECT_PROFILE.md
    ├── ENVIRONMENT.md
    ├── IMPLEMENTED_TECHNOLOGIES.md
    ├── DEPENDENCY_MAP.md
    ├── COMPATIBILITY_BASELINE.md
    ├── OFFICIAL_SOURCES.md
    ├── CHANGE_HISTORY.md
    └── KNOWLEDGE_AUDIT.md                       # Comprehensive independent technical audit report
```

### 3.2 Granular Status Classification of Components

| Component / File Path | Implementation Status | Technical Role & Description |
| :--- | :---: | :--- |
| `03_ETL/config.py` | **Implemented** | Master Python/Databricks configuration module. Defines catalog parameters, temporal parameters (2021–2024), endpoint URLs, data quality sentinels/heat-rate bounds, Kimball pruning matrix, path generators, and the idempotent environment initialization routine `init_databricks_environment(spark_session)`. |
| `.agents` | **Implemented** | Operational directive defining mandatory file scan boundaries (prohibits parsing binary `Team_Guides/`), canonical lakehouse architecture, and team work package ownership. |
| `DATABRICKS_SERVERLESS_ARCHITECTURE.md` | **Implemented** | Master technical runbook for Databricks Serverless Compute, Serverless SQL Warehouse, Unity Catalog structure, and Power BI DirectQuery integration. |
| `PROJECT_BLUEPRINT.md` | **Implemented** | Authoritative Kimball dimensional model, mathematical thermodynamic formulas, and physical validation algorithms. |
| `01_Project_Documentation/DATA_SOURCES_MASTER_SPECIFICATION.md` | **Implemented** | Exhaustive technical specification of the 6 primary data sources, attribute definitions, and relational joins. |
| `01_Project_Documentation/schema_diagram_mermaid.md` | **Implemented (Legacy Artifacts Present)** | Mermaid ER diagram specification for rendering Star Schema in Draw.io. *Audit Alert:* Contains legacy discrepancies (declares surrogate keys as `int` rather than Delta's mandatory `BIGINT`, labels facts as "Partitioned" instead of Liquid Clustered, and uses legacy PostgreSQL schema names; see `KNOWLEDGE_AUDIT.md`). |
| `archived/early_sql_drafts/` (`staging.sql`, `warehouse.sql`, `quality_checks.sql`, `Views.sql`, `OLAP.sql`) | **Partially Implemented (Drafted)** | Valid Databricks SQL DDL/DML scripts covering schemas, dimensions, facts with Liquid Clustering, quarantine rules, reporting views, and OLAP queries. Currently stored as standalone scripts, awaiting porting into modular PySpark notebooks. |
| Planned Notebooks: `01_bronze_ingestion.py`, `02_silver_cleansing_and_scd.py`, `03_gold_star_schema_facts.py`, `04_gold_reporting_marts.py` | **Planned** | Operational Databricks PySpark notebooks specified in `DATABRICKS_SERVERLESS_ARCHITECTURE.md` Section 7 Step 3 to execute automated batch extraction and transformation. |
| Power BI Report (`06_Dashboard/PowerBI.pbix`) | **Planned** | 3-page interactive visual dashboard connecting live to Databricks Serverless SQL Warehouse via Native DirectQuery. |
| `05_Analytics/` | **Planned** | Target folder for analytical query scripts and performance tuning benchmarks. |
| `02_Data/raw_data/` & `02_Data/cleaned_data/` | **Planned (Storage Target)** | Local filesystem fallback landing zones for raw archives and cleaned outputs. |
| `archived/scratch_api_tests/` (`fetch_and_save_samples.py`, `fetch_remaining_sources.py`) | **Archived / Experimental** | Early Python scripts used to test REST endpoints and scrape micro-samples for Plant 3 (Barry). Superseded by Databricks Volume ingestion architecture. |
| `archived/scratch_api_tests/sample_data/` | **Archived (Sample Data)** | Micro-sample files (CSVs and JSONs) validating the schema of raw data feeds. |
| `archived/Phase_1_Submission/` | **Archived (Historical Baseline)** | Preserved academic Phase 1 submission artifacts conforming to university grading specifications. |
| `01_Project_Documentation/Team_Guides/` | **Prohibited from AI Parsing** | Binary `.docx` team coordination documents intended exclusively for human collaboration. Prohibited by `.agents`. |
| Legacy PostgreSQL Schema References (`project_staging`, `project_dw`, `project_reporting`) | **Legacy / Compatibility Aliases** | References from early course templates. Superseded by Databricks Lakehouse schemas, but preserved in `config.py["COURSE_SCHEMA_ALIASES"]` for university grading script compatibility. |

