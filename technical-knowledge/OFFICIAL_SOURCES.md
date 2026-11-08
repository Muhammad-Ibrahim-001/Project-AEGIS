# Official Technical Documentation Bibliography & Authority Registry

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Technical Researchers, Data Engineers, System Auditors  
**Governing Standard:** Official Vendor and Government Specifications Only (Zero Unverified Blogs)  

---

## 1. Databricks Platform & Compute Architecture

### 1.1 Databricks Serverless Compute for Notebooks
* **Official Document Title:** Serverless compute for notebooks and jobs
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/compute/serverless/index.html`](https://docs.databricks.com/compute/serverless/index.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks Serverless (Photon Engine / Spark 3.5+)
* **Specific Project Relevance:** Validates the execution environment for `03_ETL/config.py` and planned ETL notebooks. Confirms instant startup, managed auto-scaling, and the Spark Connect architecture.

### 1.2 Databricks Serverless Compute Limitations & Caching
* **Official Document Title:** Serverless compute limitations & DataFrame caching
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/compute/serverless/limitations.html`](https://docs.databricks.com/compute/serverless/limitations.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks Serverless Compute (Environment v5+)
* **Specific Project Relevance:** Establishes critical architectural restrictions: no Scala or R language support, no raw Maven library coordinates, no compute-scoped init scripts, and a 7-day hard execution timeout. Confirms that `df.cache()` and `df.persist()` **are supported** in Serverless Environment Version 5+ (eagerly materializing private cloud disk snapshots `DISK_ONLY`), whereas SQL `CACHE TABLE` remains unsupported.

### 1.3 Databricks Serverless SQL Warehouses
* **Official Document Title:** What is a serverless SQL warehouse?
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/sql/admin/serverless.html`](https://docs.databricks.com/sql/admin/serverless.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks SQL Serverless
* **Specific Project Relevance:** Validates the query execution engine hosting `gold_warehouse` and `gold_marts`, and the endpoint targeted by Power BI DirectQuery over port 443.

---

## 2. Unity Catalog & Storage Specifications

### 2.1 Unity Catalog 3-Tier Namespace & Governance
* **Official Document Title:** What is Unity Catalog?
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/data-governance/unity-catalog/index.html`](https://docs.databricks.com/data-governance/unity-catalog/index.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Unity Catalog (Databricks Runtime 11.3 LTS - 15.4 LTS)
* **Specific Project Relevance:** Authoritative specification for `dwbi_catalog` 3-tier namespace structure (`catalog.schema.table`), fine-grained access control, and column-level lineage tracking.

### 2.2 Unity Catalog Volumes (Unstructured File Storage)
* **Official Document Title:** Create and work with volumes
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/volumes/index.html`](https://docs.databricks.com/volumes/index.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks Runtime 13.3 LTS+ / Serverless
* **Specific Project Relevance:** Confirms the syntax and operational behavior of `CREATE VOLUME IF NOT EXISTS dwbi_catalog.bronze_staging.raw_landing` and POSIX file system path access (`/Volumes/...`).

### 2.3 Unity Catalog Constraints (Enforced vs. Informational)
* **Official Document Title:** Constraints on Databricks
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/tables/constraints.html`](https://docs.databricks.com/tables/constraints.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks Runtime 13.3 LTS+ / DBR 15.2+ (GA)
* **Specific Project Relevance:** Confirms that `CONSTRAINT pk_... PRIMARY KEY` and `FOREIGN KEY` declarations in Unity Catalog are **informational only and not actively enforced** upon insertion. Conversely, `NOT NULL` constraints (such as audit columns in `config.py`) are **actively enforced** on every write operation, upgrading Delta table writer protocol to version 3.

---

## 3. Delta Lake Storage & Layout Optimization

### 3.1 Delta Lake Liquid Clustering
* **Official Document Title:** Use liquid clustering for Delta tables
* **Publishing Entity:** Databricks, Inc. / Delta Lake Project
* **Official URL:** [`https://docs.databricks.com/delta/clustering.html`](https://docs.databricks.com/delta/clustering.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Delta Lake 3.1+ / Databricks Runtime 13.3 LTS (Preview) / DBR 14.1+ (GA)
* **Specific Project Relevance:** Validates the `CLUSTER BY (date_key, plant_key)` clause in `warehouse.sql` and `PROJECT_BLUEPRINT.md`. Confirms replacement of legacy partitioning and `Z-ORDER`.

### 3.2 Delta Lake Identity Columns
* **Official Document Title:** Use identity columns in Delta Lake
* **Publishing Entity:** Databricks, Inc. / Delta Lake Project
* **Official URL:** [`https://docs.databricks.com/delta/identity-columns.html`](https://docs.databricks.com/delta/identity-columns.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Delta Lake 2.2.0+ / Databricks Runtime 10.4 LTS+
* **Specific Project Relevance:** Establishes behavior and strict restrictions of `BIGINT GENERATED ALWAYS AS IDENTITY` on surrogate keys (`plant_key`, `generator_key`, `run_id`). Prohibits manual override during `INSERT` and requires omitting identity columns during Delta `MERGE INTO`.

### 3.3 Delta Lake Column Defaults
* **Official Document Title:** Delta Lake Table Features: Column Defaults
* **Publishing Entity:** Delta Lake Project
* **Official URL:** [`https://docs.delta.io/latest/delta-column-defaults.html`](https://docs.delta.io/latest/delta-column-defaults.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Delta Lake 3.1+ / DBR 13.0+
* **Specific Project Relevance:** Confirms table feature requirements for `TIMESTAMP DEFAULT CURRENT_TIMESTAMP()` and `valid_to TIMESTAMP DEFAULT TIMESTAMP('9999-12-31 23:59:59')`.

---

## 4. Apache Spark & PySpark APIs

### 4.1 Apache Spark SQL Language Reference
* **Official Document Title:** Spark SQL, DataFrames and Datasets Guide
* **Publishing Entity:** Apache Software Foundation
* **Official URL:** [`https://spark.apache.org/docs/latest/sql-programming-guide.html`](https://spark.apache.org/docs/latest/sql-programming-guide.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Apache Spark 3.5.x / 4.0
* **Specific Project Relevance:** Validates Spark SQL syntax, ANSI mode compatibility, and DataFrame operations across all ETL modules.

### 4.2 Built-in Analytical SQL Aggregations (CUBE & ROLLUP)
* **Official Document Title:** Spark SQL Multi-Dimensional Aggregations: CUBE & ROLLUP
* **Publishing Entity:** Apache Software Foundation
* **Official URL:** [`https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-groupby.html`](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-groupby.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Apache Spark 3.0+
* **Specific Project Relevance:** Validates `GROUP BY CUBE (calendar_year, state_code, energy_source_code)` and `GROUP BY ROLLUP (calendar_year, calendar_quarter, calendar_month, ba_code)` implemented in `archived/early_sql_drafts/OLAP.sql`.

### 4.3 Window Aggregate Functions (`LAG`, `LEAD`, `AVG OVER`)
* **Official Document Title:** Window Functions in Spark SQL
* **Publishing Entity:** Apache Software Foundation
* **Official URL:** [`https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html`](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Apache Spark 3.0+
* **Specific Project Relevance:** Validates month-over-month growth calculations (`LAG(SUM(net_generation_mwh), 1) OVER (PARTITION BY plant_key ORDER BY calendar_year, calendar_month)`) in `OLAP.sql`.

### 4.4 Spark Connect Architecture
* **Official Document Title:** Spark Connect Overview
* **Publishing Entity:** Apache Software Foundation
* **Official URL:** [`https://spark.apache.org/docs/latest/spark-connect-overview.html`](https://spark.apache.org/docs/latest/spark-connect-overview.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Apache Spark 3.4+ / 3.5+
* **Specific Project Relevance:** Validates the decoupling of the client notebook from the serverless execution runtime, and the underlying protocol used by `DatabricksSession.builder.serverless()`.

### 4.5 Databricks ANSI SQL Compliance & `TRY_CAST`
* **Official Document Title:** ANSI compliance in Databricks Runtime & `try_cast` function
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/sql/language-manual/sql-ref-ansi-compliance.html`](https://docs.databricks.com/sql/language-manual/sql-ref-ansi-compliance.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks SQL / Databricks Runtime 14.0+
* **Specific Project Relevance:** Confirms that ANSI mode is enabled by default, causing standard `CAST()` on federal string sentinels (`"."`, `"NM"`) to throw `CAST_INVALID_INPUT`. Mandates `TRY_CAST()` for safe numeric coercion.

### 4.6 Databricks SQL Timestamp Data Type & Literals
* **Official Document Title:** Timestamp type & timestamp literal syntax
* **Publishing Entity:** Databricks, Inc.
* **Official URL:** [`https://docs.databricks.com/sql/language-manual/data-types/timestamp-type.html`](https://docs.databricks.com/sql/language-manual/data-types/timestamp-type.html)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Databricks SQL / ANSI Compliance
* **Specific Project Relevance:** Authoritative syntax specification for default column timestamp values, confirming ANSI literal syntax `TIMESTAMP 'yyyy-MM-dd HH:mm:ss'` without function parentheses.

---

## 5. Federal Open Data Sources & Technical Portals

### 5.1 EIA-860: Annual Electric Generator Report
* **Official Agency:** U.S. Energy Information Administration (EIA)
* **Data Portal URL:** [`https://www.eia.gov/electricity/data/eia860/`](https://www.eia.gov/electricity/data/eia860/)
* **Direct Archive Template:** [`https://www.eia.gov/electricity/data/eia860/archive/xls/eia860{year}.zip`](https://www.eia.gov/electricity/data/eia860/archive/xls/)
* **Verification Date:** November 8, 2026
* **Data Horizon:** 2021 – 2024 annual archives
* **Specific Project Relevance:** Source for `dim_plant`, `dim_generator` (SCD Type 2), and `6_1_EnviroAssoc` crosswalk mappings. Validates the Row 2 header offset rule.

### 5.2 EIA-923: Monthly Generation and Fuel Report
* **Official Agency:** U.S. Energy Information Administration (EIA)
* **Data Portal URL:** [`https://www.eia.gov/electricity/data/eia923/`](https://www.eia.gov/electricity/data/eia923/)
* **Direct Archive Template:** [`https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{year}.zip`](https://www.eia.gov/electricity/data/eia923/archive/xls/)
* **Verification Date:** November 8, 2026
* **Data Horizon:** 2021 – 2024 monthly records
* **Specific Project Relevance:** Source for `fact_monthly_plant_operations`. Validates the Row 6 header offset rule, string sentinels (`"."`, `"NM"`), and legitimate negative net generation business events.

### 5.3 EIA-930: Real-Time Hourly Electric Grid Monitor
* **Official Agency:** U.S. Energy Information Administration (EIA)
* **Data Portal URL:** [`https://www.eia.gov/electricity/gridmonitor/`](https://www.eia.gov/electricity/gridmonitor/)
* **Verification Date:** November 8, 2026
* **Data Horizon:** 2021 – 2024 hourly telemetry
* **Specific Project Relevance:** Source for `fact_regional_grid_demand` and `dim_balancing_authority`. Validates hourly demand, forecast demand, and fuel mix dispatch.

### 5.4 EPA CAMPD: Clean Air Markets Program Data (CEMS)
* **Official Agency:** U.S. Environmental Protection Agency (EPA)
* **Portal & Bulk Data Files:** [`https://campd.epa.gov/data/bulk-data-files`](https://campd.epa.gov/data/bulk-data-files)
* **REST Streaming API:** [`https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly`](https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly)
* **Verification Date:** November 8, 2026
* **Data Horizon:** 2021 – 2024 hourly emissions
* **Specific Project Relevance:** Source for `fact_hourly_emissions_weather` ($\text{SO}_2, \text{NO}_x, \text{CO}_2$, Gross MW, and Heat Input MMBtu).

### 5.5 EPA–EIA Crosswalk Bridge
* **Official Agency:** EPA Clean Air Markets Division & EIA Joint Working Group
* **GitHub Repository:** [`https://github.com/USEPA/camd-eia-crosswalk`](https://github.com/USEPA/camd-eia-crosswalk)
* **Raw Master CSV:** [`https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv`](https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv)
* **Verification Date:** November 8, 2026
* **Specific Project Relevance:** Master relational bridge resolving complex many-to-many physical relationships between EPA boiler smokestacks and EIA electric generators.

### 5.6 NOAA ISD: Integrated Surface Database Synoptic Weather
* **Official Agency:** National Oceanic and Atmospheric Administration (NOAA NCEI)
* **Data Portal URL:** [`https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database`](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)
* **Station History CSV:** [`https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv`](https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv)
* **Annual Archives:** [`https://www.ncei.noaa.gov/pub/data/noaa/{year}/`](https://www.ncei.noaa.gov/pub/data/noaa/)
* **Verification Date:** November 8, 2026
* **Specific Project Relevance:** Source for `dim_weather_station` and hourly weather observations joined with emissions facts using spatial Haversine algorithms ($\le 50\text{ km}$).

---

## 6. Business Intelligence & DirectQuery Integration

### 6.1 Microsoft Power BI Native Databricks Connector
* **Official Document Title:** Connect to Databricks from Power BI Desktop
* **Publishing Entity:** Microsoft Corporation
* **Official URL:** [`https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-databricks`](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-databricks)
* **Verification Date:** November 8, 2026
* **Applicable Technology Version:** Power BI Desktop (May 2023+ / 2024+)
* **Specific Project Relevance:** Authoritative guide for DirectQuery connection to Databricks SQL Serverless Warehouses, port 443 HTTPS communication, and Unity Catalog 3-tier hierarchy browsing.

