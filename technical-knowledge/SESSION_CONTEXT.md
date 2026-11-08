# Session Context: U.S. Bulk Power Generation, Emissions & Weather Lakehouse

**Layer:** 1 (Compact Operational Session Summary)  
**Authority:** Derived summary. All primary authoritative specifications reside in Layer 2 documents (`technical-knowledge/*.md`).  
**Integrity Rule:** Verifiable via `python technical-knowledge/scripts/verify_manifest.py`. Update this document ONLY when actual semantic project understanding or technical rules change.

---

## 1. Project Identity & Collaborative Architecture
* **Academic Course:** DL3004 Data Warehousing & Business Intelligence (DWBI), FAST-NUCES, Fall 2026.
* **Domain Mission:** Enterprise cloud data lakehouse integrating U.S. bulk electric generation (EIA-860/923/930), smokestack Continuous Emission Monitoring System (EPA CAMPD), crosswalk topology, and synoptic surface weather (NOAA ISD).
* **4-Person Modular Division of Work:**
  * **WP1 (Ingestion & Bronze Lead):** Muhammad Ibrahim (24L-2602) — Raw Volume landing, dynamic Excel header scanning, Bronze Delta tables, and `bronze_staging.etl_run_log`.
  * **WP2 (Data Quality & Silver Lead):** Rai Fahad Sultan (24L-2509) — Sentinel coercion, dead-letter quarantine (`quarantine.rejected_records`), SCD Type 2 tracking, and DQ PDF Report.
  * **WP3 (DW & Gold Architect):** Muhammad Ayyan (24L-2568) — Kimball Star Schema DDL, surrogate key lookups, 3 multi-grain fact tables, and Liquid Clustering (`CLUSTER BY`).
  * **WP4 (Analytics, OLAP & BI Lead):** Taha Imran (24L-2560) — Materialized reporting views (`gold_marts.vw_*`), OLAP SQL (`ROLLUP`, `CUBE`), and 3-page Power BI Dashboard via DirectQuery.

---

## 2. Canonical Lakehouse Architecture (Cloud Target)
* **Cloud Platform:** Databricks (`databricks.com` on AWS, Azure, or GCP).
* **Processing Engine:** Apache Spark 3.5+ / 4.x on Serverless Notebook Compute (Photon Engine).
* **Warehouse Engine:** Databricks Serverless SQL Warehouse.
* **Table Format & Storage:** Delta Lake (`USING DELTA`) with ACID transaction log and Liquid Clustering.
* **Unified Governance:** Unity Catalog 3-tier namespace (`catalog.schema.table`). Primary Catalog: **`dwbi_catalog`**.
* **BI Connectivity:** Microsoft Power BI Desktop connected via Native Databricks Connector (**DirectQuery** to `dwbi_catalog.gold_marts`).
* **Primary Blueprints:**
  * [`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md): Cloud infrastructure and pipeline execution.
  * [`PROJECT_BLUEPRINT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md): Domain formulas, Kimball dimensional definitions, and schemas.

---

## 3. Unity Catalog Namespace & Storage Structure (`dwbi_catalog`)
* **Volumes:**
  * `/Volumes/dwbi_catalog/bronze_staging/raw_landing/`: Landing zone for raw multi-tab Excel (.xlsx), EPA CAMPD (.csv), NOAA (.csv).
  * `/Volumes/dwbi_catalog/bronze_staging/checkpoints/`: Structured Streaming / Delta checkpoint directory.
* **Schemas & Tables:**
  1. `bronze_staging`: Append-only raw tables (`raw_eia860_*`, `raw_eia923_*`, `raw_epa_*`, `raw_noaa_*`) + `etl_run_log`.
  2. `silver_conformed`: Cleaned entities (`silver_plants_master`, `silver_generators_scd2`, `silver_emissions_cems`, `silver_weather_hourly`).
  3. `gold_warehouse`: Kimball Star Schema:
     * Dimensions: `dim_date` (PK `date_key`), `dim_plant` (PK `plant_key`), `dim_generator` (PK `generator_key`, SCD-2), `dim_balancing_authority` (PK `ba_key`), `dim_weather_station` (PK `station_key`).
     * Facts: `fact_hourly_emissions_weather` (Transactional), `fact_monthly_plant_operations` (Periodic Snapshot), `fact_regional_grid_demand` (Aggregate Grid).
  4. `gold_marts`: Analytical views (`vw_emissions_intensity`, `vw_plant_performance`, `vw_grid_stress`).
  5. `quarantine`: Dead-letter table `quarantine.rejected_records`.

---

