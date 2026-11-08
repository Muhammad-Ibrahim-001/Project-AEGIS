# Implemented Technologies, Frameworks & APIs Catalog

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Data Engineers, Software Architects, Code Reviewers  
**Traceability:** 100% of entries mapped to exact repository files and line numbers  

---

## 1. Technological Taxonomy & Implementation Status

The project codebase spans several distinct technology layers:
1. **Cloud Lakehouse & Data Engine:** Apache Spark, Delta Lake, Unity Catalog, Databricks Serverless.
2. **Data Manipulation & Query APIs:** PySpark DataFrame API, Spark SQL DDL/DML, OLAP SQL constructs.
3. **Python Runtime & Libraries:** Standard library modules, pandas, openpyxl.
4. **Business Intelligence & Reporting:** Power BI Desktop Native Databricks DirectQuery Connector.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          TECHNOLOGY INVENTORY & STATUS SUMMARY                         │
├─────────────────────────┬────────────────────────────────┬─────────────────────────────┤
│ Technology / Feature    │ Primary Role                   │ Implementation Status       │
├─────────────────────────┼────────────────────────────────┼─────────────────────────────┤
│ Unity Catalog           │ 3-Tier Governance & Volumes    │ **Implemented** in config.py│
│ Delta Lake 3.x+         │ Table Storage & ACID Logging   │ **Implemented** in config.py│
│ Identity Columns        │ Surrogate Key Generation       │ **Implemented** in config.py│
│ PySpark SQL Engine      │ Distributed Transformation     │ **Implemented** (Guarded)   │
│ Spark SQL DDL/DML       │ Schema, Table & View Creation  │ **Implemented** & Drafted   │
│ Liquid Clustering       │ Layout & Data Skipping         │ **Drafted** in SQL scripts  │
│ OLAP Aggregations       │ CUBE, ROLLUP, Window Functions │ **Drafted** in SQL scripts  │
│ Python Standard Library │ Config, Typing, REST Requests  │ **Implemented**             │
│ pandas & openpyxl       │ Excel Parsing & Micro-Testing  │ **Implemented** (Archived)  │
│ Databricks DirectQuery  │ Live BI Visual Reporting       │ **Planned / Specified**     │
└─────────────────────────┴────────────────────────────────┴─────────────────────────────┘
```

---

## 2. Granular Technology & API Catalog

### 2.1 Apache Spark & PySpark APIs

#### A. SparkSession Management & Execution Hook
* **Exact Project Location:** [`03_ETL/config.py#L284-L290`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L284-L290), [`03_ETL/config.py#L363-L367`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L363-L367)
* **APIs Used:**
  * `from pyspark.sql import SparkSession`
  * `SparkSession.getActiveSession()`
  * `SparkSession.builder.getOrCreate()`
  * `spark_session.sql(query_string)`
* **Operational Rationale:** Retrieves the live active Spark session within a Databricks notebook cell. If executed outside a Databricks environment (e.g., local Windows workstation without PySpark), catches exceptions defensively to prevent import crashes.
* **Status:** **Implemented**

#### B. Dynamic Spark SQL Query Execution
* **Exact Project Location:** [`03_ETL/config.py#L298-L354`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L298-L354)
* **APIs Used:** `spark_session.sql(...)` executing multi-line DDL statements.
* **Operational Rationale:** Automatically provisions catalog `dwbi_catalog`, schemas, volumes, and audit tables idempotently on startup.
* **Status:** **Implemented**

---

### 2.2 Unity Catalog DDL & Governance APIs

#### A. Catalog & Schema Provisioning
* **Exact Project Location:** [`03_ETL/config.py#L298-L311`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L298-L311), [`archived/early_sql_drafts/staging.sql#L9-L13`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L9-L13)
* **Syntax / Commands:**
  * `CREATE CATALOG IF NOT EXISTS dwbi_catalog`
  * `USE CATALOG dwbi_catalog`
  * `CREATE SCHEMA IF NOT EXISTS dwbi_catalog.bronze_staging`
  * `CREATE SCHEMA IF NOT EXISTS dwbi_catalog.silver_conformed`
  * `CREATE SCHEMA IF NOT EXISTS dwbi_catalog.gold_warehouse`
  * `CREATE SCHEMA IF NOT EXISTS dwbi_catalog.gold_marts`
  * `CREATE SCHEMA IF NOT EXISTS dwbi_catalog.quarantine`
