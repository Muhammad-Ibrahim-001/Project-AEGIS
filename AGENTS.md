# ==============================================================================
# AGENT OPERATIONAL DIRECTIVES & REPOSITORY SPECIFICATION
# Project: U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Technology: Databricks Serverless Cloud Lakehouse (Apache Spark & Delta Lake)
# ==============================================================================

This file contains binding instructions for any AI assistant or autonomous agent
operating within this workspace. Antigravity automatically discovers and loads
this file at the start of every session as a root-level workspace rule.

> **Phased Builder Directive:** Read `PROJECT.md` first. Update it after every unit. Follow its plan and "Current" section.

---

## PART I: MANDATORY SESSION-START REVIEW PROTOCOL (TWO-LAYER KNOWLEDGE ARCHITECTURE)

This protocol is a permanent operating requirement. It applies to **EVERY new conversation/session** before performing any engineering, architecture, debugging, optimization, or technical advisory work, regardless of task complexity.

### 1. Mandatory Two-Layer Knowledge Protocol
At the beginning of every new session:
* **Step 1: Check Manifest Integrity (Layer 2 Verification):**
  * Run the integrity verification script (`python technical-knowledge/scripts/verify_manifest.py`) or inspect [`technical-knowledge/manifest.json`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/manifest.json).
  * **Efficiency Guard:** This verification checks SHA-256 hashes and **avoids loading full document contents into model context during routine integrity checks**.
  * **Integrity vs. Semantics:** SHA-256 confirms byte-level file integrity; it does not confirm semantic correctness.
  * **Non-Silent Integrity Policy:** If all 8 Layer 2 documents match their baseline hashes, proceed to Step 2. If any document is `MODIFIED`, `ADDED`, `DELETED`, or `MISSING`:
    - **HALT** automatic execution and inspect the changed file(s) directly.
    - Never automatically register newly discovered files or accept modified files as a new baseline without inspection.
    - Update [`SESSION_CONTEXT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/SESSION_CONTEXT.md) **only when actual semantic project knowledge changes**.
    - Rebaseline the manifest (`python technical-knowledge/scripts/verify_manifest.py --rebaseline`) only after human or agent review confirms the changes.
* **Step 2: Read Layer 1 Operational Summary:**
  * Read [`technical-knowledge/SESSION_CONTEXT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/SESSION_CONTEXT.md) in full. This provides comprehensive situational awareness of active architecture, Unity Catalog schemas, environment boundaries, and critical domain rules within ~2,000 tokens.
* **Step 3: Consult Layer 2 Authoritative Documents On-Demand (Task-Specific):**
  * Preserve all 8 detailed documents in [`technical-knowledge/`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge) as the authoritative single source of truth.
  * The agent must **NOT** read all Layer 2 documents unconditionally at session start.
  * Instead, read specific complete documents when directly relevant to the current task:
    * Modifying DDL, table constraints, SQL queries, or data types: Read [`COMPATIBILITY_BASELINE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/COMPATIBILITY_BASELINE.md) & [`IMPLEMENTED_TECHNOLOGIES.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/IMPLEMENTED_TECHNOLOGIES.md).
    * Working on data ingestion, pipeline staging, or data lineage: Read [`DEPENDENCY_MAP.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/DEPENDENCY_MAP.md).
    * Configuring compute, local tooling, or Databricks Connect: Read [`ENVIRONMENT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/ENVIRONMENT.md).
    * Resolving domain formulas, heat rates, or syllabus rubric requirements: Read [`PROJECT_PROFILE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/PROJECT_PROFILE.md).
    * Investigating platform edge cases, caching rules, or audit findings: Read [`KNOWLEDGE_AUDIT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/KNOWLEDGE_AUDIT.md).
    * Citing vendor APIs or checking external documentation: Read [`OFFICIAL_SOURCES.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/OFFICIAL_SOURCES.md).
    * Verifying architectural rationale or historical decisions: Read [`CHANGE_HISTORY.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/CHANGE_HISTORY.md).
* **Read Project Instruction & Governance Files:** Read [`AGENTS.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/AGENTS.md) and any `GEMINI.md` files if present.
* **Read Core Architectural Runbooks When Architecting:** Read [`README.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/README.md), [`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md), and [`PROJECT_BLUEPRINT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md).
* **No Reliance on Prior Chat Memory:** Do not rely on prior conversation memory as a substitute for inspecting files.

