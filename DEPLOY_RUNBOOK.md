# ==============================================================================
# PROJECT-AEGIS: DEPLOYMENT & OPERATIONAL RUNBOOK
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Target:  Databricks Serverless Cloud Lakehouse (`dwbi_catalog`)
# Engine:  Apache Spark 3.5+ (Photon) / Delta Lake 3.x / Serverless SQL Warehouse
# ==============================================================================

This runbook provides complete, unambiguous, step-by-step instructions for running
Project-AEGIS both in local offline mode (with synthetic rubric-scale generation or
sample fixtures) and on the live Databricks Serverless Cloud Lakehouse.

---

## PART I: ARCHITECTURAL BOUNDARY (LOCAL VS. DATABRICKS CLOUD)

The pipeline is engineered with a unified codebase that automatically adapts to its
runtime environment:

| Capability | Local Offline Mode | Databricks Serverless Cloud |
| :--- | :--- | :--- |
| **Execution Engine** | Python 3.12 Standard Library (`uv run`) | Apache Spark 3.5+ / Photon on Serverless Compute |
| **Storage Format** | In-memory + Local CSV audit logs (`02_Data/cleaned_data/`) | Delta Lake tables (`USING DELTA`) with ACID log |
| **Catalog / Namespace** | Python dictionary structures (`dw.dim_*`, `dw.fact_*`) | Unity Catalog 3-tier namespace (`dwbi_catalog.schema.table`) |
| **Performance Tuning** | Spherical Haversine in pure Python | `/*+ BROADCAST(s) */` spatial cross-join + Liquid Clustering |
| **Reporting / BI** | CSV exports + direct query emulation | Serverless SQL Warehouse + Power BI DirectQuery views |
| **Audit Logs** | `02_Data/cleaned_data/cleaning_step_log.csv` & `dq_results.csv` | `dwbi_catalog.silver_conformed.cleaning_step_log` & `quarantine.dq_check_results` |

---

## PART II: API KEY CONFIGURATION (`CAMPD_API_KEY`)

The EPA Clean Air Markets Program Data (CAMPD) API requires an approved developer API key.
**Security Rule:** Never commit, print, or log API keys or secrets in repository files or notebook outputs.

### 1. Local Environment Configuration
Set the key in your terminal before running ingestion or download scripts:

**PowerShell (Windows):**
```powershell
$env:CAMPD_API_KEY = "your_actual_campd_api_key_here"
```

**Bash / Zsh (Linux / macOS):**
```bash
export CAMPD_API_KEY="your_actual_campd_api_key_here"
```

### 2. Databricks Cloud Configuration (Production Standard)
In Databricks, store the key securely using **Databricks Secrets**:

1. Install and authenticate the Databricks CLI on your machine:
   ```bash
   databricks auth login --host https://<your-workspace-instance>.cloud.databricks.com
   ```
2. Create an encrypted secret scope:
   ```bash
   databricks secrets create-scope aegis
   ```
3. Store the CAMPD API key in the scope:
   ```bash
   databricks secrets put-secret aegis campd_api_key
   ```
4. Access the key securely inside your Databricks Python notebooks:
   ```python
   import os
   try:
       campd_key = dbutils.secrets.get(scope="aegis", key="campd_api_key")
       os.environ["CAMPD_API_KEY"] = campd_key
   except Exception as e:
       print(f"Databricks secrets retrieval note: {e}")
   ```

---

## PART III: DATA INGESTION & DOWNLOAD INSTRUCTIONS

### 1. Downloading Public Federal Datasets (Local Step)
Run `03_ETL/00_download_sources.py` to retrieve official federal data files.
The script implements exponential backoff retry on HTTP 429/5xx, verifies SHA-256 hashes,
and skips existing completed files:

```bash
# Test endpoint connectivity across all 6 federal sources
uv run python 03_ETL/00_download_sources.py --test-connection

# Download EIA-860 plant and generator master files (2023)
uv run python 03_ETL/00_download_sources.py --source eia860 --year 2023

# Download EIA-923 monthly generation and fuel receipts (2023)
uv run python 03_ETL/00_download_sources.py --source eia923 --year 2023

# Download EPA CAMPD hourly CEMS emissions (requires CAMPD_API_KEY)
uv run python 03_ETL/00_download_sources.py --source epa_cems --year 2023 --limit 50000

# Download NOAA ISD global weather station history and hourly observations
uv run python 03_ETL/00_download_sources.py --source noaa_isd --year 2023

# Download EPA-EIA crosswalk table
uv run python 03_ETL/00_download_sources.py --source crosswalk
```

