# Technical Compatibility Baseline & Contradiction Detection Matrix

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Senior Data Engineers, Cloud Architects, Automated Compatibility Monitors  
**Purpose:** Systematically detect future breaking changes, runtime contradictions, deprecations, and platform incompatibilities across the project's implemented APIs and architectural patterns.

---

## 1. Executive Summary & Verification Methodology

This document establishes the verified compatibility baseline for all technologies, APIs, SQL constructs, storage configurations, and governance patterns discovered in the codebase.

Each baseline record follows an 8-point inspection contract:
1. **Implemented Feature / API:** The exact technology or construct implemented.
2. **Project Code Location:** Exact file path and line numbers.
3. **Architectural Rationale:** Why this technology is used in the project.
4. **Supported Environments & Version Baseline:** Verified versions supporting the feature without degradation.
5. **Incompatibility Triggers & Breaking Changes:** What environmental, syntactic, or platform changes will cause runtime failures.
6. **Contradiction Detection Rule:** The exact logical condition signaling that a contradiction has occurred.
7. **Documentation Monitoring Target:** Official vendor documentation and release notes that must be tracked.
8. **Compatible Replacement:** The exact syntax, pattern, or alternative API if the current implementation becomes deprecated or incompatible.

---

## 2. Granular Technology Compatibility Profiles

### 2.1 Unity Catalog 3-Tier Namespace & DDL
* **Implemented Feature:** `CREATE CATALOG IF NOT EXISTS` and 3-tier table addressing (`catalog.schema.table`).
* **Project Code Location:**
  * [`03_ETL/config.py#L32-L37`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L32-L37)
  * [`03_ETL/config.py#L298-L300`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L298-L300)
  * [`archived/early_sql_drafts/staging.sql#L9-L10`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L9-L10)
  * [`archived/early_sql_drafts/warehouse.sql#L9-L10`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L9-L10)
* **Architectural Rationale:** Centralizes governance, column-level lineage, identity assignment, and access control under `dwbi_catalog`, isolating bronze, silver, gold, and quarantine assets.
* **Supported Environments & Version Baseline:**
  * Databricks Runtime (DBR) 11.3 LTS+ (Basic UC), DBR 13.3 LTS+ (Full UC feature set), Databricks Serverless Compute, Databricks Serverless SQL Warehouse.
  * Workspace must be attached to an active Unity Catalog metastore.
* **Incompatibility Triggers & Breaking Changes:**
  1. Workspace runs on legacy Hive Metastore without Unity Catalog metastore assignment.
  2. Executing user lacks `CREATE CATALOG` privilege on the metastore.
  3. Running on non-Databricks open-source Apache Spark without Unity Catalog integration.
* **Contradiction Detection Rule:**
  * *Trigger:* Error `CATALOG_NOT_FOUND` or `PERMISSION_DENIED: User does not have CREATE CATALOG on Metastore`.