### 2. Understand the Actual Project
After reviewing the knowledge base:
* **Inspect Repository Structure:** Verify actual directories, scripts, notebooks, and configurations.
* **Inspect Git Status:** Run `git status` to detect uncommitted changes, modified files, and untracked assets.
* **Understand Implemented Architecture:** Verify the active implementation in [`03_ETL/config.py`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/config.py) and drafted SQL in [`archived/early_sql_drafts/`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/archived/early_sql_drafts).
* **Identify Component Dependencies:** Validate upstream/downstream relationships documented in [`DEPENDENCY_MAP.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/DEPENDENCY_MAP.md).
* **Compare Documentation Against Code:** Never assume documentation accurately represents code. Verify actual code contracts (e.g., `warehouse.sql` defines dimension PKs but omits FKs).

### 3. Research-First Engineering
Before implementing or recommending any technical solution:
1. **Identify Affected Technologies & Components:** Map changes to exact modules, schemas, or tables.
2. **Read Implementation Files First:** Read the exact files being modified or referenced.
3. **Consult Authoritative Documentation:** Reference [`OFFICIAL_SOURCES.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/OFFICIAL_SOURCES.md) and official vendor documentation (Databricks, Apache Spark, Delta Lake, Power BI, Python).
4. **Verify Platform Compatibility & Restrictions:**
   * Verify Serverless Compute limitations (no Scala/R, no raw Maven coordinates, 7-day timeout, `df.cache()` disk snapshots supported on Serverless Env 5+ with Connect Python 18.1.8+; SQL `CACHE TABLE` unsupported).
   * Verify Delta Lake identity column rules (`MERGE INTO` requires `UPDATE SET * EXCEPT (identity_col)`).
   * Verify ANSI SQL mode rules (requires `TRY_CAST()` on federal sentinel strings; literal syntax `TIMESTAMP 'YYYY-MM-DD HH:MM:SS'`).
5. **Compare Approaches Against Course Rubric:** Validate solutions against academic grading requirements in [`01_Project_Documentation/course_requirements/`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/01_Project_Documentation/course_requirements).
6. **Prefer Appropriate Over Complex Solutions:** Choose the simplest, robust, standard pattern fitting requirements.
7. **Zero Fabrication:** Never invent documentation, APIs, syntax flags, or compatibility assertions. Cite authoritative sources with version numbers.

### 4. Mandatory Session-Start Report
Before executing the requested engineering task, the agent MUST present a concise report covering:
* **Knowledge files successfully reviewed:** Status of manifest check, confirmation that Layer 1 `SESSION_CONTEXT.md` was read, and any specific Layer 2 documents consulted on-demand.
* **Project documentation reviewed:** Specific architectural runbooks, blueprints, and syllabus rubrics read.
* **Current repository status:** Git branch, clean/dirty working tree, untracked files, and recent commit state.
* **Important technical constraints:** Active runtime boundaries (Serverless environment, Python version mismatch, Delta protocols, ANSI SQL mode).
* **Discrepancies & contradictions discovered:** Any document-code mismatches or conflicting claims identified.
* **Task-specific research status:** Whether additional targeted research is required before implementing the user's specific request.
* **Transparency clause:** If any file cannot be accessed or read, explicitly report it. Never claim to have read a file you did not read.

### 5. No Premature Implementation
* Do not modify code, schemas, or configurations before completing the review and research phases.
* For substantial architectural or implementation changes, present the proposed design, trade-offs, and rationale for approval before writing code.
* Do not modify code merely to make documentation appear consistent without first investigating actual requirements.

### 6. Maintain the Knowledge Base
When an implementation or verified discovery changes the project's technical understanding:
* Update the relevant Layer 2 authoritative knowledge document in `technical-knowledge/`.
* Record all architectural transitions, schema changes, and audit findings in [`CHANGE_HISTORY.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/CHANGE_HISTORY.md).
* Update [`manifest.json`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/manifest.json) after inspecting the changes.
* Update [`SESSION_CONTEXT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/technical-knowledge/SESSION_CONTEXT.md) only if semantic project understanding changes.
* Categorize facts into standard evidentiary tiers: `[REPO-VERIFIED]`, `[DOC-VERIFIED]`, `[TESTED]`, or `[ASSUMPTION / UNVERIFIED]`.
* Record unresolved assumptions, limitations, and platform edge-cases.
* Never silently replace an earlier architectural decision.

