# Execution Environment Specification & Verification Matrix

**Document Status:** Complete & Verified Baseline  
**Verification Date:** November 8, 2026  
**Audience:** Data Engineers, Cloud Architects, System Administrators  
**Applicable Platform:** Databricks Serverless Cloud Lakehouse & Local Development Environment  

---

## 1. Verified Target Execution Environment

The project's target deployment platform is the **Databricks Serverless Cloud Lakehouse**, utilizing **Databricks Serverless Compute** for data engineering notebooks and **Databricks Serverless SQL Warehouse** for SQL analytics and Power BI connectivity.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DATABRICKS CLOUD LAKEHOUSE ENVIRONMENT                          │
├────────────────────────────────┬───────────────────────────────────────────────────────┤
│ Architectural Component        │ Verified Platform Specification                       │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Cloud Lakehouse Platform       │ Databricks (`databricks.com` on AWS, Azure, or GCP)   │
│ Notebook Compute Type          │ **Databricks Serverless Compute** (managed serverless)│
│ Core Processing Engine         │ **Apache Spark 3.5+ / 4.x** with Photon Engine        │
│ Warehouse & Query Engine       │ **Databricks Serverless SQL Warehouse**               │
│ Storage Format & Transaction   │ **Delta Lake 3.x+** (ACID log in `_delta_log/`)       │
│ Governance & Catalog Container │ **Unity Catalog** (`catalog.schema.table` 3-tier)     │
│ Primary Governed Catalog       │ **`dwbi_catalog`**                                    │
│ Unstructured Landing Storage   │ **Unity Catalog Volumes** (`/Volumes/...`)            │
│ Data Clustering Optimization   │ **Liquid Clustering** (`CLUSTER BY`)                  │
│ BI Connectivity & Mode         │ **Power BI Desktop** via Native Databricks DirectQuery│
│ Interactive API Surface        │ **Apache Spark Connect** (Serverless Client gRPC)     │
└────────────────────────────────┴───────────────────────────────────────────────────────┘
```

---

## 2. Serverless vs. Classic Compute Comparison

Databricks Serverless Compute differs significantly from classic all-purpose or job clusters. Understanding these differences is critical to avoiding runtime incompatibilities:

| Operational Feature | Databricks Serverless Compute (Current Target) | Classic All-Purpose / Job Compute |
| :--- | :--- | :--- |
| **Startup Latency** | Instantaneous ($\approx 5$ to $15$ seconds) | Slow cluster provisioning ($3$ to $7$ minutes) |
| **Engine Acceleration** | **Photon Engine** active by default | Optional toggle (Photon incurs additional DBU cost) |
| **Spark Engine Architecture**| **Apache Spark Connect** (client-server gRPC model) | Traditional monolithic Spark Driver / Executor JVM |
| **Language Support** | **Python and SQL only** (Scala and R unsupported) | Python, SQL, Scala, and R |
| **Library Management** | Notebook-scoped via `%pip` & UI Environment panel | Cluster-level Maven, CRAN, PyPI, and custom init scripts |
| **Maven JAR Support** | **No raw Maven coordinates supported** | Direct Maven coordinate installation supported |
| **Local File System** | Ephemeral driver container with POSIX `/Volumes/` | Full access to `/dbfs/`, driver root, and init scripts |
| **DataFrame Caching** | **`df.cache()` & `df.persist()` supported in Env v5+** (evaluates eagerly, session-local cloud disk snapshot `DISK_ONLY`); SQL `CACHE TABLE` & `checkpoint()` prohibited | Full support for in-memory and disk caching with lazy evaluation |
| **Low-Level Spark UI** | Not exposed (Query Profile & Query Insights used) | Full access to traditional Spark UI and executor logs |
| **Maximum Execution Limit**| Strict hard cap of **7 days** continuous runtime | Configurable timeout or indefinite execution |
| **Infrastructure Overhead** | Zero infrastructure management, auto-scaling | Requires VM sizing, driver/worker memory tuning |

---

## 3. Local Development Workstation vs. Cloud Environment

An inspection of the local workstation reveals a substantial discrepancy between local Python tooling and cloud execution capabilities:

### 3.1 Local Workstation Baseline (Inspected November 8, 2026)
* **Operating System:** Microsoft Windows 11 (build architecture: AMD64/x86_64)
* **Active Python Interpreter:** **Python 3.14.5** (detected via local execution)
* **Bytecode Cache:** `03_ETL/__pycache__/config.cpython-314.pyc` confirms local compilation under Python 3.14
* **Installed Packages (Subset of Local Environment):**
  * Data processing: `pandas 3.0.3`, `numpy 2.4.6`, `openpyxl 3.1.5`, `scipy 1.17.1`
  * Visualization: `matplotlib 3.10.9`, `seaborn 0.13.2`
  * Networking / Web: `requests 2.34.2`, `urllib3 2.7.0`, `playwright 1.62.0`, `beautifulsoup4 4.15.0`
  * Document parsing: `pypdf 6.19.0`, `python-docx 1.2.0`
  * Machine learning: `scikit-learn 1.9.0`
* **MISSING Local Packages (Not Installed):**
  * ❌ `pyspark` (Not installed locally)
  * ❌ `delta-spark` (Not installed locally)
  * ❌ `databricks-connect` (Not installed locally)

### 3.2 Cloud Databricks Runtime Baseline
* **Python Runtime in Databricks Serverless:** Typically **Python 3.10**, **Python 3.11**, or **Python 3.12** depending on Serverless Environment version. Serverless Environment Version 5 operates on Python 3.12.x.
* **Spark Version:** Apache Spark 3.5.x or 4.0 preview with Photon engine.
* **Compatibility Conflict with Host:** PySpark and Databricks Connect do NOT officially support Python 3.14. Local execution of `databricks-connect` or `pyspark` on a Python 3.14 host will fail due to missing wheels and incompatible C-API extensions.
* **Defensive Guard in Project Code:**
  `03_ETL/config.py` lines 284–290 explicitly wrap the live `SparkSession` call in a defensive exception handler:
  ```python
  try:
      from pyspark.sql import SparkSession
      spark_session = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
  except Exception:
      print("[WARN] SparkSession not found. Skipping live Databricks DDL initialization.")
      return
  ```
  This allows `config.py` to be imported locally in standard Python for parameter lookup without crashing.

### 3.3 Approved Team-Wide Development Standard (4-Tier Separation Matrix)
*(Approved & Established: November 8, 2026 — Mandatory Baseline for All Four Team Members)*

To guarantee absolute runtime reproducibility across all four team members while preventing local machine conflicts, the team has formally approved and standardized four distinct, strictly decoupled environmental tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               MANDATORY 4-TIER TEAM-WIDE DEVELOPMENT STANDARD MATRIX                   │
├──────┬───────────────────────────────┬─────────────────────────────────────────────────┤
│ Tier │ Architectural Dimension       │ Approved Specification & Enforcement Boundary   │
├──────┼───────────────────────────────┼─────────────────────────────────────────────────┤
│  1   │ Remote Serverless Compute     │ Databricks Serverless Environment Version 5     │
│      │                               │ (Managed cloud container running Python 3.12.x, │
│      │                               │ Apache Spark 3.5+/4.x, Photon engine)           │
├──────┼───────────────────────────────┼─────────────────────────────────────────────────┤
│  2   │ Local Python Interpreter      │ Python 3.12.3                                   │
│      │                               │ (Side-by-side user-scope install; host Python   │
│      │                               │ 3.14/3.13 and system PATH untouched)           │
├──────┼───────────────────────────────┼─────────────────────────────────────────────────┤
│  3   │ Databricks Connect Client     │ databricks-connect==18.3.7                      │
│      │                               │ (Installed in dedicated repo-root .venv-dbx;    │
│      │                               │ strictly NO standalone pyspark or delta-spark)  │
├──────┼───────────────────────────────┼─────────────────────────────────────────────────┤
│  4   │ Authentication Architecture   │ Individual Authentication per Teammate          │
│      │                               │ (CLI OAuth / PAT stored outside repo in         │
│      │                               │ ~/.databrickscfg; zero credentials in git)      │
└──────┴───────────────────────────────┴─────────────────────────────────────────────────┘
```