### 2. Uploading Downloaded Files to Databricks Unity Catalog Volume (Cloud Step)
Bulk files downloaded locally must be staged into the Unity Catalog Bronze landing volume:
`/Volumes/dwbi_catalog/bronze_staging/raw_landing`

Use the Databricks CLI to copy the files directly into the volume:
```bash
databricks fs cp 02_Data/raw_data/ dbfs:/Volumes/dwbi_catalog/bronze_staging/raw_landing/ --recursive
```

Verify staged files via Databricks SQL:
```sql
LIST '/Volumes/dwbi_catalog/bronze_staging/raw_landing';
```

---

## PART IV: PIPELINE EXECUTION INSTRUCTIONS

### Option A: Local Offline Execution

#### 1. Baseline Run on Sample Test Fixtures (< 100 rows, for unit tests)
```bash
uv run python 03_ETL/master_pipeline_runner.py
```
*Note:* Prints a loud warning banner indicating rubric volume gate is NOT satisfied (sample fixtures only).

#### 2. University Rubric Scale Execution (>= 100 Dimensions, >= 10,000 Facts)
```bash
uv run python 03_ETL/master_pipeline_runner.py --synthetic
```
*Output Summary:*
- Generates 125 conformed plants and 375 conformed generators (exceeds $\ge 100$ threshold).
- Generates 12,500 hourly emissions facts (exceeds $\ge 10,000$ threshold).
- Populates 16,182 total star schema facts across all 3 grains.
- Injects 105 tracked defects and reconciles them against cleaning audit logs.
- Executes all 6 Data Quality validation categories (0 `FAIL`).

#### 3. Running the Test Suite
```bash
uv run python -m unittest discover tests
```
*Expected Result:* 75 tests passing green (`OK`).

---

### Option B: Databricks Serverless Cloud Lakehouse Execution

#### Step 1: Initialize Unity Catalog Schemas & Tables (One-Time Setup)
Open Databricks SQL Editor or attach a SQL notebook to your Serverless SQL Warehouse and run:
1. Run [`04_SQL/warehouse.sql`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/04_SQL/warehouse.sql):
   - Creates catalog `dwbi_catalog`.
   - Creates schemas: `bronze_staging`, `silver_conformed`, `gold_warehouse`, `gold_marts`, `quarantine`.
   - Provisions all 5 Dimensions (`dim_date`, `dim_plant`, `dim_generator`, `dim_balancing_authority`, `dim_weather_station`).
   - Provisions all 3 Liquid Clustered Fact tables.
   - Inserts $-1$ default members for unknown entities.
2. Run [`04_SQL/staging.sql`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/04_SQL/staging.sql):
   - Provisions Bronze landing tables, `etl_run_log`, and dead-letter `rejected_records`.
3. Run [`04_SQL/Views.sql`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/04_SQL/Views.sql):
   - Provisions Gold analytical reporting views in `gold_marts`.

#### Step 2: Execute Master Lakehouse Pipeline Notebook
1. Import the repository into your Databricks Workspace under **Workspace > Users > your_email > Project-AEGIS**.
2. Open `03_ETL/master_pipeline_runner.py` as a Databricks Notebook.
3. Attach the notebook to **Serverless Compute** (Photon enabled).
4. Run all cells. The orchestrator will:
   - Ingest Bronze landing files from `/Volumes/dwbi_catalog/bronze_staging/raw_landing`.
   - Clean, conform, standardize text, and perform SCD Type 2 merges into `silver_conformed`.
   - Execute broadcast spatial nearest-station matching and populate `gold_warehouse` star schema.
   - Materialize DirectQuery views in `gold_marts`.
   - Execute all 6 Data Quality check categories into `dwbi_catalog.quarantine.dq_check_results`.
   - Log execution metrics into `dwbi_catalog.bronze_staging.etl_run_log`.