### 7. Operating Principles
* This protocol applies unconditionally to every conversation turn that begins a new session.
* Do not bypass or abbreviate the review because a task appears small or simple.
* Focus research on project-relevant technologies; avoid investigating unrelated frameworks.
* If context window or execution limitations prevent completing the required review, halt and explicitly list what remains unread.

---

## PART II: MANDATORY FILE ACCESS RULES

### 1. NEVER READ (STRICTLY PROHIBITED)
Agents must NEVER scan, parse, or read files in the following directory:
* ⛔ `01_Project_Documentation/Team_Guides/`
  * **Reason:** Contains binary Microsoft Word onboarding documents (`.docx`) and scripts intended exclusively for human team coordination. Parsing these files is unnecessary and unhelpful for coding or analysis tasks.
*(Note: Obsolete exploratory research notes in `01_Project_Documentation/research/` have been permanently purged from the repository).*

### 2. ALWAYS READ (MANDATORY GROUND TRUTH)
Before proposing, generating, or modifying any code, schema, query, or report, agents must ALWAYS read and verify compliance against:
* ⚠️ `01_Project_Documentation/course_requirements/`
  * **Reason:** Contains the official academic project syllabus, phase grading rubrics (`DWBI Lab Phase 2.pdf`, `DWBI Lab Phase 3.pdf`), and reference 11-stage pipeline architecture.
  * **Core Rubric Requirements Mapped to Databricks:**
    * Medallion Lakehouse layout: Bronze (Staging), Silver (Conformed & Cleansed), Gold (Star Schema Warehouse & Reporting Marts), Quarantine.
    * Minimum data volume: **100+ dimension rows**, **10,000+ fact rows**.
    * Mandatory surrogate keys (`dim_xxx_key`) and business-key lookup mapping.
    * Formal data quality checks: Completeness, Accuracy, and Referential Integrity.
    * Analytical SQL with window functions, `ROLLUP`, `CUBE`, and query execution plan optimization.
    * 3-Page Power BI dashboard (Executive Overview, Detailed Analysis, Decision Support).

---

## PART III: CANONICAL SYSTEM ARCHITECTURE: DATABRICKS ONLY

There is NO dual architecture. The project is implemented exclusively on the **Databricks Serverless Cloud Lakehouse**:

* **Cloud Platform:** Databricks (`databricks.com` on AWS, Azure, or GCP)
* **Processing Engine:** Apache Spark 3.5+ / 4.x on Serverless Compute (Photon Engine)
* **Warehouse Engine:** Databricks Serverless SQL Warehouse
* **Table & Storage Format:** Delta Lake (`USING DELTA`) with ACID log and Liquid Clustering
* **Unified Governance:** Unity Catalog 3-tier namespace (`catalog.schema.table`)
* **Target Catalog:** **`dwbi_catalog`**
* **BI Connectivity:** Microsoft Power BI Desktop connected via Native Databricks Connector (**DirectQuery** to `gold_marts`)
* **Primary Blueprints:**
  * **[`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md)**: Master cloud architecture runbook.
  * **[`PROJECT_BLUEPRINT.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md)**: Master domain logic, mathematical formulas, and Kimball dimensional definitions.

---

## PART IV: UNITY CATALOG SPECIFICATION (`dwbi_catalog`)

All tables, views, and raw volumes live under **`dwbi_catalog`**:

```
dwbi_catalog/
├── Volumes/
│   └── bronze_staging/
│       └── raw_landing/                     # Raw files: EIA-860/923 (.xlsx), EPA CAMPD (.csv), NOAA (.csv)
│
├── Schemas:
│   ├── bronze_staging                       # Append-only raw Delta tables + ingestion audit log (etl_run_log)
│   ├── silver_conformed                     # Conformed units, deduplicated entities, crosswalk graph
│   ├── gold_warehouse                       # Kimball Star Schema (5 Dims + 3 Multi-Grain Facts)
│   ├── gold_marts                           # Materialized reporting views for Power BI DirectQuery
│   └── quarantine                           # Dead-letter quarantine table (rejected_records)
```