#### Detailed Dimension Specifications:

1. **Remote Serverless Compute Version (Tier 1):**
   * **Target:** **Databricks Serverless Environment Version 5**.
   * **Characteristics:** Fully managed cloud compute container running on Azure/AWS Databricks.
   * **Engine:** Apache Spark with native Photon acceleration, sub-15 second auto-start, and automatic serverless scaling.
   * **Server Runtime:** Bundles remote Python 3.12.x and Databricks Connect 18 runtime libraries.
   * **Data Governance:** Governed directly under Unity Catalog (`dwbi_catalog`).
   * **Advanced Features:** Supports eager DataFrame disk caching (`df.cache()` with `DISK_ONLY` session snapshots).

2. **Local Python Version (Tier 2):**
   * **Target:** **Python 3.12.3** (64-bit AMD64).
   * **Isolation Rule:** Installed in user scope (e.g., via Windows `winget` or `py -3.12`). Host default interpreters (such as Python 3.14.5 or 3.13.3) and system `PATH` are preserved untouched.
   * **Minor Version Matching Requirement:** Official Databricks Connect protocol requires local Python minor version parity (3.12.x client $\to$ 3.12.x server) to guarantee serialization integrity for Python UDFs and custom transformations without bytecode mismatches.

3. **Databricks Connect Package Version (Tier 3):**
   * **Target:** **`databricks-connect==18.3.7`**.
   * **Environment Location:** Dedicated `.venv-dbx` virtual environment created at the repository root.
   * **Strict Exclusion Invariant:** **Strictly NO standalone `pyspark` or `delta-spark` packages**.
   * **Mechanism:** `databricks-connect` provides client-side Spark Connect stubs that compile local Python DataFrame operations into lightweight Protobuf query plans, transmitting them over gRPC (port 443) to be executed remotely on the Serverless Photon engine.