---

## PART V: UNITY CATALOG SQL AUDIT & VERIFICATION QUERIES

After execution, run these SQL verification queries in Databricks SQL Warehouse to verify
rubric compliance and data quality:

### 1. Rubric Volume Gate Verification (>= 100 Dims, >= 10,000 Facts)
```sql
SELECT 
    'dim_plant' AS table_name, 
    COUNT(*) AS total_rows, 
    COUNT(CASE WHEN plant_key != -1 THEN 1 END) AS business_rows,
    CASE WHEN COUNT(CASE WHEN plant_key != -1 THEN 1 END) >= 100 THEN 'PASS' ELSE 'FAIL' END AS rubric_status
FROM dwbi_catalog.gold_warehouse.dim_plant
UNION ALL
SELECT 
    'dim_generator', 
    COUNT(*), 
    COUNT(CASE WHEN generator_key != -1 THEN 1 END),
    CASE WHEN COUNT(CASE WHEN generator_key != -1 THEN 1 END) >= 100 THEN 'PASS' ELSE 'FAIL' END
FROM dwbi_catalog.gold_warehouse.dim_generator
UNION ALL
SELECT 
    'fact_hourly_emissions_weather', 
    COUNT(*), 
    COUNT(*),
    CASE WHEN COUNT(*) >= 10000 THEN 'PASS' ELSE 'FAIL' END
FROM dwbi_catalog.gold_warehouse.fact_hourly_emissions_weather;
```

### 2. Data Quality Audit Suite Results
```sql
SELECT 
    check_category,
    status,
    COUNT(*) AS check_count,
    ROUND(AVG(metric_value), 3) AS avg_metric_value
FROM dwbi_catalog.quarantine.dq_check_results
GROUP BY check_category, status
ORDER BY check_category, status;
```

### 3. Dead-Letter Quarantine Breakdown
```sql
SELECT 
    source_table,
    rejection_reason,
    COUNT(*) AS quarantined_record_count
FROM dwbi_catalog.quarantine.rejected_records
GROUP BY source_table, rejection_reason
ORDER BY quarantined_record_count DESC;
```

### 4. Cleaning Audit Log Row Conservation Check
```sql
SELECT 
    step_name,
    target_table,
    rows_in,
    rows_changed,
    rows_removed,
    rows_quarantined,
    rows_out,
    (rows_in - (rows_out + rows_removed + rows_quarantined)) AS unexplained_difference
FROM dwbi_catalog.silver_conformed.cleaning_step_log
ORDER BY logged_at DESC;
```
*(The `unexplained_difference` column must be exactly 0 across every row).*

### 5. Liquid Clustering Verification
```sql
DESCRIBE DETAIL dwbi_catalog.gold_warehouse.fact_hourly_emissions_weather;
```
*(Confirm that `clusteringColumns` displays `["date_key", "plant_key"]`).*

---

## PART VI: POWER BI DIRECTQUERY CONNECTIVITY

To connect Microsoft Power BI Desktop to `dwbi_catalog.gold_marts`:

1. In Power BI Desktop, click **Get Data > More... > Azure > Azure Databricks** (or **Databricks**).
2. Enter your **Server Hostname** and **HTTP Path** from your Databricks Serverless SQL Warehouse connection details:
   - Server Hostname: `<workspace-id>.cloud.databricks.com`
   - HTTP Path: `/sql/1.0/warehouses/<warehouse-id>`
3. Connection Mode: Select **DirectQuery** (Required by project rubric).
4. Authentication: Sign in with your Databricks Microsoft/Google organizational account or Personal Access Token (PAT).
5. Navigator Dialog:
   - Expand `dwbi_catalog` > `gold_marts`.
   - Select the 3 materialized reporting views:
     - `vw_grid_stress_thermal_efficiency` (Page 1: Executive Grid Stress)
     - `vw_emissions_weather_correlation` (Page 2: Emissions vs Extreme Weather)
     - `vw_monthly_generation_mix` (Page 3: Generation Mix & Heat Rate Benchmarking)
6. Load the views into Power BI and proceed with visual dashboard design.