### Standardized Tables in `gold_warehouse`
* **Dimensions:**
  * `dim_date`: PK `date_key` (INT, `YYYYMMDD`)
  * `dim_plant`: PK `plant_key` (BIGINT IDENTITY), Natural UK `orispl_code`
  * `dim_generator`: PK `generator_key` (BIGINT IDENTITY), Natural `(orispl_code, generator_id)`. **SCD Type 2** tracked via `operating_status`, `valid_from`, `valid_to`, `is_current`.
  * `dim_balancing_authority`: PK `ba_key` (BIGINT IDENTITY), Natural UK `ba_code`
  * `dim_weather_station`: PK `station_key` (BIGINT IDENTITY), Natural UK `station_id`
* **Fact Tables (3 Kimball Archetypes):**
  1. `fact_hourly_emissions_weather` (**Transactional Fact**):
     * PK: `(date_key, hour_of_day, plant_key, unit_id)`
     * Optimization: Liquid Clustering via `CLUSTER BY (date_key, plant_key)`
  2. `fact_monthly_plant_operations` (**Periodic Snapshot Fact**):
     * PK: `snapshot_key` (BIGINT IDENTITY), FK: `month_start_date_key`, `plant_key`
     * Measures: `net_generation_mwh` (allows negative during maintenance), `fuel_consumed_mmbtu`, `avg_heat_rate_btu_kwh`, etc.
  3. `fact_regional_grid_demand` (**Aggregate Grid Fact**):
     * PK: `(date_key, hour_of_day, ba_key)`
     * Measures: `demand_mw`, `net_gen_coal_mw`, `net_gen_gas_mw`, `net_gen_wind_mw`, `net_gen_solar_mw`, `net_interchange_mw`.

---

## PART V: DEFENSIVE ENGINEERING GOTCHAS & DOMAIN RULES

1. **Shifting Excel Headers:** EIA-860 headers are on Row 2; EIA-923 headers are on Row 6. Handled via programmatic header discovery scanning for `'Plant Code'` / `'Plant Id'`.
2. **Missing Value Sentinels:** Coerces literal strings (`"."`, `"NM"`, `"*"`, `""`) and NOAA's integer `-9999` to `NULL`. Use `TRY_CAST()` under ANSI SQL mode to prevent query aborts.
3. **Negative Net Generation:** Valid business event in EIA-923 caused by offline power plants consuming auxiliary grid power during maintenance. Must NEVER be rejected by DQ checks.
4. **Thermodynamic Heat Rate Validation Bounds:**
   * CCGT (Combined Cycle): $5,000 \le \text{Heat Rate} \le 14,000\text{ Btu/kWh}$
   * Coal Steam Turbines: $8,500 \le \text{Heat Rate} \le 18,000\text{ Btu/kWh}$
   * Peakers (Gas Turbines): $9,000 \le \text{Heat Rate} \le 22,000\text{ Btu/kWh}$
   * Violations routed to `dwbi_catalog.quarantine.rejected_records`.
5. **Physical Auxiliary Reconciliation:** $\text{Net Generation (EIA-923)} \le \text{Gross Generation (EPA CAMPD)}$ with auxiliary load ratios expected between $3\%$ and $14\%$.
6. **Delta Identity Column Merges:** In SCD Type 2 merges, never use `UPDATE SET *` directly on tables with identity columns; use `UPDATE SET * EXCEPT (<identity_col>)`. For surrogate keys requiring default row values (`-1 = Unknown`), use `GENERATED BY DEFAULT AS IDENTITY`.

---

## PART VI: 4-PERSON DIVISION OF WORK

* **Work Package 1: Ingestion & Bronze Lakehouse Lead** — Muhammad Ibrahim (24L-2602)
* **Work Package 2: Data Quality & Silver Conformance Lead** — Rai Fahad Sultan (24L-2509)
* **Work Package 3: Dimensional Warehouse & Gold Layer Architect** — Muhammad Ayyan (24L-2568)
* **Work Package 4: Analytics, OLAP, Power BI & Performance Lead** — Taha Imran (24L-2560)