## 4. Machine-Specific Local Environment & Approved Team Standard
* **Host Operating System:** Microsoft Windows 11 (AMD64 architecture).
* **Global Python Installation:** **Python 3.14.5** (Default host interpreter; preserved and NOT modified).
* **Databricks CLI:** Version **1.19.0** installed via WinGet (`databricks.exe`).
* **Approved 4-Tier Development Standard (Mandatory for All 4 Members):**
  1. **Remote Serverless Compute Version:** Azure/AWS Databricks **Serverless Environment Version 5** (runs remote Python 3.12.x, Photon engine, Spark Connect gRPC).
  2. **Local Python Interpreter:** **Python 3.12.3** (`py -3.12`) installed in user scope without altering host default Python (3.14.5/3.13.3) or system PATH. Minor-version matches remote serverless container.
  3. **Databricks Connect Package:** **`databricks-connect==18.3.7`** installed in dedicated repository-root **`.venv-dbx`**. Strictly **NO standalone `pyspark` or `delta-spark`** installed.
  4. **Individual Authentication Requirements:** Individual authentication per teammate (OAuth U2M via `databricks auth login` or PAT stored in `~/.databrickscfg`). Strictly **zero credentials or tokens in Git repository**. All table edits and ETL logs attribute immutably to `current_user()`.

---

## 5. Critical Platform Constraints & Engineering Rules
1. **Shifting Excel Headers:** EIA-860 headers are on Row 2; EIA-923 headers are on Row 6. Dynamic scanning for `'Plant Code'` / `'Plant Id'` is standardized in `03_ETL/config.py`.
2. **Missing Value Sentinels & ANSI Mode:** Coerce string sentinels (`"."`, `"NM"`, `"*"`, `""`) and NOAA integer `-9999` to `NULL`. Modern Databricks SQL enables ANSI mode by default; **always use `TRY_CAST()`** to prevent query aborts. Literal syntax requires `TIMESTAMP 'YYYY-MM-DD HH:MM:SS'`.
3. **Negative Net Generation:** Valid business event in EIA-923 caused by offline power plants drawing auxiliary station power during maintenance. Must NEVER be rejected by DQ checks.
4. **Thermodynamic Heat Rate Bounds:** CCGT: 5,000–14,000 Btu/kWh; Coal Steam Turbines: 8,500–18,000 Btu/kWh; Peakers: 9,000–22,000 Btu/kWh. Violations route to `quarantine.rejected_records`.
5. **Auxiliary Reconciliation:** $\text{Net Generation (EIA-923)} \le \text{Gross Generation (EPA CAMPD)}$ with auxiliary load ratios expected between $3\%$ and $14\%$.
6. **Delta Identity Column Merges:** In SCD Type 2 merges, use `UPDATE SET * EXCEPT (identity_col)`. Default surrogate key rows (`-1 = Unknown`) require `GENERATED BY DEFAULT AS IDENTITY`.
7. **Serverless DataFrame Caching:** Supported **only** on **Serverless Environment Version 5+ AND Databricks Connect Python 18.1.8+** (materializes session-local disk snapshot `DISK_ONLY`). SQL `CACHE TABLE` is unsupported.
8. **Python UDF Minor-Version Requirement:** For Python UDF support, official Databricks documentation states that the local client Python minor version must match the remote serverless Python minor version (e.g., local Python 3.12.x to remote Python 3.12.x on Serverless Environments 3 through 6). Ordinary DataFrame and SQL operations transmit Protobuf query plans and do not execute Python bytecode on the server.

---

## 6. Authoritative Layer 2 Cross-Reference Index
Consult these complete documents in [`technical-knowledge/`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge) when working on task-specific areas:

| Task Area | Consult Document | Key Contents |
| :--- | :--- | :--- |
| **SQL DDL, DML & Table Contracts** | [`COMPATIBILITY_BASELINE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/COMPATIBILITY_BASELINE.md) | 8-point compatibility contracts, identity update hazards, ANSI cast rules. |
| **Active Catalog & APIs** | [`IMPLEMENTED_TECHNOLOGIES.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/IMPLEMENTED_TECHNOLOGIES.md) | Line-by-line mapping of `config.py`, Volumes, and table constraints. |
| **Data Lineage & Pipeline Stages** | [`DEPENDENCY_MAP.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/DEPENDENCY_MAP.md) | Federal source to Gold mart data flow and column mappings. |
| **Runtime & Compute Architecture** | [`ENVIRONMENT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/ENVIRONMENT.md) | Databricks Serverless vs classic clusters, local host specifications. |
| **Audit Findings & Nuance Fixes** | [`KNOWLEDGE_AUDIT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/KNOWLEDGE_AUDIT.md) | Verified audit corrections (Env v5+ caching, foreign key omissions). |
| **Vendor & Agency Documentation** | [`OFFICIAL_SOURCES.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/OFFICIAL_SOURCES.md) | Official vendor URLs, version tracking, and government specifications. |
| **Domain Mission & Academic Context**| [`PROJECT_PROFILE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/PROJECT_PROFILE.md) | Research questions, 11-stage course mapping, and team roles. |
| **Commit History & Architecture Log**| [`CHANGE_HISTORY.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/CHANGE_HISTORY.md) | Chronological evolution from PostgreSQL template to Databricks Lakehouse. |