4. **Individual Authentication Requirements (Tier 4):**
   * **Zero Shared Credentials:** No shared team passwords, tokens, service principals, or API keys.
   * **Zero Repository Credentials:** Personal credentials, tokens, or configuration profiles must **NEVER** be committed to Git. `.gitignore` explicitly blocks `.databrickscfg`, `.env*`, `*.token`, `*.pem`, `*.key`, and `credentials.json`.
   * **Local Storage:** All authentication artifacts reside strictly outside the repository in each teammate's individual user home directory (`%USERPROFILE%\.databrickscfg` on Windows, or per-session environment variables).
   * **Supported Auth Methods:**
     * *Recommended:* Databricks CLI OAuth user-to-machine (U2M) browser login (`databricks auth login --host <workspace-url>`).
     * *Alternative:* Individual Personal Access Token (PAT) configured in `~/.databrickscfg` under `[DEFAULT]` or a named profile `[dwbi-dev]`.
     * *Ephemeral:* In-session environment variables (`$env:DATABRICKS_HOST` and `$env:DATABRICKS_TOKEN`).
   * **Audit & Attribution Integrity:** Individual authentication guarantees that all table creation, data lineage, pipeline runs, and query histories in Databricks and `dwbi_catalog.bronze_staging.etl_run_log` are immutably attributed to the specific teammate (`current_user()`).

#### Teammate Setup Protocol (Windows 11):
1. **Side-by-Side Python 3.12.3 Installation (WinGet):**
   ```powershell
   winget install --id Python.Python.3.12 --version 3.12.3 --scope user --override "/quiet InstallAllUsers=0 PrependPath=0 Shortcuts=0 Include_launcher=1"
   ```
2. **Verify Python 3.12 Launcher:**
   ```powershell
   py -3.12 -V
   # Expected Output: Python 3.12.3
   ```