* **Operational Rationale:** Establishes the 3-tier namespace required for data isolation, role-based access control, and medallion architecture.
* **Status:** **Implemented** in `config.py`

#### B. Unity Catalog Volumes (Unstructured Landing)
* **Exact Project Location:** [`03_ETL/config.py#L56-L59`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L56-L59), [`03_ETL/config.py#L315-L319`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L315-L319), [`archived/early_sql_drafts/staging.sql#L16`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L16)
* **Syntax / Commands:**
  * `CREATE VOLUME IF NOT EXISTS dwbi_catalog.bronze_staging.raw_landing`
  * Volume Paths: `/Volumes/dwbi_catalog/bronze_staging/raw_landing` and `/Volumes/dwbi_catalog/bronze_staging/checkpoints`
* **Operational Rationale:** Provides a high-performance landing zone for non-tabular raw files (EIA Excel sheets, EPA bulk CSVs, NOAA weather feeds) accessible via both Spark APIs and standard Python file system calls (`open()`, `openpyxl`).
* **Status:** **Implemented** in `config.py`

#### C. Primary Key Informational Constraints (and Unimplemented Foreign Keys)
* **Exact Project Location:** [`archived/early_sql_drafts/warehouse.sql#L30-L86`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L30-L86)
* **Syntax / Commands (Drafted on Dimensions Only):**
  * `CONSTRAINT pk_dim_date PRIMARY KEY (date_key)`
  * `CONSTRAINT pk_dim_plant PRIMARY KEY (plant_key)`
  * `CONSTRAINT pk_dim_generator PRIMARY KEY (generator_key)`
  * `CONSTRAINT pk_dim_ba PRIMARY KEY (ba_key)`
  * `CONSTRAINT pk_dim_station PRIMARY KEY (station_key)`
* **Operational Rationale:** Documents dimensional entity identity for BI tools and the Spark Catalyst query optimizer.
* **Audit & Implementation Note:** 
  * Primary Keys in Unity Catalog are **informational only** and are not actively enforced during insertion.
  * **Code vs Doc Discrepancy:** While `PROJECT_BLUEPRINT.md` and `schema_diagram_mermaid.md` define Foreign Key relationships, `warehouse.sql` contains **zero Foreign Key constraints** and no Primary Key constraints on the 3 fact tables. Foreign Key DDL remains unauthored.
* **Status:** **Partially Implemented (Dimension PKs Drafted; FKs Unimplemented)**

#### D. Enforced Constraints (`NOT NULL`)
* **Exact Project Location:** [`03_ETL/config.py#L326-L352`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L326-L352) (`batch_id STRING NOT NULL`, `rejection_reason STRING NOT NULL`, `raw_payload_json STRING NOT NULL`, etc.)
* **Syntax / Commands:** `<column_name> <data_type> NOT NULL`
* **Operational Rationale:** Prevents null values from entering mandatory pipeline audit columns and dead-letter quarantine records.
* **Important Behavior:** Unlike Primary Keys, `NOT NULL` constraints are **actively enforced** by Delta Lake on every write operation (`INSERT`, `UPDATE`, `MERGE`), upgrading the table to writer protocol version 3. Transactions abort immediately if a null value is introduced.
* **Status:** **Implemented** in `config.py`

---

### 2.3 Delta Lake 3.x+ Storage & Layout Features

#### A. Table Storage Engine (`USING DELTA`)
* **Exact Project Location:** [`03_ETL/config.py#L337`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L337), [`03_ETL/config.py#L353`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L353), [`archived/early_sql_drafts/staging.sql#L34-L134`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L34-L134)
* **Syntax / Commands:** `CREATE TABLE IF NOT EXISTS ... USING DELTA`
* **Operational Rationale:** Guarantees ACID transactional compliance, schema enforcement, time travel (`VERSION AS OF`), and unified batch/streaming semantics.
* **Status:** **Implemented** in `config.py` and `staging.sql`