* **Documentation Monitoring Target:**
  * Databricks Unity Catalog Guide: [What is Unity Catalog?](https://docs.databricks.com/data-governance/unity-catalog/index.html)
* **Compatible Replacement:**
  * If Unity Catalog is unavailable, fall back to 2-tier namespace in the default catalog:
    ```sql
    -- Legacy 2-tier fallback pattern implemented in config.py
    USE CATALOG hive_metastore; -- or default catalog
    CREATE SCHEMA IF NOT EXISTS bronze_staging;
    ```
    *(Handled automatically via `CATALOG_CONFIG["USE_UNITY_CATALOG"] = False` in `03_ETL/config.py#L303-L310`)*.

---

### 2.2 Unity Catalog Volumes (`CREATE VOLUME`) & File Access
* **Implemented Feature:** `CREATE VOLUME IF NOT EXISTS` and POSIX file system access via `/Volumes/...` paths.
* **Project Code Location:**
  * [`03_ETL/config.py#L56-L59`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L56-L59)
  * [`03_ETL/config.py#L315-L319`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L315-L319)
  * [`archived/early_sql_drafts/staging.sql#L16`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/staging.sql#L16)
* **Architectural Rationale:** Provides a high-performance landing zone for non-tabular raw files (EIA multi-tab Excel files, EPA bulk CSVs, NOAA weather files) with unified POSIX and Spark DataFrame access.
* **Supported Environments & Version Baseline:**
  * Databricks Runtime 13.3 LTS+, Databricks Serverless Compute, Databricks Serverless SQL Warehouse.
  * Supported on AWS S3, Azure ADLS Gen2, and Google Cloud Storage via Unity Catalog.
* **Incompatibility Triggers & Breaking Changes:**
  1. Legacy DBR versions (< 13.3 LTS) do not recognize `CREATE VOLUME` syntax.
  2. Workspace without Unity Catalog (Volumes are strictly a Unity Catalog governance object; they do not exist in Hive Metastore).
  3. FUSE mount latency or missing `/Volumes` mount on non-Databricks Spark clusters.
* **Contradiction Detection Rule:**
  * *Trigger:* Error `PARSE_SYNTAX_ERROR: mismatched input 'VOLUME'` or `PATH_NOT_FOUND: /Volumes/...`.
* **Documentation Monitoring Target:**
  * Databricks Volumes Guide: [Create and work with volumes](https://docs.databricks.com/volumes/index.html)
* **Compatible Replacement:**
  * On classic clusters without Unity Catalog Volumes, files must land on DBFS or cloud bucket mounts:
    ```python
    raw_path = "dbfs:/mnt/dwbi_landing/raw_files/"
    df = spark.read.format("csv").load(raw_path)
    ```

---

### 2.3 Identity Columns (`GENERATED ALWAYS AS IDENTITY`)
* **Implemented Feature:** Surrogate key auto-incrementing integers (`BIGINT GENERATED ALWAYS AS IDENTITY`).
* **Project Code Location:**
  * [`03_ETL/config.py#L325`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L325) (`etl_run_log.run_id`)
  * [`03_ETL/config.py#L345`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L345) (`quarantine.rejected_records.rejection_id`)
  * [`archived/early_sql_drafts/warehouse.sql#L35`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L35) (`dim_balancing_authority.ba_key`)
  * [`archived/early_sql_drafts/warehouse.sql#L45`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L45) (`dim_plant.plant_key`)
  * [`archived/early_sql_drafts/warehouse.sql#L63`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L63) (`dim_generator.generator_key`)
  * [`archived/early_sql_drafts/warehouse.sql#L78`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L78) (`dim_weather_station.station_key`)
  * [`archived/early_sql_drafts/warehouse.sql#L112`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L112) (`fact_monthly_plant_operations.snapshot_key`)
* **Architectural Rationale:** Automatically assigns unique, monotonic surrogate keys for Kimball star schema dimensions and periodic snapshot facts without distributed shuffles.
* **Supported Environments & Version Baseline:**
  * Delta Lake 2.2.0+, Databricks Runtime 10.4 LTS+, Databricks Serverless Compute, Databricks Serverless SQL Warehouse.
  * Supported data type: `BIGINT` only.
* **Incompatibility Triggers & Breaking Changes:**
  1. **MERGE INTO UPDATE SET * HAZARD:** In `dim_generator` (SCD Type 2), attempting to execute `MERGE INTO ... WHEN MATCHED THEN UPDATE SET *` will fail because Delta attempts to overwrite the immutable identity column. It must be written as `WHEN MATCHED THEN UPDATE SET * EXCEPT (generator_key)` or explicitly list non-identity target columns.
  2. **SOURCE DATA WITH IDENTITY COLUMN IN INSERT *:** If the incoming source DataFrame schema contains an identity column and attempts to insert explicit values into a `GENERATED ALWAYS` column, Delta Lake throws `DELTA_IDENTITY_COLUMNS_EXPLICIT_INSERT_NOT_SUPPORTED`.
  3. **DEFAULT SURROGATE KEY INSERTION PROHIBITION:** In Kimball modeling, inserting a default record with surrogate key `-1` (representing "Unknown / Not Applicable" for non-thermal plants) will **fail** because `GENERATED ALWAYS` rejects manual key overrides.
  4. **CONCURRENT WRITES:** Delta tables with identity columns do NOT support concurrent append transactions; writes must be strictly serialized.
  5. **CTAS PROHIBITION:** Identity column syntax cannot be specified inside `CREATE TABLE AS SELECT` (CTAS) queries.
* **Contradiction Detection Rule:**
  * *Trigger 1:* `DELTA_IDENTITY_COLUMNS_EXPLICIT_INSERT_NOT_SUPPORTED: Providing values for GENERATED ALWAYS AS IDENTITY column is not supported.`
  * *Trigger 2:* Attempting to seed surrogate key `-1` fails with value rejection.
* **Documentation Monitoring Target:**
  * Databricks Delta Documentation: [Use identity columns in Delta Lake](https://docs.databricks.com/delta/identity-columns.html)
* **Compatible Replacement:**
  * Switch from `GENERATED ALWAYS` to `GENERATED BY DEFAULT AS IDENTITY`:
    ```sql
    -- Compatible syntax allowing default row (-1) seeding and explicit bypass:
    CREATE TABLE gold_warehouse.dim_plant (
        plant_key BIGINT GENERATED BY DEFAULT AS IDENTITY,
        orispl_code INT NOT NULL,
        ...
    ) USING DELTA;
    ```
  * In `MERGE INTO` operations, explicitly exclude the identity column from `UPDATE` clauses:
    ```sql
    -- Databricks SQL / DBR 12.2+ syntax:
    WHEN MATCHED THEN UPDATE SET * EXCEPT (generator_key)
    -- Or explicit assignment:
    WHEN MATCHED THEN UPDATE SET target.operating_status = source.operating_status, target.valid_to = source.valid_to
    ```

---

### 2.4 Liquid Clustering (`CLUSTER BY`)
* **Implemented Feature:** Multi-dimensional automated storage layout optimization (`CLUSTER BY`).
* **Project Code Location:**
  * [`03_ETL/config.py#L7`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L7)
  * [`archived/early_sql_drafts/warehouse.sql#L108`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L108) (`CLUSTER BY (date_key, plant_key)`)
  * [`archived/early_sql_drafts/warehouse.sql#L124`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L124) (`CLUSTER BY (month_start_date_key, plant_key)`)
  * [`archived/early_sql_drafts/warehouse.sql#L141`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L141) (`CLUSTER BY (date_key, ba_key)`)
* **Architectural Rationale:** Replaces legacy table partitioning (`PARTITIONED BY`) and manual Z-order sorting. Prevents small-file over-partitioning while providing sub-second partition pruning and data skipping for Power BI DirectQuery visual filtering.
* **Supported Environments & Version Baseline:**
  * Databricks Runtime 13.3 LTS (Preview), Databricks Runtime 14.1+ (Generally Available), Databricks Serverless Compute, Databricks Serverless SQL Warehouse, Delta Lake 3.1+.
* **Incompatibility Triggers & Breaking Changes:**
  1. Attempting to use both `PARTITIONED BY` and `CLUSTER BY` on the same table throws a syntax error.
  2. Specifying more than 4 clustering columns degrades write performance.
  3. Reading liquid-clustered Delta tables with older, un-upgraded Delta Lake readers (< Delta 3.0) throws protocol incompatibility error (`Table requires feature: domainMetadata or clustering`).
* **Contradiction Detection Rule:**
  * *Trigger:* Error `Cannot specify both PARTITIONED BY and CLUSTER BY` or reader failure `DELTA_UNSUPPORTED_FEATURES_IN_READ`.
* **Documentation Monitoring Target:**
  * Databricks Liquid Clustering Guide: [Use liquid clustering for Delta tables](https://docs.databricks.com/delta/clustering.html)
* **Compatible Replacement:**
  * On older engines lacking Liquid Clustering support, fall back to standard Delta partitioning or Z-Ordering:
    ```sql
    CREATE TABLE gold_warehouse.fact_hourly_emissions_weather (...)
    USING DELTA
    PARTITIONED BY (date_key);
    
    OPTIMIZE gold_warehouse.fact_hourly_emissions_weather ZORDER BY (plant_key);
    ```

---

### 2.5 Informational vs. Enforced Constraints
* **Implemented Feature:** Explicit DDL Primary Key informational constraints on dimensions, alongside enforced `NOT NULL` constraints in audit tables.
* **Project Code Location:**
  * Dimension Primary Keys: [`archived/early_sql_drafts/warehouse.sql#L30-L86`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L30-L86) (`pk_dim_date`, `pk_dim_ba`, `pk_dim_plant`, `pk_dim_generator`, `pk_dim_station`)
  * Enforced NOT NULL columns: [`03_ETL/config.py#L326-L352`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L326-L352) (`batch_id STRING NOT NULL`, `rejection_reason STRING NOT NULL`, etc.)
* **Architectural Rationale:** Documents dimensional relationships for data modeling tools, Power BI semantic modeling, and enables Catalyst query optimizer join elimination, while strictly blocking nulls in audit logs.
* **Supported Environments & Version Baseline:**
  * Databricks Runtime 13.3 LTS+, Generally Available in DBR 15.2+, Databricks Serverless SQL Warehouse.
  * Informational PK/FK supported **only** on Delta tables registered in Unity Catalog.
  * Enforced constraints (`NOT NULL`, `CHECK`) supported across Delta Lake (writer protocol version 3+).
* **Incompatibility Triggers & Breaking Changes:**
  1. **INFORMATIONAL NATURE OF PK/FK:** In Unity Catalog, Primary Key and Foreign Key constraints are **informational only and are NOT enforced upon insertion**. The engine will NOT reject duplicate primary keys or orphaned foreign keys.
  2. **FOREIGN KEYS MISSING IN SQL DDL:** Code inspection reveals that while `PROJECT_BLUEPRINT.md` and `schema_diagram_mermaid.md` describe Foreign Keys, `warehouse.sql` contains **zero Foreign Key DDL statements**.
  3. **STRICT ENFORCEMENT OF NOT NULL:** Delta Lake actively enforces `NOT NULL`. Inserting a null into `batch_id` or `rejection_reason` causes the entire transaction to abort immediately.
  4. Defining PK/FK constraints on tables in legacy Hive Metastore will fail with a syntax error.
* **Contradiction Detection Rule:**
  * *Trigger 1:* Pipeline code assumes the database engine will prevent duplicate business keys or invalid FK references, resulting in undetected dirty data entering gold fact tables.
  * *Trigger 2:* Ingestion pipeline attempts to insert a NULL into a `NOT NULL` audit column, aborting the write batch.
* **Documentation Monitoring Target:**
  * Databricks Constraints Guide: [Constraints on Databricks](https://docs.databricks.com/tables/constraints.html)
* **Compatible Replacement:**
  * Enforce referential integrity and uniqueness programmatically in the Silver layer using `MERGE INTO`, `dropDuplicates()`, and lookup validation queries prior to inserting into Gold tables:
    ```python
    # Defensive software-enforced uniqueness
    silver_df = raw_df.dropDuplicates(["orispl_code", "generator_id"])
    ```

---

### 2.6 Delta Lake Column Default Values
* **Implemented Feature:** Column default expressions (`DEFAULT default_expression`).
* **Project Code Location:**
  * [`03_ETL/config.py#L334`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L334) (`start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP()`)
  * [`03_ETL/config.py#L352`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L352) (`rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()`)
  * [`archived/early_sql_drafts/warehouse.sql#L56`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L56) (`is_combined_heat_power BOOLEAN DEFAULT FALSE`)
  * [`archived/early_sql_drafts/warehouse.sql#L71`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L71) (`valid_to TIMESTAMP DEFAULT TIMESTAMP('9999-12-31 23:59:59')`)
  * [`archived/early_sql_drafts/warehouse.sql#L72`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L72) (`is_current BOOLEAN NOT NULL DEFAULT TRUE`)
* **Architectural Rationale:** Simplifies SCD Type 2 record insertion by automatically establishing open-ended validity horizons (`9999-12-31`) and audit timestamps without requiring application code to inject literals.
* **Supported Environments & Version Baseline:**
  * Delta Lake 3.1+, Databricks Runtime 13.0+, Databricks Serverless Compute, Databricks Serverless SQL Warehouse.
  * Relies on Delta Table Feature `delta.feature.allowColumnDefaults`.
* **Incompatibility Triggers & Breaking Changes:**
  1. Older Spark/Delta readers that do not support Delta 3.1 table features will fail to read tables with column defaults enabled.
  2. Inline `DEFAULT` syntax inside `ALTER TABLE ... ADD COLUMN` is not supported (must add column first, then set default via `ALTER COLUMN ... SET DEFAULT`).
* **Contradiction Detection Rule:**
  * *Trigger:* Error `TABLE_FEATURE_NOT_SUPPORTED` or reader failure on legacy downstream consumers.
* **Documentation Monitoring Target:**
  * Delta Lake Protocol Specifications: [Delta Lake Table Features & Defaults](https://docs.delta.io/latest/delta-column-defaults.html)
* **Compatible Replacement:**
  * If executing on older runtimes, omit `DEFAULT` from DDL and inject default literals explicitly via PySpark `.withColumn()` during DataFrame transformation:
    ```python
    df = df.withColumn("valid_to", F.to_timestamp(F.lit("9999-12-31 23:59:59"))) \
           .withColumn("is_current", F.lit(True))
    ```

---

### 2.7 Databricks Serverless Compute Language & Library Model
* **Implemented Feature:** Serverless Notebook Compute running Python and Spark SQL.
* **Project Code Location:**
  * [`DATABRICKS_SERVERLESS_ARCHITECTURE.md#L14-L20`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md#L14-L20)
  * [`PROJECT_BLUEPRINT.md#L14-L20`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md#L14-L20)
* **Architectural Rationale:** Provides instant startup, zero cluster sizing, automated autoscaling, and Photon acceleration for ELT workloads.
* **Supported Environments & Version Baseline:**
  * Databricks Serverless Notebook Compute track (tracks Apache Spark 3.5+ with Photon).
* **Incompatibility Triggers & Breaking Changes:**
  1. **SCALA & R EXCLUSION:** Attempting to run `%scala` or `%r` cells inside a notebook attached to serverless compute throws an immediate runtime exception.
  2. **MAVEN COORDINATES PROHIBITION:** Cluster-level Maven library installation is not supported on Serverless Compute. Trying to install third-party Spark connectors like `com.crealytics:spark-excel` via Maven coordinates will fail.
  3. **SQL CACHING VS DATAFRAME CACHING:**
     * `CACHE TABLE` / `UNCACHE TABLE` (SQL commands), `spark.catalog.cacheTable()`, and `df.checkpoint()` are **not supported** and throw exceptions.
     * `df.cache()` and `df.persist()` **are supported** starting in Serverless Environment Version 5+, materializing eager session-local cloud disk snapshots (`DISK_ONLY`).
  4. **SPARK INTERNALS ACCESS:** Code accessing internal Spark RDDs (`rdd()`) or non-public Catalyst APIs fails under Spark Connect.
* **Contradiction Detection Rule:**
  * *Trigger 1:* Notebook cell contains `%scala` or SQL `CACHE TABLE`, throwing `FEATURE_UNSUPPORTED_ON_SERVERLESS`.
  * *Trigger 2:* Job configuration attempts to pass raw Maven coordinates.
* **Documentation Monitoring Target:**
  * Databricks Serverless Guide: [Serverless compute limitations](https://docs.databricks.com/compute/serverless/limitations.html)
* **Compatible Replacement:**
  * Use Python exclusively (`%python` or `%sql`).
  * Replace distributed Spark Excel JARs with notebook-scoped Python libraries (`openpyxl` / `pandas` via `%pip install openpyxl`).
  * If caching DataFrames in Serverless Environment v5+, note that storage levels like `MEMORY_ONLY` are ignored and fallback to eager disk snapshots.

---

### 2.8 Local Python 3.14.5 vs Cloud Runtime Mismatch
* **Implemented Feature:** Local configuration inspection using host Python.
* **Project Code Location:**
  * Active workstation interpreter: Python 3.14.5
  * Bytecode cache: [`03_ETL/__pycache__/config.cpython-314.pyc`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/__pycache__/config.cpython-314.pyc)
* **Architectural Rationale:** Facilitates local script execution and parameter validation.
* **Supported Environments & Version Baseline:**
  * Local host Windows environment (Python 3.14.5).
  * Cloud Databricks Serverless Runtime (Python 3.10 / 3.11).
* **Incompatibility Triggers & Breaking Changes:**
  1. `pyspark 3.5.x` supports Python 3.8 to 3.11+; it does NOT officially support Python 3.14.
  2. `databricks-connect` client does NOT have pre-compiled wheels for Python 3.14.
  3. Attempting to run local PySpark unit tests under Python 3.14 will fail during C-extension compilation or Cython import.
* **Contradiction Detection Rule:**
  * *Trigger:* Running `import pyspark` or `from databricks.connect import DatabricksSession` on local workstation throws `ModuleNotFoundError` or build failure.
* **Documentation Monitoring Target:**
  * Apache Spark Python Version Support: [Spark Python Requirements](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
* **Compatible Replacement:**
  * Create a local dedicated virtual environment using **Python 3.10** or **Python 3.11** if local execution via Databricks Connect is required:
    ```bash
    py -3.11 -m venv .venv_dwbi
    .venv_dwbi\Scripts\activate
    pip install databricks-connect>=15.1.0 pandas openpyxl
    ```

---

### 2.9 Power BI Native Databricks Connector (DirectQuery Pushdown)
* **Implemented Feature:** Power BI Desktop Native Connector via DirectQuery over HTTPS/Port 443.
* **Project Code Location:**
  * [`DATABRICKS_SERVERLESS_ARCHITECTURE.md#L102-L115`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md#L102-L115)
  * [`archived/early_sql_drafts/Views.sql#L1-L115`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/Views.sql#L1-L115)
* **Architectural Rationale:** Eliminates local desktop memory limitations by pushing analytical SQL down to the Databricks Serverless SQL Warehouse, querying Delta tables clustered by `(date_key, plant_key)`.
* **Supported Environments & Version Baseline:**
  * Microsoft Power BI Desktop (May 2023 release or newer).
  * Databricks Serverless SQL Warehouse (v2023.50+).
  * Connector: `Databricks.Catalogs` (V2 native connector).
* **Incompatibility Triggers & Breaking Changes:**
  1. Using legacy ODBC/JDBC DSN configurations instead of the native connector.
  2. Writing DAX calculated tables that do not support DirectQuery folding, forcing Power BI to fall back to in-memory import mode.
  3. Passing invalid HTTP paths or hitting firewalled ports (requires port 443 outbound).
* **Contradiction Detection Rule:**
  * *Trigger:* Power BI prompt: `DirectQuery is not supported for this data source or query` or connection timeout on port 443.
* **Documentation Monitoring Target:**
  * Microsoft Power BI Documentation: [Connect to Databricks from Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-databricks)
* **Compatible Replacement:**
  * Ensure all analytical transformations are encapsulated in Databricks views inside `gold_marts` (`vw_emissions_intensity`, `vw_plant_performance`, `vw_grid_stress`), allowing Power BI visuals to issue simple `SELECT ... FROM gold_marts.vw_* WHERE ...` queries.

---

### 2.10 ANSI SQL Mode & Sentinel Value Casting (`TRY_CAST`)
* **Implemented Feature:** Data type casting and numeric sanitization on raw EIA/NOAA inputs containing sentinel strings (`"."`, `"NM"`, `"*"`).
* **Project Code Location:**
  * Sentinel definitions: [`03_ETL/config.py#L152-L155`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L152-L155)
  * Quarantine checks: [`archived/early_sql_drafts/quality_checks.sql#L29-L30`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/quality_checks.sql#L29-L30)
* **Architectural Rationale:** Federal spreadsheets use textual sentinels for missing observations. Cleaned columns must be typed as `DOUBLE` or `DECIMAL` in Delta Lake.
* **Supported Environments & Version Baseline:**
  * Databricks SQL (All versions), Databricks Runtime 14.0+ (ANSI mode enabled by default: `spark.sql.ansi.enabled = true`).
* **Incompatibility Triggers & Breaking Changes:**
  1. In ANSI mode, standard `CAST('.' AS DOUBLE)` throws `CAST_INVALID_INPUT` and aborts the pipeline, unlike legacy Spark which returned `NULL`.
* **Contradiction Detection Rule:**
  * *Trigger:* Error `[CAST_INVALID_INPUT] The value '.' of the type "STRING" cannot be cast to "DOUBLE" because it is malformed.`
* **Documentation Monitoring Target:**
  * Databricks ANSI Mode Reference: [ANSI compliance in Databricks Runtime](https://docs.databricks.com/sql/language-manual/sql-ref-ansi-compliance.html)
* **Compatible Replacement:**
  * Use `TRY_CAST()` which returns `NULL` on invalid format characters without throwing exceptions:
    ```sql
    SELECT TRY_CAST(quantity_january AS DOUBLE) AS net_generation_mwh FROM bronze_staging.raw_eia923...
    ```

---

### 2.11 Serverless Excel File Extraction Architecture
* **Implemented Feature:** Multi-tab Excel file parsing (`.xlsx`) from Unity Catalog Volumes for EIA-860 and EIA-923.
* **Project Code Location:**
  * Dynamic header keys: [`03_ETL/config.py#L100-L110`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L100-L110)
  * Extraction logic: [`archived/scratch_api_tests/fetch_and_save_samples.py#L60-L65`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/scratch_api_tests/fetch_and_save_samples.py#L60-L65)
* **Architectural Rationale:** Federal energy agencies publish annual generator and monthly net generation schedules exclusively as multi-tab `.xlsx` workbooks with shifting header offsets.
* **Supported Environments & Version Baseline:**
  * Python runtime (`openpyxl 3.1.5` / `pandas 3.0.3`) accessing POSIX `/Volumes/...` mount on Databricks Serverless Compute.
* **Incompatibility Triggers & Breaking Changes:**
  1. Attempting to use `spark.read.format("com.crealytics.spark.excel")` fails because Maven coordinates cannot be installed on Serverless Compute.
  2. Large `.xlsx` files (> 50 MB) parsed via `openpyxl` on driver nodes can cause driver Out-Of-Memory (OOM) errors.
* **Contradiction Detection Rule:**
  * *Trigger 1:* `ClassNotFoundException: Failed to find data source: excel`
  * *Trigger 2:* Driver memory exhaustion during `pd.read_excel()` execution.
* **Documentation Monitoring Target:**
  * Databricks Volumes POSIX Access: [Access files in volumes using standard Python file APIs](https://docs.databricks.com/volumes/index.html)
* **Compatible Replacement:**
  * In Serverless notebooks, read from `/Volumes/dwbi_catalog/bronze_staging/raw_landing/...` via `openpyxl` or `pandas` with explicit read chunking, convert to Spark DataFrame via `spark.createDataFrame(pdf)`, and write to Bronze Delta tables.

---

### 2.12 ANSI Timestamp Literal Syntax in DDL
* **Implemented Feature:** Default timestamp values on table definitions (`valid_to`, `start_time`, `rejected_at`).
* **Project Code Location:**
  * [`03_ETL/config.py#L334`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py#L334) (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP()`)
  * [`archived/early_sql_drafts/warehouse.sql#L71`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts/warehouse.sql#L71) (`valid_to TIMESTAMP DEFAULT TIMESTAMP('9999-12-31 23:59:59')`)
* **Architectural Rationale:** Automatically establishes open-ended validity horizons (`9999-12-31`) for SCD Type 2 tracking and audit timestamps.
* **Supported Environments & Version Baseline:**
  * Databricks SQL, Databricks Runtime 13.0+, Delta Lake 3.1+.
* **Incompatibility Triggers & Breaking Changes:**
  1. In strict ANSI mode, writing `TIMESTAMP('...')` with parentheses is parsed as a function invocation, whereas the ANSI SQL standard requires literal syntax `TIMESTAMP 'yyyy-MM-dd HH:mm:ss'`.
* **Contradiction Detection Rule:**
  * *Trigger:* Parse syntax warning or strict ANSI rejection on DDL compilation.
* **Documentation Monitoring Target:**
  * Databricks SQL Language Reference: [Timestamp Type & Literals](https://docs.databricks.com/sql/language-manual/data-types/timestamp-type.html)
* **Compatible Replacement:**
  * Use the ANSI compliant literal syntax without parentheses:
    ```sql
    valid_to TIMESTAMP DEFAULT TIMESTAMP '9999-12-31 23:59:59'
    ```
  * Microsoft Power BI Documentation: [Connect to Databricks from Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-databricks)
* **Compatible Replacement:**
  * Ensure all analytical transformations are encapsulated in Databricks views inside `gold_marts` (`vw_emissions_intensity`, `vw_plant_performance`, `vw_grid_stress`), allowing Power BI visuals to issue simple `SELECT ... FROM gold_marts.vw_* WHERE ...` queries.