3. **Create Dedicated Virtual Environment:**
   ```powershell
   py -3.12 -m venv .venv-dbx
   ```
4. **Activate Virtual Environment (PowerShell):**
   ```powershell
   .\.venv-dbx\Scripts\Activate.ps1
   ```
5. **Install Databricks Connect 18.3.7:**
   ```powershell
   .\.venv-dbx\Scripts\python.exe -m pip install "databricks-connect==18.3.7"
   ```
6. **Verify Installation & Spark Connect Stubs:**
   ```powershell
   .\.venv-dbx\Scripts\python.exe -V
   # Output: Python 3.12.3
   .\.venv-dbx\Scripts\python.exe -m pip show databricks-connect
   # Output: Version: 18.3.7
   .\.venv-dbx\Scripts\python.exe -c "from databricks.connect import DatabricksSession; import pyspark; print('IMPORTS_SUCCESSFUL')"
   # Output: IMPORTS_SUCCESSFUL
   ```

---

## 4. Unity Catalog Storage & Volume Configuration

Unity Catalog provides centralized access control, lineage, and storage management across all tiers:

```
dwbi_catalog/
├── Volumes/
│   └── bronze_staging/
│       ├── raw_landing/                     # Target: /Volumes/dwbi_catalog/bronze_staging/raw_landing
│       └── checkpoints/                     # Target: /Volumes/dwbi_catalog/bronze_staging/checkpoints
│
├── Schemas (3-Tier Namespace):
│   ├── bronze_staging                       # Append-only raw Delta tables + etl_run_log
│   ├── silver_conformed                     # Cleansed, typed, deduplicated conformed data
│   ├── gold_warehouse                       # Kimball Star Schema (5 Dimensions + 3 Facts)
│   ├── gold_marts                           # Materialized reporting views for Power BI DirectQuery
│   └── quarantine                           # Dead-letter quarantine table (rejected_records)
```

### 4.1 Storage Access Rules
* **Volume Access in PySpark:**
  ```python
  df = spark.read.format("csv").option("header", "true").load("/Volumes/dwbi_catalog/bronze_staging/raw_landing/campd/hourly_emissions.csv")
  ```
* **POSIX File Access (Driver Python / OpenPyXL):**
  ```python
  import openpyxl
  wb = openpyxl.load_workbook("/Volumes/dwbi_catalog/bronze_staging/raw_landing/eia860/3_1_Generator_Y2023.xlsx", data_only=True)
  ```
  *Note:* Databricks Serverless Compute mounts Unity Catalog Volumes under `/Volumes/` using a high-performance FUSE driver, enabling direct POSIX read/write access.

---

## 5. Network, Security & BI DirectQuery Connectivity

### 5.1 Power BI Desktop Connectivity Specification
Power BI Desktop connects to the Databricks Serverless SQL Warehouse via the native connector:
* **Connection Interface:** Native Databricks Connector (`Get Data -> Databricks`)
* **Host / Server Name:** `<workspace-id>.cloud.databricks.com` (Port 443 over HTTPS/TLS 1.3)
* **HTTP Path:** `/sql/1.0/warehouses/<warehouse-id>`
* **Catalog:** `dwbi_catalog`
* **Default Database:** `gold_marts` (or `gold_warehouse`)
* **Authentication Options:**
  1. Personal Access Token (PAT)
  2. OAuth 2.0 / Microsoft Entra ID (Azure AD)
* **Execution Mode:** **DirectQuery**
  * DirectQuery pushes all DAX visual aggregations directly to the Databricks Serverless SQL Warehouse.
  * Queries execute against Delta Lake with Liquid Clustering, returning summarized result sets in sub-seconds.
  * Zero local memory import bottlenecks on client workstations.

### 5.2 Individual Developer Authentication Architecture (Zero Repository Credentials)

All remote connections via Databricks CLI, Databricks Connect, and IDE extensions require individual authentication. Shared credentials, hardcoded passwords, or repository-committed tokens are strictly prohibited.