#### B. Surrogate Key Generation via Identity Columns
* **Exact Project Location:** [`03_ETL/config.py#L325`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L325), [`03_ETL/config.py#L345`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L345), [`archived/early_sql_drafts/warehouse.sql#L35-L112`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L35-L112)
* **Syntax / Commands:** `BIGINT GENERATED ALWAYS AS IDENTITY`
* **Used On:**
  * `bronze_staging.etl_run_log.run_id`
  * `quarantine.rejected_records.rejection_id`
  * `gold_warehouse.dim_plant.plant_key`
  * `gold_warehouse.dim_generator.generator_key`
  * `gold_warehouse.dim_balancing_authority.ba_key`
  * `gold_warehouse.dim_weather_station.station_key`
  * `gold_warehouse.fact_monthly_plant_operations.snapshot_key`
* **Operational Rationale:** Automatically generates sequential, monotonically increasing synthetic surrogate keys without requiring expensive distributed `ROW_NUMBER()` or window shuffles.
* **Status:** **Implemented** in `config.py` & **Drafted** in `warehouse.sql`

#### C. Liquid Clustering (`CLUSTER BY`)
* **Exact Project Location:** [`archived/early_sql_drafts/warehouse.sql#L108-L141`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L108-L141), [`PROJECT_BLUEPRINT.md#L413-L447`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L413-L447)
* **Syntax / Commands:**
  * `gold_warehouse.fact_hourly_emissions_weather ... CLUSTER BY (date_key, plant_key)`
  * `gold_warehouse.fact_monthly_plant_operations ... CLUSTER BY (month_start_date_key, plant_key)`
  * `gold_warehouse.fact_regional_grid_demand ... CLUSTER BY (date_key, ba_key)`
* **Operational Rationale:** Replaces legacy static hive-style partitioning (`PARTITIONED BY`) and manual `Z-ORDER`. Enables automatic multidimensional data skipping and avoids small-file fragmentation.
* **Status:** **Partially Implemented (Drafted in SQL)**

---

### 2.4 Spark SQL Built-in Functions & Analytical Constructs

