# U.S. Bulk Power Generation, Emissions & Weather Lakehouse

## What
Enterprise cloud data lakehouse on Databricks Serverless analyzing electrical grid dispatch, smokestack air emissions, and weather stress for DL3004 DWBI.

## Scope
In: Bronze raw landing, Silver DQ & SCD-2, Gold Kimball Star Schema (5 dims, 3 facts), Gold reporting marts, OLAP SQL, Power BI DirectQuery.
Out: Course retail scenario (CampusCart), local PostgreSQL, unclustered Hive Metastore.

## Stack
Databricks Serverless Compute (Photon), Delta Lake (Liquid Clustering), Unity Catalog (`dwbi_catalog`), Python 3.12/3.14, unittest, Power BI DirectQuery.

## Structure
- `01_Project_Documentation`: Master specs, requirements, data dictionaries, schema diagrams.
- `02_Data`: Raw and cleaned bulk archives.
- `03_ETL`: Master config (`config.py`) and Medallion ETL scripts (`01_bronze_ingestion.py`, etc.).
- `04_SQL`: Production Databricks SQL DDL (warehouse, staging, views, quality checks).
- `05_Analytics`: Analytical SQL, OLAP queries (ROLLUP/CUBE), and reporting views.
- `technical-knowledge`: 8 authoritative Layer 2 knowledge base documents + manifest.
- `tests/unit`: Fast, isolated Tier 1 unit tests.

## Run and test
- Install: `uv sync` or `py -3.12 -m venv .venv-dbx`
- Run Bronze: `uv run python 03_ETL/01_bronze_ingestion.py`
- Run Silver: `uv run python 03_ETL/02_silver_cleansing_and_scd.py`
- Test all: `uv run python -m unittest discover tests`
- Test one unit: `uv run python -m unittest tests/unit/test_silver_cleansing.py`

## Decisions
- Databricks Serverless over PostgreSQL: native distributed compute, Delta ACID, Photon vectorization.
- Liquid Clustering over Partitioning: eliminates small file problem; optimizes multi-grain joins.
- Shifting Excel header scanning: EIA-860 Row 2 and EIA-923 Row 6 dynamic detection.
- Allow negative NetGen: preserves valid maintenance station auxiliary draws.
- SCD-2 with EXCEPT: prevents mutating identity columns during Delta MERGE.

## Plan
Status: [ ] todo, [~] in progress, [x] done. Tags S/M/L set model tier.

### Phase 1 - Bronze Staging & Header Discovery [x]
Gate: 9/9 source extractors succeed + 25/25 unit tests green.
- [x] 1.1 Ingestion config & catalog setup [S]
- [x] 1.2 Shifting-header discovery & column cleaner [S]
- [x] 1.3 Bronze multi-source extractors & audit logging [M]

### Phase 2 - Silver Conformance, Data Quality & SCD-2 [x]
Gate: Sentinel coercion, thermodynamic rejection filtering, and SCD-2 tests green.
- [x] 2.1 Sentinel value coercion & TRY_CAST float/int [S]
- [x] 2.2 Thermodynamic heat rate validator & dead-letter quarantine [M]
- [x] 2.3 Generator SCD Type 2 atomic lifecycle tracker [M]
- [x] 2.4 Silver conformance test suite & full phase gate [S]

### Phase 3 - Gold Kimball Star Schema & Multi-Grain Facts [x]
Gate: 5 Dims + 3 Facts DDL created and populated with Liquid Clustering.
- [x] 3.1 Conformed dimensions population (Date, Plant, BA, Station) [M]
- [x] 3.2 Transactional Fact: Hourly Emissions & Weather [L]
- [x] 3.3 Periodic Snapshot Fact: Monthly Plant Operations [M]
- [x] 3.4 Aggregate Grid Fact: Regional Grid Demand [M]

### Phase 4 - Gold Reporting Marts, OLAP SQL & Power BI [x]
Gate: 3 reporting views in gold_marts + OLAP queries execute without error.
- [x] 4.1 Reporting views (vw_emissions_intensity, vw_plant_performance, vw_grid_stress) [M]
- [x] 4.2 OLAP SQL analytics (CUBE, ROLLUP, window functions) [M]
- [x] 4.3 DirectQuery Power BI semantic verification [S]

## Current
Stage 1 (Repo hygiene), Stage 2 (Loader correctness), Stage 3 (6-Category DQ Engine), Stage 4 (Real-Data Downloader, Rubric Volume Gate >=100 Dims / >=10,000 Facts, Synthetic Defect Generator), Stage 5 (Phase 1 document fixes: 10 Kimball BQs, grain statements, hierarchies, vw_monthly_generation_mix), and Stage 6 (Automated PDF Report Generator: Data_Cleaning_Report.pdf and Data_Quality_Report.pdf via ReportLab) are complete. All 87 unit tests green. Next step: Stage 5 leftovers (replace BQ9, CTE grain aggregation for Q8/10/11, DuckDB validation suite, standalone Business_Questions.md & Grain_Definitions.md, and Data_Dictionary.xlsx sync) followed by Stage 7 platform alignment. Suggested model tier: mid.

## Open issues
- None.