#### Authentication Specifications:
1. **Zero Repository Storage:**
   * Credentials must never exist in workspace code files, notebooks, or scripts.
   * `.gitignore` explicitly excludes `.databrickscfg`, `.env*`, `*.token`, `*.pem`, `*.key`, and `credentials.json`.
2. **Individual Teammate Accountability:**
   * Each of the four team members (Ibrahim, Fahad, Ayyan, Taha) generates their own personal credential against the cloud Databricks workspace.
   * Ensures fine-grained Unity Catalog audit logs and that `SELECT current_user()` matches the specific author executing the pipeline.
3. **Primary Authentication Flow (OAuth U2M via Databricks CLI):**
   * Uses browser-based OAuth user-to-machine login managed by the Databricks CLI (`databricks.exe`):
     ```powershell
     databricks auth login --host https://<workspace-url>
     ```
   * Stores the OAuth token securely in the user's home profile (`C:\Users\<user>\.databrickscfg` on Windows), completely outside the repository tree.
4. **Alternative Flow (Personal Access Token in User Home Profile):**
   * If OAuth browser flow is unavailable, configure `~/.databrickscfg`:
     ```ini
     [DEFAULT]
     host  = https://<workspace-url>
     token = <personal-access-token>
     ```
   * Or define a named profile:
     ```ini
     [dwbi-dev]
     host  = https://<workspace-url>
     token = <personal-access-token>
     ```
5. **Ephemeral Session Flow (PowerShell Environment Variables):**
   * For single-session execution without disk storage:
     ```powershell
     $env:DATABRICKS_HOST  = "https://<workspace-url>"
     $env:DATABRICKS_TOKEN = "<personal-access-token>"
     ```
   * Variables exist only in memory in the active PowerShell terminal session and disappear upon closing.

---

## 6. Unknown and Unverified Environment Parameters

To uphold strict scientific integrity, the following deployment-specific parameters are currently **UNKNOWN** from static codebase analysis and must be confirmed prior to live production execution:

| Unknown / Unverified Item | Current Status | How to Verify in Databricks Workspace |
| :--- | :---: | :--- |
| **Databricks Cloud Provider** | **UNKNOWN** | Check workspace URL: AWS (`*.cloud.databricks.com`), Azure (`*.azuredatabricks.net`), or GCP (`*.gcp.databricks.com`). |
| **Databricks Workspace Hostname** | **UNKNOWN** | Navigate to Databricks Workspace $\to$ Copy browser URL (e.g., `dbc-abcdef12-3456.cloud.databricks.com`). |
| **SQL Warehouse ID & HTTP Path** | **UNKNOWN** | In Databricks, navigate to **SQL Warehouses** $\to$ Select target Serverless Warehouse $\to$ **Connection details** $\to$ Copy **HTTP Path** (`/sql/1.0/warehouses/...`). |
| **Unity Catalog Metastore Assignment** | **UNKNOWN** | Verify in **Catalog Explorer** that the workspace is attached to an active Unity Catalog metastore and the user has `CREATE CATALOG` privilege. |
| **Volume Storage Backing** | **UNKNOWN** | Determine whether `/Volumes/dwbi_catalog/bronze_staging/raw_landing` is a Managed Volume (default cloud root) or an External Volume backed by an explicit S3 bucket / ADLS container. |
| **Serverless Compute Region Availability** | **UNKNOWN** | Verify in cloud admin console that Serverless Compute is enabled for your workspace region. |

---

## 7. Verification Checklist for New Developers / Agents

Before attempting to execute pipeline code, run the following verification protocol:
1. Open Databricks SQL Editor or a Serverless Notebook.
2. Run `SELECT current_user(), current_version(), current_metastore();`
3. Execute `03_ETL/config.py` in a notebook cell to automatically provision `dwbi_catalog`, schemas, volumes, and audit tables.
4. If running locally with Python, do not attempt to run `pyspark` directly under Python 3.14; use the dedicated `.venv-dbx` environment with Python 3.12.3 and `databricks-connect==18.3.7` as detailed in Section 3.3.