#### A. Serialization, UUID & Sanitization Functions
* **Exact Project Location:** [`archived/early_sql_drafts/quality_checks.sql#L27-L80`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/quality_checks.sql#L27-L80)
* **Functions Used:**
  * `to_json(named_struct('key1', val1, ...))`: Serializes rejected raw record payloads into JSON strings for auditing in `quarantine.rejected_records`.
  * `uuid()`: Generates RFC 4122 v4 UUID tokens for audit batch identifiers.
  * `TRIM(column_name)`: Removes leading/trailing whitespace prior to sentinel matching.
  * `CAST(expression AS STRING)`: Explicit type coercion for surrogate identifiers.
* **Status:** **Partially Implemented (Drafted in SQL)**

#### B. Reporting Views in `gold_marts`
* **Exact Project Location:** [`archived/early_sql_drafts/Views.sql#L18-L113`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/Views.sql#L18-L113)
* **Views Defined:**
  1. `gold_marts.vw_emissions_intensity`: Daily/monthly rollups of Gross MW, $\text{CO}_2$, $\text{SO}_2$, $\text{NO}_x$, and $\text{CO}_2$ intensity per MW.
  2. `gold_marts.vw_plant_performance`: Monthly fuel consumption, net generation, delivered fuel cost, and heat rate operational categorizations.
  3. `gold_marts.vw_grid_stress`: Hourly balancing authority demand, forecast residuals, renewable generation totals, and renewable penetration percentages.
* **Functions Used:** `NULLIF()`, `ROUND()`, `AVG()`, `SUM()`, `CASE ... WHEN ... THEN ... ELSE ... END`.
* **Status:** **Partially Implemented (Drafted in SQL)**

#### C. Multi-Dimensional OLAP Aggregations & Window Functions
* **Exact Project Location:** [`archived/early_sql_drafts/OLAP.sql#L14-L72`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/OLAP.sql#L14-L72)
* **Constructs Used:**
  * `GROUP BY CUBE (calendar_year, state_code, energy_source_code)`: Computes all $2^3 = 8$ subtotals and grand totals across year, state, and fuel.
  * `GROUP BY ROLLUP (calendar_year, calendar_quarter, calendar_month, ba_code)`: Computes hierarchical rollups from individual Balancing Authorities up to National Annual totals.
  * `LAG(SUM(net_generation_mwh), 1) OVER (PARTITION BY plant_key ORDER BY calendar_year, calendar_month)`: Computes month-over-month ramp rates and growth percentages.
  * `ORDER BY ... NULLS LAST`: Ensures aggregated subtotal rows appear cleanly at the bottom of result sets.
* **Status:** **Partially Implemented (Drafted in SQL)**

---

### 2.5 Python Standard & Third-Party Libraries

| Library / Module | Import Path | Project File Location | Role & Description | Status |
| :--- | :--- | :--- | :--- | :---: |
| `os` | Standard Library | [`03_ETL/config.py#L24`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L24) | Operating system interactions and directory creation. | Implemented |
| `typing` | Standard Library | [`03_ETL/config.py#L25`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L25) | Type annotations (`Dict`, `List`, `Any`, `Tuple`) enforcing configuration schema contracts. | Implemented |
| `urllib.request` | Standard Library | [`archived/scratch_api_tests/fetch_and_save_samples.py#L1`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L1) | HTTP GET requests to EPA CAMPD, NOAA, and EIA servers with custom request headers. | Archived |
| `json` | Standard Library | [`archived/scratch_api_tests/fetch_and_save_samples.py#L2`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L2) | Parsing and writing REST JSON responses for emissions, weather, and grid telemetry. | Archived |
| `csv` | Standard Library | [`archived/scratch_api_tests/fetch_and_save_samples.py#L3`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L3) | Parsing and writing crosswalk CSV files via `DictReader` and `DictWriter`. | Archived |
| `io` | Standard Library | [`archived/scratch_api_tests/fetch_and_save_samples.py#L4`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L4) | In-memory byte stream handling (`io.BytesIO`) for ZIP file decompression without disk writes. | Archived |
| `zipfile` | Standard Library | [`archived/scratch_api_tests/fetch_and_save_samples.py#L5`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L5) | Unzipping EIA-860 and EIA-923 annual bulk zip packages. | Archived |
| `pandas` | Third-Party (`3.0.3`) | [`archived/scratch_api_tests/fetch_and_save_samples.py#L6`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L6) | Reading Excel files (`pd.read_excel`), filtering plant records, and writing CSVs. | Archived |
| `openpyxl` | Third-Party (`3.1.5`) | Underlying engine for `pd.read_excel` | Parsing `.xlsx` formats for EIA-860 and EIA-923 workbooks. | Archived / Required |

---

### 2.6 Planned Operational Components

* **PySpark Bronze Ingestion Notebook (`01_bronze_ingestion.py`):** Planned notebook to extract bulk files from `/Volumes/dwbi_catalog/bronze_staging/raw_landing` into append-only Delta tables with header discovery.
* **PySpark Silver Conformance Notebook (`02_silver_cleansing_and_scd.py`):** Planned notebook to filter sentinels, perform spatial Haversine matching, route anomalies to `quarantine.rejected_records`, and execute Delta `MERGE INTO` for SCD Type 1 & Type 2.
* **PySpark Gold Warehouse Notebook (`03_gold_star_schema_facts.py`):** Planned notebook to perform surrogate key business lookups and load the 5 conformed dimensions and 3 multi-grain fact tables with Liquid Clustering.
* **PySpark Gold Marts Notebook (`04_gold_reporting_marts.py`):** Planned notebook to define materialized reporting views in `gold_marts`.
* **Microsoft Power BI Desktop (`06_Dashboard/PowerBI.pbix`):** Planned 3-page reporting dashboard connecting directly via Databricks DirectQuery.

