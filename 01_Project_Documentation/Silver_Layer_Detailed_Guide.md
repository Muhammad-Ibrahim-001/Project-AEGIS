# Complete Beginner-Friendly Guide to the Silver Layer ETL Pipeline
## Comprehensive Function-by-Function Breakdown of `03_ETL/02_silver_cleansing_and_scd.py`

**Source File:** [`03_ETL/02_silver_cleansing_and_scd.py`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py)  
**Project:** U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse  
**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)  
**Layer in Lakehouse:** Silver Layer (Conformed, Cleaned, and Historical Data)  

---

## Welcome to the Silver Layer: A Plain-English Overview

Imagine you run an orange juice factory:
1. **The Bronze Layer** is where raw truckloads of oranges arrive straight from the farms. Some oranges are ripe, but some are dirty, some are rotten, and some branches and pebbles are mixed in. The Bronze layer accepts everything just as it arrived so we have proof of what the farm delivered.
2. **The Silver Layer** is the washing, sorting, and inspection station. Here, we wash off the dirt, filter out rocks and bad oranges into a separate inspection bin (called **Quarantine**), standardize all oranges into neat crates, and track how the inventory changes over time.
3. **The Gold Layer** is the clean juice packaged into bottles, ready for customers and business executives to drink and analyze.

This document explains every single Python function inside [`03_ETL/02_silver_cleansing_and_scd.py`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py). There are **15 functions** in total, organized into **6 clear categories**. Everything is explained in everyday language without confusing technical buzzwords.

---

## Table of Contents & Category Overview

The 15 functions are divided into 6 logical categories based on what job they do:

* **[Category 1: Foundation Cleaners & Safe Type Converters](#category-1-foundation-cleaners--safe-type-converters)**
  * [Function 1: `is_sentinel`](#function-1-is_sentinel) — Spotting fake or placeholder missing-data values.
  * [Function 2: `coerce_sentinel`](#function-2-coerce_sentinel) — Converting fake values into real database nulls.
  * [Function 3: `try_cast_float`](#function-3-try_cast_float) — Safely converting messy text into decimal numbers.
  * [Function 4: `try_cast_int`](#function-4-try_cast_int) — Safely converting text or decimals into whole numbers.
  * [Function 5: `standardize_text`](#function-5-standardize_text) — Cleaning up accidental spaces and fixing messy capitalization.
* **[Category 2: Data Quality Logging & Defect Quarantine](#category-2-data-quality-logging--defect-quarantine)**
  * [Function 6: `record_cleaning_step`](#function-6-record_cleaning_step) — Logging the exact scorecard of every cleaning step.
  * [Function 7: `quarantine_record`](#function-7-quarantine_record) — Isolating broken records into a holding bin without deleting them.
* **[Category 3: Real-World Physics & Thermodynamic Rules](#category-3-real-world-physics--thermodynamic-rules)**
  * [Function 8: `calculate_and_validate_heat_rate`](#function-8-calculate_and_validate_heat_rate) — Checking if power plant efficiency follows the laws of physics.
* **[Category 4: Tracking Historical Changes Over Time (SCD Type 2)](#category-4-tracking-historical-changes-over-time-scd-type-2)**
  * [Function 9: `conform_generators_scd2`](#function-9-conform_generators_scd2) — Keeping a full timeline of power plant generator upgrades and retirements.
* **[Category 5: Specialized Table Cleaners (Entity Conformance)](#category-5-specialized-table-cleaners-entity-conformance)**
  * [Function 10: `conform_plants`](#function-10-conform_plants) — Cleaning and deduplicating master power plant directories.
  * [Function 11: `conform_monthly_generation`](#function-11-conform_monthly_generation) — Cleaning monthly electricity production and fuel consumption.
  * [Function 12: `conform_weather_hourly`](#function-12-conform_weather_hourly) — Cleaning hourly airport weather station readings.
  * [Function 13: `conform_emissions_hourly`](#function-13-conform_emissions_hourly) — Cleaning hourly smokestack air pollution sensor data.
  * [Function 14: `conform_grid_hourly`](#function-14-conform_grid_hourly) — Cleaning regional power grid electricity supply and demand.
* **[Category 6: Master Pipeline Orchestrator](#category-6-master-pipeline-orchestrator)**
  * [Function 15: `run_silver_conformance_suite`](#function-15-run_silver_conformance_suite) — The conductor running the entire Silver pipeline from start to finish.

---

# CATEGORY 1: Foundation Cleaners & Safe Type Converters

These functions are the basic tools in our toolbox. They are small, fast, reusable helpers that solve common data cleanliness issues before bigger operations take place.

---

## Function 1: `is_sentinel`

### 1. Code of the Function
```python
SENTINEL_SET = {
    ".", "NM", "*", "--", "NA", "N/A", "null", "NULL", "None", "", "   ",
    "-9999", "-9999.0", -9999, -9999.0
}

def is_sentinel(value: Any) -> bool:
    """Checks whether a value is a documented federal missing-data sentinel."""
    if value is None:
        return True
    if isinstance(value, str):
        v_stripped = value.strip()
        if v_stripped in SENTINEL_SET:
            return True
        try:
            num = float(v_stripped)
            return num == -9999.0
        except ValueError:
            return False
    if isinstance(value, (int, float)):
        return value == -9999 or value == -9999.0
    return False
```

### 2. Purpose of This Function
In government and weather databases, when data is missing, people or sensors often don't leave it blank. Instead, they write "fake" placeholder symbols like a dot `"."` (meaning "confidential information"), `"NM"` (meaning "not measured"), or `"-9999"` (meaning a weather thermometer broke). 

The purpose of this function is to act as a **lie detector**. It checks any piece of incoming data and returns `True` if the value is one of these fake placeholders, or `False` if it is a real piece of information.

### 3. Parameters and Data Types
* **`value`** (Data Type: `Any` — can be text, a number, a blank `None`, or anything else):
  * **What it is:** The single piece of data you want to test (for example: `"150.4"`, `"."`, or `-9999`).

* **Returns** (Data Type: `bool`):
  * Returns `True` if the value is a placeholder/missing symbol.
  * Returns `False` if the value is genuine data.

### 4. Step-by-Step Explanation of Important Lines
* `if value is None: return True`
  * If the value is already empty in Python, it is obviously missing, so the function immediately answers `True`.
* `if isinstance(value, str): v_stripped = value.strip()`
  * If the input is text, it removes any accidental spaces from the beginning or end (e.g. `" . "` becomes `"."`).
* `if v_stripped in SENTINEL_SET: return True`
  * It checks if the text matches any known dummy characters in our predefined dictionary list (like `"NM"` or `"*"`).
* `num = float(v_stripped); return num == -9999.0`
  * Weather instruments write missing temperatures as `"-9999"` or `"-9999.0"`. This line safely converts the text to a number to verify if it equals `-9999`.
* `if isinstance(value, (int, float)): return value == -9999 or value == -9999.0`
  * If the input was already a number (not text), it directly checks if the number is `-9999`.

### 5. Data Engineering Concept: Missing Data Sentinels & Scrubbing
* **What is the concept?** In real-world data engineering, older computer systems could not store empty cells (`NULL`). So developers programmed them to insert strange codes like `-9999` or `99999` or `"N/A"`.
* **Why do data engineers care?** If you don't detect these sentinels and you calculate the average outdoor temperature for Chicago in winter, including `-9999` will tell your boss that Chicago was -500 degrees! Detecting sentinels prevents broken mathematical calculations across the entire company.

---

## Function 2: `coerce_sentinel`

### 1. Code of the Function
```python
def coerce_sentinel(value: Any) -> Optional[Any]:
    """Coerces sentinel values to None (SQL NULL). Returns original value if clean."""
    return None if is_sentinel(value) else value
```

### 2. Purpose of This Function
The word "coerce" simply means to safely convert or transform. This function uses our `is_sentinel` lie detector from earlier. If a value is a fake placeholder, it transforms it into Python's official blank value: `None` (which modern SQL databases understand as `NULL`). If the value is clean and genuine, it leaves it untouched.

### 3. Parameters and Data Types
* **`value`** (Data Type: `Any`):
  * **What it is:** The raw data cell being inspected.

* **Returns** (Data Type: `Optional[Any]`):
  * Returns `None` if the input was a dummy placeholder.
  * Returns the original value if it was clean data.

### 4. Step-by-Step Explanation of Important Lines
* `return None if is_sentinel(value) else value`
  * This is a one-line decision: "Call `is_sentinel(value)`. If it says `True`, return `None`. Otherwise, return the original `value`."

### 5. Data Engineering Concept: NULL Normalization
* **What is the concept?** In data warehouses, every dataset should speak the same language. When data is missing, it should always be represented by the universal database symbol `NULL`.
* **Why do data engineers care?** When all missing values are converted to true `NULL`s, SQL functions like `COUNT()`, `AVG()`, and `IS NULL` work automatically without having to write ten different `WHERE column != 'NM' AND column != '.'` conditions every time you run a query.

---

## Function 3: `try_cast_float`

### 1. Code of the Function
```python
def try_cast_float(value: Any) -> Optional[float]:
    """
    Simulates ANSI SQL TRY_CAST(value AS DOUBLE).
    Coerces sentinels and unparseable strings to None without raising exceptions.
    """
    if is_sentinel(value):
        return None
    try:
        cleaned_str = str(value).replace(",", "").strip()
        return float(cleaned_str)
    except (ValueError, TypeError):
        return None
```

### 2. Purpose of This Function
Computers are very strict. If you tell Python to turn the text `"1,250.5"` or `"N/A"` into a decimal number using standard `float()`, Python will panic, crash, and stop your entire multi-hour data pipeline!

This function safely converts any text into a decimal number. It removes commas (like turning `"1,000"` into `"1000"`), and if the text cannot be converted (like `"broken"` or `None`), it quietly returns `None` instead of crashing.

### 3. Parameters and Data Types
* **`value`** (Data Type: `Any`):
  * **What it is:** The raw text or number you want to turn into a decimal (float).

* **Returns** (Data Type: `Optional[float]`):
  * Returns a valid decimal number (e.g. `1250.5`).
  * Returns `None` if it was impossible to convert.

### 4. Step-by-Step Explanation of Important Lines
* `if is_sentinel(value): return None`
  * First, it asks if the value is a dummy character. If so, don't even try to convert it; just return `None`.
* `cleaned_str = str(value).replace(",", "").strip()`
  * Converts the input to text, strips away formatting commas (e.g., `"1,500.25"` becomes `"1500.25"`), and removes accidental edge spaces.
* `return float(cleaned_str)`
  * Converts the clean text into an actual computer decimal number.
* `except (ValueError, TypeError): return None`
  * The safety net: if someone passed in corrupted gibberish like `"ERROR_#4"`, Python catches the error and safely returns `None` instead of crashing the pipeline.

### 5. Data Engineering Concept: Defensive Type Casting (TRY_CAST)
* **What is the concept?** In production enterprise systems, millions of rows flow every minute. You cannot afford for your pipeline to crash at 3:00 AM because row number 850,000 had a stray typo.
* **Why do data engineers care?** Modern cloud engines (like Databricks SQL, Snowflake, and BigQuery) have a special command called `TRY_CAST`. It attempts the conversion and gives `NULL` on failure. This Python function brings that exact same enterprise safety to Python code.

---

## Function 4: `try_cast_int`

### 1. Code of the Function
```python
def try_cast_int(value: Any) -> Optional[int]:
    """
    Simulates ANSI SQL TRY_CAST(value AS INT).
    Coerces sentinels and unparseable values to None.
    """
    f_val = try_cast_float(value)
    return int(round(f_val)) if f_val is not None else None
```

### 2. Purpose of This Function
Just like `try_cast_float`, this function safely converts input values into whole numbers (integers), such as ID numbers, calendar years, or dates. It also handles annoying spreadsheet quirks where whole numbers are written with decimals (for example, Excel often writes the year 2023 as `2023.0`).

### 3. Parameters and Data Types
* **`value`** (Data Type: `Any`):
  * **What it is:** The raw input to be turned into a whole integer.

* **Returns** (Data Type: `Optional[int]`):
  * Returns a whole number (e.g., `2023`, `1001`).
  * Returns `None` if conversion is impossible.

### 4. Step-by-Step Explanation of Important Lines
* `f_val = try_cast_float(value)`
  * Smart trick: it first calls `try_cast_float` so all commas and dummy sentinels are already safely filtered out.
* `return int(round(f_val)) if f_val is not None else None`
  * If a valid decimal came back, it rounds it to the nearest whole number and converts it to an integer (e.g., `2023.0` becomes `2023`). If `f_val` was `None`, it returns `None`.

### 5. Data Engineering Concept: Integer Key Standardization
* **What is the concept?** In a database, IDs and Date Keys (like `20230101` for Jan 1, 2023) must be whole integers.
* **Why do data engineers care?** Joining two massive tables together using integer keys is up to 10 times faster and uses much less memory than joining on messy text strings.

---

## Function 5: `standardize_text`

### 1. Code of the Function
```python
def standardize_text(value: Any, mode: str = "title") -> Optional[str]:
    """
    Standardizes string text:
    - Strips leading and trailing whitespace.
    - Collapses multiple internal whitespace characters into a single space.
    - Coerces sentinel values and empty strings to None.
    - If mode == 'title': Converts words to Title Case (e.g. ' lahore ' and 'LAHORE' -> 'Lahore').
    - If mode == 'upper': Converts string to UPPERCASE (e.g. ' pjm ' -> 'PJM').
    - If mode == 'lower': Converts string to lowercase.
    """
    if is_sentinel(value):
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    collapsed = re.sub(r"\s+", " ", val_str)
    if not collapsed:
        return None
    if mode == "title":
        return collapsed.title()
    elif mode == "upper":
        return collapsed.upper()
    elif mode == "lower":
        return collapsed.lower()
    return collapsed
```

### 2. Purpose of This Function
Humans type inconsistently. In raw files, the same power plant might be typed as `"BARRY"`, `"barry"`, or `"  Barry   "` with extra accidental spaces. 

This function cleans up text by:
1. Stripping outside spaces.
2. Turning multiple inside spaces into a single space (e.g., `"Miller   Steam    Plant"` becomes `"Miller Steam Plant"`).
3. Standardizing letter casing:
   * **Title Case** (`mode="title"`): Every word capitalized (e.g., `"Barry Power Plant"`).
   * **Uppercase** (`mode="upper"`): All capital letters (e.g., state codes like `"AL"` or grid codes like `"PJM"`).
   * **Lowercase** (`mode="lower"`): All small letters.

### 3. Parameters and Data Types
* **`value`** (Data Type: `Any`):
  * **What it is:** The raw text to clean.
* **`mode`** (Data Type: `str`, default value is `"title"`):
  * **What it is:** Casing mode. Accepts `"title"`, `"upper"`, or `"lower"`.

* **Returns** (Data Type: `Optional[str]`):
  * Returns the clean, standardized text string.
  * Returns `None` if the text was empty or a sentinel placeholder.

### 4. Step-by-Step Explanation of Important Lines
* `if is_sentinel(value): return None`
  * If the text was just `"."` or `"N/A"`, return `None` right away.
* `collapsed = re.sub(r"\s+", " ", val_str)`
  * Uses regular expressions (regex) to find clusters of tabs and multiple spaces and collapse them down into one neat space.
* `if mode == "title": return collapsed.title()`
  * Converts the first letter of each word to uppercase and the rest to lowercase.
* `elif mode == "upper": return collapsed.upper()`
  * Converts all letters to uppercase (ideal for postal abbreviations and agency codes).

### 5. Data Engineering Concept: Data Harmonization & Deduplication Prep
* **What is the concept?** Harmonization means bringing messy text from multiple different organizations into a single unified visual format.
* **Why do data engineers care?** If you group your sales report by state, a database treats `"tx"`, `"TX"`, and `" TX "` as three completely different states! Standardizing text ensures your reports and charts group data correctly.

---

# CATEGORY 2: Data Quality Logging & Defect Quarantine

In professional data engineering, you never quietly delete bad data. You must measure what you did, and you must isolate bad data into a safe place so engineers can inspect it.

---

## Function 6: `record_cleaning_step`

### 1. Code of the Function
```python
CLEANING_STEP_LOG: List[Dict[str, Any]] = []

def record_cleaning_step(
    batch_id: str,
    step_name: str,
    target_table: str,
    rows_in: int,
    rows_changed: int,
    rows_removed: int,
    rows_quarantined: int,
    rows_out: Optional[int] = None,
    spark_session=None
) -> Dict[str, Any]:
    """
    Logs data cleansing metrics (in, changed, removed, quarantined, out)
    to dwbi_catalog.silver_conformed.cleaning_step_log in Databricks
    or to 02_Data/cleaned_data/cleaning_step_log.csv when running offline.
    """
    if rows_out is None:
        rows_out = rows_in - rows_removed - rows_quarantined

    entry = {
        "batch_id": batch_id,
        "step_name": step_name,
        "target_table": target_table,
        "rows_in": rows_in,
        "rows_changed": rows_changed,
        "rows_removed": rows_removed,
        "rows_quarantined": rows_quarantined,
        "rows_out": rows_out,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    CLEANING_STEP_LOG.append(entry)

    # Persist to local CSV
    try:
        out_dir = MODULE_DIR.parent / "02_Data" / "cleaned_data"
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_file = out_dir / "cleaning_step_log.csv"
        file_exists = csv_file.exists()
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "batch_id", "step_name", "target_table", "rows_in",
                "rows_changed", "rows_removed", "rows_quarantined", "rows_out", "logged_at"
            ])
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry)
    except Exception as e:
        print(f"[WARN] Failed to write cleaning step log to CSV: {e}")

    if spark_session is not None:
        try:
            from pyspark.sql import Row
            log_table = config.get_table_fqn("SILVER", "cleaning_step_log")
            dbx_row = {
                "step_name": str(step_name),
                "table_name": str(target_table),
                "rows_in": int(rows_in),
                "rows_changed": int(rows_changed),
                "rows_removed": int(rows_removed),
                "rows_quarantined": int(rows_quarantined),
                "logged_at": datetime.now(timezone.utc)
            }
            df_log = spark_session.createDataFrame([Row(**dbx_row)])
            df_log.write.format("delta").mode("append").saveAsTable(log_table)
        except Exception as e:
            print(f"[WARN] Failed to write cleaning step log to Spark Delta table: {e}")

    return entry
```

### 2. Purpose of This Function
This function acts as the **audit scorecard** for every data cleaning operation. Whenever we clean a table, this function records:
* How many rows entered the factory (`rows_in`).
* How many rows had spelling or number errors fixed (`rows_changed`).
* How many duplicate rows were removed (`rows_removed`).
* How many defective rows were kicked out to quarantine (`rows_quarantined`).
* How many pristine clean rows came out (`rows_out`).

It saves these records both to a local CSV file on disk and into the cloud Databricks audit table (`cleaning_step_log`).

### 3. Parameters and Data Types
* **`batch_id`** (`str`): The unique execution tag for this pipeline run (e.g. `"BATCH_20261118_01"`).
* **`step_name`** (`str`): The name of the cleaning task (e.g. `"CONFORM_PLANTS"`).
* **`target_table`** (`str`): The table being produced (e.g. `"silver_plants"`).
* **`rows_in`** (`int`): Count of incoming raw rows.
* **`rows_changed`** (`int`): Count of rows that were modified/fixed.
* **`rows_removed`** (`int`): Count of duplicate rows dropped.
* **`rows_quarantined`** (`int`): Count of rejected rows sent to quarantine.
* **`rows_out`** (`Optional[int]`, default `None`): Final clean rows. If omitted, the function automatically calculates it: `rows_in - rows_removed - rows_quarantined`.
* **`spark_session`** (`Optional[Any]`, default `None`): The live Databricks cloud Spark session (if running in the cloud).

* **Returns** (`Dict[str, Any]`): A dictionary containing the logged audit metrics.

### 4. Step-by-Step Explanation of Important Lines
* `if rows_out is None: rows_out = rows_in - rows_removed - rows_quarantined`
  * **The Law of Row Conservation:** Data cannot magically vanish into thin air! Every row that entered must be accounted for as clean, duplicate-removed, or quarantined.
* `CLEANING_STEP_LOG.append(entry)`
  * Saves the audit entry into computer memory for quick inspection.
* `with open(csv_file, "a", ...) as f: writer.writerow(entry)`
  * Safely appends the metrics to a persistent CSV file so you can open it in Microsoft Excel anytime.
* `df_log.write.format("delta").mode("append").saveAsTable(log_table)`
  * When running in Databricks cloud, it permanently appends this audit row to the Delta Lake audit table.

### 5. Data Engineering Concept: Row Conservation & Pipeline Observability
* **What is the concept?** Observability means knowing what is happening inside your data pipelines without guessing. Row conservation means:
$$\text{Rows In} = \text{Rows Out} + \text{Rows Removed} + \text{Rows Quarantined}$$
* **Why do data engineers care?** If an executive asks, *"Why did our report have 1,000 fewer rows today than yesterday?"*, a data engineer who has this log can instantly answer: *"Because 1,000 records had corrupt plant IDs and were safely routed to quarantine."*

---

## Function 7: `quarantine_record`

### 1. Code of the Function
```python
QUARANTINE_HISTORY: List[Dict[str, Any]] = []

def quarantine_record(
    batch_id: str,
    source_system: str,
    source_table: str,
    source_row_identifier: str,
    rejection_reason: str,
    raw_payload: Dict[str, Any],
    spark_session=None
) -> Dict[str, Any]:
    """
    Routes an anomalous or sentinel-corrupted record to the dead-letter quarantine table.
    """
    record = {
        "batch_id": batch_id,
        "source_system": source_system,
        "source_table": source_table,
        "source_row_identifier": str(source_row_identifier),
        "rejection_reason": rejection_reason,
        "raw_payload_json": json.dumps(raw_payload, default=str),
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }
    QUARANTINE_HISTORY.append(record)
    return record
```

### 2. Purpose of This Function
When a record has a critical defect (for example, missing its plant ID, having an impossible date like month 15, or having broken temperatures), we cannot let it into our clean warehouse. But we also must **never throw it away**.

This function packages up the defective row, records **who** sent it, **why** it was rejected, and stores the **entire raw row as a JSON text snippet** inside our "Dead-Letter Quarantine" holding table (`dwbi_catalog.quarantine.rejected_records`).

### 3. Parameters and Data Types
* **`batch_id`** (`str`): The run identifier.
* **`source_system`** (`str`): The government agency name (e.g. `"EIA-860"`, `"EPA-CAMPD"`, `"NOAA-ISD"`).
* **`source_table`** (`str`): The Bronze table name where the bad row came from.
* **`source_row_identifier`** (`str`): A helpful human-readable tag identifying the row (like plant ID or station ID).
* **`rejection_reason`** (`str`): A clear label stating why it was rejected (e.g. `"INVALID_ORISPL_CODE"`, `"INVALID_DATE_FORMAT"`).
* **`raw_payload`** (`Dict[str, Any]`): The entire dictionary of all columns for that raw row.
* **`spark_session`** (`Optional[Any]`, default `None`): Cloud Spark connection.

* **Returns** (`Dict[str, Any]`): The quarantine record dictionary.

### 4. Step-by-Step Explanation of Important Lines
* `"raw_payload_json": json.dumps(raw_payload, default=str)`
  * Converts the entire original dictionary of raw data into a JSON string. Even if different tables have completely different columns, JSON allows storing any shape of data in a single text column!
* `"rejected_at": datetime.now(timezone.utc).isoformat()`
  * Stamps the exact universal date and second when this record failed inspection.
* `QUARANTINE_HISTORY.append(record)`
  * Stores it in memory so downstream reporting tools or unit tests can inspect all rejections.

### 5. Data Engineering Concept: Dead-Letter Queue (DLQ) & Zero Data Loss
* **What is the concept?** A Dead-Letter Queue (DLQ) is an isolation holding pen for defective messages or records that cannot be processed.
* **Why do data engineers care?** Novice programmers simply use `DROP` or filter out bad rows with `WHERE`. If you do that, the bad data is gone forever! With a quarantine table, you achieve **zero data loss**: the clean tables stay 100% trustworthy, and data engineers can inspect the quarantine table later, find bugs in the source files, and reprocess the fixed records.

---

# CATEGORY 3: Real-World Physics & Thermodynamic Rules

Data engineering isn't just about checking if something is text or a number. It is about understanding the real world. In energy data, power plants must obey the laws of physics.

---

## Function 8: `calculate_and_validate_heat_rate`

### 1. Code of the Function
```python
def calculate_and_validate_heat_rate(
    fuel_mmbtu_val: Any,
    netgen_mwh_val: Any,
    prime_mover_code: Optional[str] = None
) -> Tuple[Optional[float], bool, Optional[str]]:
    """
    Calculates Heat Rate (Btu/kWh) = (Fuel MMBtu * 1,000) / NetGen MWh.
    Validates against technology-specific physical thermodynamic boundaries.
    
    Returns:
        (heat_rate_value, is_valid, validation_status_code)
    """
    fuel_mmbtu = try_cast_float(fuel_mmbtu_val)
    netgen_mwh = try_cast_float(netgen_mwh_val)

    if fuel_mmbtu is None or netgen_mwh is None:
        return None, True, "MISSING_THERMAL_INPUTS"

    # Business Exception: Offline maintenance draw (NetGen < 0)
    if netgen_mwh < 0:
        return None, True, "STATION_SERVICE_EXCEEDS_OUTPUT"

    if netgen_mwh == 0:
        return None, True, "ZERO_GENERATION_STANDBY"

    heat_rate = (fuel_mmbtu * 1000.0) / netgen_mwh

    # Technology-specific boundary checks
    bounds_cfg = config.DATA_QUALITY_RULES.get("HEAT_RATE_BOUNDS", {})
    pm = (prime_mover_code or "").upper().strip()

    if pm in ["CA", "CT", "CS", "CC"]:
        bounds = bounds_cfg.get("CCGT", {"min": 5000, "max": 14000})
        category = "CCGT"
    elif pm in ["ST"]:
        bounds = bounds_cfg.get("COAL_ST", {"min": 8500, "max": 18000})
        category = "COAL_ST"
    elif pm in ["GT"]:
        bounds = bounds_cfg.get("PEAKER_GT", {"min": 9000, "max": 22000})
        category = "PEAKER_GT"
    else:
        bounds = bounds_cfg.get("GENERAL_THERMAL", {"min": 4500, "max": 30000})
        category = "GENERAL_THERMAL"

    if heat_rate < bounds["min"] or heat_rate > bounds["max"]:
        reason = f"HEAT_RATE_OUT_OF_BOUNDS_{category}_{round(heat_rate, 1)}_LIMITS_{bounds['min']}_{bounds['max']}"
        return round(heat_rate, 2), False, reason

    return round(heat_rate, 2), True, "PHYSICALLY_VALID"
```

### 2. Purpose of This Function
"Heat Rate" is the standard engineering measure of power plant fuel efficiency. It measures how much heat energy (in British Thermal Units, or Btu) a power plant has to burn to generate 1 kilowatt-hour (kWh) of electricity.
* A low heat rate means the plant is super-efficient (it burns very little fuel to make power).
* A high heat rate means the plant is an old fuel-guzzler.

This function does two things:
1. Calculates the Heat Rate formula:
$$\text{Heat Rate} = \frac{\text{Fuel Consumed (Million Btu)} \times 1,000}{\text{Net Electricity Generated (Megawatt-hours)}}$$
2. Checks whether that number is physically possible according to the laws of thermodynamics for that specific engine type:
   * **Combined Cycle Gas Plants (CCGT):** Must be between 5,000 and 14,000 Btu/kWh.
   * **Coal Steam Turbines (ST):** Must be between 8,500 and 18,000 Btu/kWh.
   * **Peaker Gas Turbines (GT):** Must be between 9,000 and 22,000 Btu/kWh.

### 3. Parameters and Data Types
* **`fuel_mmbtu_val`** (`Any`): The amount of fuel burned (Million Btu).
* **`netgen_mwh_val`** (`Any`): The amount of electricity produced (Megawatt-hours).
* **`prime_mover_code`** (`Optional[str]`, default `None`): The mechanical engine type code (e.g. `"CC"`, `"ST"`, `"GT"`).

* **Returns** (`Tuple[Optional[float], bool, Optional[str]]`): A 3-part answer:
  1. The calculated heat rate number (e.g. `7420.5`).
  2. `is_valid` (`True` if valid physics, `False` if impossible).
  3. A status code explaining the outcome (e.g. `"PHYSICALLY_VALID"`, `"STATION_SERVICE_EXCEEDS_OUTPUT"`).

### 4. Step-by-Step Explanation of Important Lines
* `if netgen_mwh < 0: return None, True, "STATION_SERVICE_EXCEEDS_OUTPUT"`
  * **Critical Real-World Rule:** In power plants, when an offline generator is undergoing maintenance, it doesn't produce electricity; it actually pulls power *from* the electrical grid to run lights and cooling pumps! Therefore, **negative net generation is a valid real-world event**, NOT a bug! We flag it as valid so it is not accidentally thrown into quarantine.
* `heat_rate = (fuel_mmbtu * 1000.0) / netgen_mwh`
  * Computes the mathematical efficiency.
* `if heat_rate < bounds["min"] or heat_rate > bounds["max"]:`
  * If a plant claims a heat rate of 2,000 (which would mean 150% efficiency, violating the Second Law of Thermodynamics) or 100,000 (a massive sensor error), it returns `False` so the row is quarantined.

### 5. Data Engineering Concept: Domain-Driven Data Quality
* **What is the concept?** Basic data validation checks technical types (like "is this a number?"). Domain-driven validation checks **business logic and scientific reality** (like "can a physical machine actually operate like this?").
* **Why do data engineers care?** Without physics validation, bad sensor numbers will ruin downstream artificial intelligence models and executive financial forecasts.

---

# CATEGORY 4: Tracking Historical Changes Over Time (SCD Type 2)

Power plants are not static; over 30 years, an operating generator might be temporarily mothballed into standby, have its capacity increased, or be retired permanently.

---

## Function 9: `conform_generators_scd2`

### 1. Code of the Function
```python
def conform_generators_scd2(
    raw_generators: List[Dict[str, Any]],
    batch_id: str,
    existing_dim_records: Optional[List[Dict[str, Any]]] = None,
    effective_timestamp: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Applies SCD Type 2 tracking to generators:
    - Natural Composite Key: (orispl_code, generator_id).
    - Monitored Attributes: operating_status, nameplate_capacity_mw.
    - If status or capacity changes, closes previous version (valid_to = now, is_current = False)
      and opens new version (valid_from = now, valid_to = '9999-12-31 23:59:59', is_current = True).
    - Deduplicates on (orispl_code, generator_id) within initial baseline batch, keeping latest.
    - Standardizes codes and text to uppercase.
    """
    effective_timestamp = effective_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    open_infinity = "9999-12-31 23:59:59"
    rows_in = len(raw_generators)
    rows_changed = 0
    rows_removed = 0
    quarantined = []

    # Index existing current and historical records when provided
    existing_map = {}
    historical_records = []
    if existing_dim_records:
        for rec in existing_dim_records:
            if rec.get("is_current", True):
                k = (rec.get("orispl_code"), str(rec.get("generator_id")).strip().upper())
                existing_map[k] = dict(rec)
            else:
                historical_records.append(dict(rec))

    # Baseline pass: deduplicate incoming batch keeping latest
    # Update pass: process sequentially so chronological transitions (OP -> SB -> RE) are preserved
    if not existing_dim_records:
        deduped_raw = {}
        for row in raw_generators:
            raw_code = row.get("plant_code") or row.get("plant_id")
            orispl = try_cast_int(raw_code)
            gen_id = standardize_text(row.get("generator_id", ""), mode="upper")

            if orispl is None or not gen_id:
                q_rec = quarantine_record(
                    batch_id=batch_id,
                    source_system="EIA-860",
                    source_table="bronze_staging.raw_eia860_generator",
                    source_row_identifier=f"{raw_code}_{gen_id}",
                    rejection_reason="MISSING_GENERATOR_NATURAL_KEY",
                    raw_payload=row
                )
                quarantined.append(q_rec)
                continue

            nat_key = (orispl, gen_id)
            if nat_key in deduped_raw:
                rows_removed += 1
            deduped_raw[nat_key] = row
        update_rows = list(deduped_raw.values())
    else:
        update_rows = []
        for row in raw_generators:
            raw_code = row.get("plant_code") or row.get("plant_id")
            orispl = try_cast_int(raw_code)
            gen_id = standardize_text(row.get("generator_id", ""), mode="upper")
            if orispl is None or not gen_id:
                q_rec = quarantine_record(
                    batch_id=batch_id,
                    source_system="EIA-860",
                    source_table="bronze_staging.raw_eia860_generator",
                    source_row_identifier=f"{raw_code}_{gen_id}",
                    rejection_reason="MISSING_GENERATOR_NATURAL_KEY",
                    raw_payload=row
                )
                quarantined.append(q_rec)
                continue
            update_rows.append(row)

    conformed_updates = list(historical_records)

    for row in update_rows:
        raw_code = row.get("plant_code") or row.get("plant_id")
        orispl = try_cast_int(raw_code)
        gen_id = standardize_text(row.get("generator_id", ""), mode="upper")
        nat_key = (orispl, gen_id)

        raw_status = row.get("status", row.get("operating_status", "OP"))
        std_status = standardize_text(raw_status, mode="upper") or "OP"
        capacity_mw = try_cast_float(row.get("nameplate_capacity_mw"))
        pm = standardize_text(row.get("prime_mover", row.get("prime_mover_code", "")), mode="upper") or ""
        energy = standardize_text(row.get("energy_source_1", row.get("primary_energy_source", "")), mode="upper") or ""
        row_effective_time = row.get("valid_from") or effective_timestamp

        if nat_key in existing_map:
            prior = existing_map[nat_key]
            prior_status = str(prior.get("operating_status", "")).strip().upper()
            prior_cap = try_cast_float(prior.get("nameplate_capacity_mw"))

            if prior_status != std_status or (capacity_mw is not None and prior_cap != capacity_mw):
                rows_changed += 1
                prior["valid_to"] = row_effective_time
                prior["is_current"] = False
                conformed_updates.append(dict(prior))

                new_version = dict(prior)
                new_version["operating_status"] = std_status
                if capacity_mw is not None:
                    new_version["nameplate_capacity_mw"] = capacity_mw
                new_version["valid_from"] = row_effective_time
                new_version["valid_to"] = open_infinity
                new_version["is_current"] = True
                new_version["_batch_id"] = batch_id
                existing_map[nat_key] = new_version
        else:
            if std_status != raw_status or pm != row.get("prime_mover") or energy != row.get("energy_source_1"):
                rows_changed += 1
            existing_map[nat_key] = {
                "orispl_code": orispl,
                "generator_id": gen_id,
                "prime_mover_code": pm,
                "primary_energy_source": energy,
                "nameplate_capacity_mw": capacity_mw,
                "operating_status": std_status,
                "operating_year": try_cast_int(row.get("operating_year")),
                "planned_retirement_year": try_cast_int(row.get("retirement_year", row.get("planned_retirement_year"))),
                "valid_from": row_effective_time,
                "valid_to": open_infinity,
                "is_current": True,
                "_batch_id": batch_id
            }

    conformed_inserts = list(existing_map.values())
    all_conformed = conformed_updates + conformed_inserts
    rows_out_step = (rows_in - rows_removed - len(quarantined)) if existing_dim_records else len(all_conformed)
    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_GENERATORS_SCD2_UPDATES" if existing_dim_records else "CONFORM_GENERATORS_SCD2",
        target_table="silver_generators",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=rows_out_step,
        spark_session=spark_session if "spark_session" in locals() else None
    )
    return all_conformed, quarantined
```

### 2. Purpose of This Function
Imagine a generator called "Unit 1" at Plant 1001. In 2020, it was actively operating (`"OP"`). In 2022, it was put on standby (`"SB"`). In 2024, it was retired permanently (`"RE"`).

If you just overwrite the generator record, your database will think Unit 1 was retired all the way back in 2020! That makes your historical reports wrong.

This function implements **Slowly Changing Dimension Type 2 (SCD Type 2)**:
* When a generator's status or capacity changes, it "closes" the old record (sets its `valid_to` date to the day of change, and `is_current = False`).
* It inserts a brand-new row for the new status with `valid_from = day of change`, `valid_to = '9999-12-31 23:59:59'` (meaning infinity/still active), and `is_current = True`.

### 3. Parameters and Data Types
* **`raw_generators`** (`List[Dict[str, Any]]`): List of raw generator records to process.
* **`batch_id`** (`str`): The batch execution ID.
* **`existing_dim_records`** (`Optional[List[Dict[str, Any]]]`, default `None`): Pre-existing generator records from earlier runs (if updating existing historical records).
* **`effective_timestamp`** (`Optional[str]`, default `None`): The date and time when this change took effect.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Complete list of conformed generator records (both past history and current active rows).
  2. Quarantined records (e.g. rows missing plant codes or generator IDs).

### 4. Step-by-Step Explanation of Important Lines
* `nat_key = (orispl, gen_id)`
  * Builds the composite natural key: a generator is uniquely identified by the combination of its Plant Code (`orispl`) and its Unit ID (`gen_id`).
* `if prior_status != std_status or (capacity_mw is not None and prior_cap != capacity_mw):`
  * Checks if the monitored attributes (status or capacity) actually changed.
* `prior["valid_to"] = row_effective_time; prior["is_current"] = False`
  * Retires the old version: stamps when it stopped being active and marks `is_current` as `False`.
* `new_version["valid_from"] = row_effective_time; new_version["valid_to"] = "9999-12-31 23:59:59"; new_version["is_current"] = True`
  * Creates the new version: stamps when it began, sets its expiration to the distant future, and marks it as the current truth.

### 5. Data Engineering Concept: Slowly Changing Dimensions (SCD Type 2)
* **What is the concept?** Created by Ralph Kimball (the father of data warehousing), SCD Type 2 is the gold standard for tracking history. Instead of overwriting old data (Type 1), you append a new row and maintain a time-validity window (`valid_from` to `valid_to`).
* **Why do data engineers care?** It allows "time travel" queries. An analyst can ask: *"Show me all electricity generated in 2021 by plants that were operating in 2021"*, and the query will be 100% historically accurate.

---

# CATEGORY 5: Specialized Table Cleaners (Entity Conformance)

The following 5 functions take raw Bronze tables from specific government agencies and clean them into trusted Silver tables.

---

## Function 10: `conform_plants`

### 1. Code of the Function
```python
def conform_plants(
    raw_plants: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms and deduplicates EIA-860 plant master records.
    Filters out rows with invalid or missing ORISPL codes.
    Standardizes text (plant_name, county_name, utility_name in Title Case; state_code, ba_code in Uppercase).
    Deduplicates on orispl_code, keeping latest, counting duplicates.
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_plants)
    rows_changed = 0
    rows_removed = 0
    seen_plants = {}  # orispl -> index in conformed

    for row in raw_plants:
        raw_code = row.get("plant_code") or row.get("plant_id")
        orispl = try_cast_int(raw_code)

        if orispl is None or orispl <= 0:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-860",
                source_table="bronze_staging.raw_eia860_plant",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_ORISPL_CODE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_name = row.get("plant_name", "UNKNOWN")
        std_name = standardize_text(raw_name, mode="title") or "Unknown Plant"
        raw_county = row.get("county", row.get("county_name"))
        std_county = standardize_text(raw_county, mode="title")
        raw_util = row.get("utility_name")
        std_util = standardize_text(raw_util, mode="title")

        raw_state = str(row.get("state", row.get("state_code", "")))
        std_state = (standardize_text(raw_state, mode="upper") or "")[:2]
        raw_ba = row.get("balancing_authority_code") or row.get("balancing_auth_code") or row.get("ba_code")
        std_ba = standardize_text(raw_ba, mode="upper")

        if (std_name != raw_name or std_county != raw_county or 
            std_util != raw_util or std_state != raw_state or std_ba != raw_ba):
            rows_changed += 1

        chp_flag = str(row.get("is_combined_heat_power", "")).strip().upper()
        plant_rec = {
            "orispl_code": orispl,
            "plant_name": std_name,
            "utility_id": try_cast_int(row.get("utility_id")),
            "utility_name": std_util,
            "state_code": std_state,
            "county_name": std_county,
            "latitude": try_cast_float(row.get("latitude")),
            "longitude": try_cast_float(row.get("longitude")),
            "ba_code": std_ba,
            "is_combined_heat_power": chp_flag in ["Y", "YES", "TRUE", "1"],
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        if orispl in seen_plants:
            rows_removed += 1
            conformed[seen_plants[orispl]] = plant_rec
        else:
            seen_plants[orispl] = len(conformed)
            conformed.append(plant_rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_PLANTS",
        target_table="silver_plants",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined
```

### 2. Purpose of This Function
This cleans the official government master directory of all U.S. power plants (Form EIA-860). It ensures every plant has a valid identification number (called an `orispl_code`), fixes city/plant/utility names into clean Title Case, standardizes two-letter state codes to uppercase (e.g., `"tx"` becomes `"TX"`), and eliminates duplicate rows so each plant exists exactly once.

### 3. Parameters and Data Types
* **`raw_plants`** (`List[Dict[str, Any]]`): List of raw plant dictionaries from the Bronze stage.
* **`batch_id`** (`str`): Pipeline run tag.
* **`spark_session`** (`Optional[Any]`, default `None`): Databricks connection.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Clean list of conformed plant records.
  2. List of quarantined plant records.

### 4. Step-by-Step Explanation of Important Lines
* `if orispl is None or orispl <= 0:`
  * If a plant has no ID number, it is useless because we cannot connect it to emissions or weather. Such rows are quarantined with reason `"INVALID_ORISPL_CODE"`.
* `std_name = standardize_text(raw_name, mode="title") or "Unknown Plant"`
  * Clean text in Title Case.
* `if orispl in seen_plants: conformed[seen_plants[orispl]] = plant_rec`
  * **Smart Deduplication:** If we encounter plant 1001 a second time in the file, it replaces the older record with the latest one and increments `rows_removed`.
* `record_cleaning_step(...)`
  * Logs the exact row scorecard for auditing.

### 5. Data Engineering Concept: Master Data Management (MDM) & Deduplication
* **What is the concept?** Master Data Management means creating a single, trusted "Golden Record" for your core business entities (like customers, products, or power plants).
* **Why do data engineers care?** If plant names or IDs are duplicated or misformatted, joining emissions to weather will produce duplicate data, multiplying your calculated emissions by 2x or 3x!

---

## Function 11: `conform_monthly_generation`

### 1. Code of the Function
```python
def conform_monthly_generation(
    raw_gen_records: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EIA-923 Monthly Generation & Fuel data:
    - Coerces sentinel strings ('.', 'NM') to NULL.
    - Calculates and validates heat rate per prime mover.
    - Routes out-of-bounds heat rate records to quarantine.
    - Allows negative net generation (station maintenance draw).
    - Standardizes text (plant_name in Title Case; prime_mover_code, energy_source_code in Uppercase).
    - Computes snapshot month_start_date_key (YYYYMMDD).
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_gen_records)
    rows_changed = 0
    rows_removed = 0

    for row in raw_gen_records:
        raw_code = row.get("plant_id") or row.get("plant_code")
        orispl = try_cast_int(raw_code)

        if orispl is None:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-923",
                source_table="bronze_staging.raw_eia923_monthly_generation",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_PLANT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_name = row.get("plant_name")
        std_name = standardize_text(raw_name, mode="title")
        raw_pm = row.get("reported_prime_mover") or row.get("prime_mover_code") or ""
        pm = standardize_text(raw_pm, mode="upper") or ""
        raw_fuel = row.get("reported_fuel_type_code") or row.get("reported_fuel_type") or row.get("energy_source_code") or ""
        fuel_code = standardize_text(raw_fuel, mode="upper") or ""

        # In EIA-923, each record contains monthly quantities and netgen
        qty_val = row.get("quantity_january")
        netgen_val = row.get("netgen_january")

        # Coerce sentinels
        qty_clean = try_cast_float(qty_val)
        netgen_clean = try_cast_float(netgen_val)
        sentinel_coerced = is_sentinel(qty_val) or is_sentinel(netgen_val)

        if (std_name != raw_name or pm != str(raw_pm).strip() or 
            fuel_code != str(raw_fuel).strip() or sentinel_coerced):
            rows_changed += 1

        year_val = try_cast_int(row.get("YEAR") or row.get("year")) or 2023
        month_val = try_cast_int(row.get("MONTH") or row.get("month")) or 1
        month_start_date_key = year_val * 10000 + (month_val * 100) + 1

        # Estimate MMBtu if physical quantity is given (approx 1.0 MMBtu/unit)
        fuel_mmbtu = qty_clean if qty_clean is not None else 0.0

        heat_rate, is_valid, hr_status = calculate_and_validate_heat_rate(
            fuel_mmbtu_val=fuel_mmbtu,
            netgen_mwh_val=netgen_clean,
            prime_mover_code=pm
        )

        if not is_valid:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-923",
                source_table="bronze_staging.raw_eia923_monthly_generation",
                source_row_identifier=f"{orispl}_{pm}_{fuel_code}_JAN",
                rejection_reason=hr_status or "HEAT_RATE_OUT_OF_BOUNDS",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        conformed.append({
            "orispl_code": orispl,
            "plant_name": std_name,
            "prime_mover_code": pm,
            "energy_source_code": fuel_code,
            "year": year_val,
            "month_start_date_key": month_start_date_key,
            "net_generation_mwh": netgen_clean if netgen_clean is not None else 0.0,
            "fuel_consumed_mmbtu": fuel_mmbtu,
            "avg_heat_rate_btu_kwh": heat_rate,
            "heat_rate_validation_code": hr_status,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_MONTHLY_GENERATION",
        target_table="silver_monthly_generation",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined
```

### 2. Purpose of This Function
Cleans monthly electricity generation and fuel consumption data (Form EIA-923). It filters out sentinel characters, computes and tests heat rates against the laws of physics, allows negative net generation for maintenance draws, standardizes fuel codes (e.g. `"NG"` for natural gas, `"BIT"` for bituminous coal), and generates a monthly integer date key (e.g. `20230101` for January 2023).

### 3. Parameters and Data Types
* **`raw_gen_records`** (`List[Dict[str, Any]]`): Raw monthly generation rows from EIA-923.
* **`batch_id`** (`str`): Pipeline execution run tag.
* **`spark_session`** (`Optional[Any]`, default `None`): Cloud Spark session.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Clean conformed monthly generation records.
  2. Quarantined records (e.g. impossible heat rates or missing plant IDs).

### 4. Step-by-Step Explanation of Important Lines
* `month_start_date_key = year_val * 10000 + (month_val * 100) + 1`
  * **Math Date Key Generation:** Converts year 2023 and month 1 into an integer: $2023 \times 10000 + 100 + 1 = 20230101$.
* `heat_rate, is_valid, hr_status = calculate_and_validate_heat_rate(...)`
  * Calls our physics engine to calculate heat rate and verify physical limits.
* `if not is_valid: quarantined.append(...)`
  * If a record violates physics, it is isolated to quarantine with the exact violation details.

### 5. Data Engineering Concept: Periodic Snapshot Fact Preparation
* **What is the concept?** In Kimball data warehouse design, a "Periodic Snapshot" takes a picture of performance at regular intervals (like at the end of every month).
* **Why do data engineers care?** Operating monthly facts require standardized surrogate date keys (like `20230101`) to connect directly to the central Calendar Dimension table (`dim_date`).

---

## Function 12: `conform_weather_hourly`

### 1. Code of the Function
```python
def conform_weather_hourly(
    raw_weather_records: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms NOAA ISD Weather observations:
    - Coerces -9999 sensor dropouts to NULL.
    - Standardizes station_id to uppercase.
    - Routes invalid readings or corrupt timestamps to quarantine.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_weather_records)
    rows_changed = 0
    rows_removed = 0

    for row in raw_weather_records:
        raw_station = row.get("station_id", row.get("station", ""))
        station_id = standardize_text(raw_station, mode="upper") or "UNKNOWN"
        ts = row.get("timestamp_utc", row.get("timestamp", ""))

        # Check for corrupt timestamps or missing station
        if not ts or "BAD" in str(ts) or "CORRUPT" in str(ts) or station_id == "UNKNOWN":
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="NOAA-ISD",
                source_table="bronze_staging.raw_noaa_isd_weather",
                source_row_identifier=f"{station_id}_{ts}",
                rejection_reason="INVALID_OR_CORRUPT_TIMESTAMP",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        temp_raw = row.get("air_temperature_c", row.get("temperature", {}).get("value") if isinstance(row.get("temperature"), dict) else row.get("temperature"))
        wind_raw = row.get("wind_speed_mps", row.get("windSpeed", {}).get("value") if isinstance(row.get("windSpeed"), dict) else row.get("windSpeed"))

        temp_c = try_cast_float(temp_raw)
        wind_mps = try_cast_float(wind_raw)

        # Domain rule: -9999 is NOAA missing value sentinel, coerced to NULL
        is_temp_sentinel = str(temp_raw).strip() in ["-9999", "-9999.0"] or is_sentinel(temp_raw)
        is_wind_sentinel = str(wind_raw).strip() in ["-9999", "-9999.0"] or is_sentinel(wind_raw)

        if is_temp_sentinel:
            temp_c = None
        if is_wind_sentinel:
            wind_mps = None

        if station_id != str(raw_station).strip() or is_temp_sentinel or is_wind_sentinel:
            rows_changed += 1

        conformed.append({
            "station_id": station_id,
            "timestamp_utc": str(ts),
            "air_temperature_c": temp_c,
            "wind_speed_mps": wind_mps,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        })

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_WEATHER_HOURLY",
        target_table="silver_weather_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined
```

### 2. Purpose of This Function
Cleans hourly surface weather data collected from airport weather stations across the United States (NOAA Integrated Surface Database). It handles missing sensor dropouts (coercing `-9999` to `NULL`), quarantines corrupted or unreadable timestamps, and cleans station ID codes.

### 3. Parameters and Data Types
* **`raw_weather_records`** (`List[Dict[str, Any]]`): Raw weather rows from NOAA.
* **`batch_id`** (`str`): Pipeline batch ID.
* **`spark_session`** (`Optional[Any]`, default `None`): Cloud Spark session.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Conformed hourly weather records.
  2. Quarantined bad weather rows.

### 4. Step-by-Step Explanation of Important Lines
* `if not ts or "BAD" in str(ts) or ...: quarantined.append(...)`
  * If a weather reading has no timestamp or a corrupted date string, we cannot correlate it to power plants, so it is routed to quarantine.
* `is_temp_sentinel = str(temp_raw).strip() in ["-9999", "-9999.0"] ...`
  * Detects NOAA's infamous `-9999` sensor error and resets it to `None` (`NULL`).

### 5. Data Engineering Concept: IoT Telemetry Scrubbing
* **What is the concept?** Weather stations and internet-of-things (IoT) devices frequently lose internet connectivity or suffer sensor dropouts.
* **Why do data engineers care?** When handling sensor data, a data engineer must differentiate between a genuine freezing reading (like -20°C in Alaska) and a hardware malfunction (`-9999`).

---

## Function 13: `conform_emissions_hourly`

### 1. Code of the Function
```python
def conform_emissions_hourly(
    raw_emissions: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EPA CAMPD Hourly Smokestack Emissions:
    - Sentinel coercion on all numeric metrics (gross load, heat input, SO2, NOx, CO2).
    - Date format validation (YYYY-MM-DD -> date_key YYYYMMDD); invalid dates routed to quarantine.
    - Hour validation (0-23); invalid or out-of-bounds hours routed to quarantine.
    - Facility and unit key validation; missing keys routed to quarantine.
    - Deduplication on (orispl_code, unit_id, date_key, hour_of_day), keeping latest.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_emissions)
    rows_changed = 0
    rows_removed = 0
    seen_keys = {}  # (orispl, unit, date_key, hour) -> index in conformed

    for row in raw_emissions:
        raw_code = (row.get("oris_code") or row.get("facilityid") or row.get("facilityId") or 
                    row.get("plant_code") or row.get("facility_id"))
        orispl = try_cast_int(raw_code)

        if orispl is None or orispl <= 0:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=str(raw_code),
                rejection_reason="INVALID_PLANT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_unit = row.get("unit_id") or row.get("unitid") or row.get("unitId")
        unit_id = standardize_text(raw_unit, mode="upper")
        if not unit_id:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_UNKNOWN_UNIT",
                rejection_reason="MISSING_UNIT_ID",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Parse date
        raw_date = row.get("date_observed") or row.get("date")
        date_key = None
        if raw_date is not None:
            clean_date_str = str(raw_date).strip().replace("-", "")
            if len(clean_date_str) == 8 and clean_date_str.isdigit():
                date_key = try_cast_int(clean_date_str)

        if date_key is None or date_key < 19000101 or date_key > 21000101:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_{unit_id}_{raw_date}",
                rejection_reason="INVALID_DATE_FORMAT",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Parse hour
        raw_hour = row.get("hour_observed") if row.get("hour_observed") is not None else row.get("hour")
        hour_of_day = try_cast_int(raw_hour)
        if hour_of_day is None or hour_of_day < 0 or hour_of_day > 23:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EPA-CAMPD",
                source_table="bronze_staging.raw_epa_hourly_emissions",
                source_row_identifier=f"{orispl}_{unit_id}_{date_key}_{raw_hour}",
                rejection_reason="INVALID_HOUR_RANGE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        # Clean measures
        gross_load = try_cast_float(row.get("gross_load_mw") if row.get("gross_load_mw") is not None else (row.get("grossload") if row.get("grossload") is not None else row.get("grossLoad")))
        heat_input = try_cast_float(row.get("heat_input_mmbtu") if row.get("heat_input_mmbtu") is not None else (row.get("heatinput") if row.get("heatinput") is not None else row.get("heatInput")))
        so2_mass = try_cast_float(row.get("so2_mass_lbs") if row.get("so2_mass_lbs") is not None else (row.get("so2mass") if row.get("so2mass") is not None else row.get("so2Mass")))
        nox_mass = try_cast_float(row.get("nox_mass_lbs") if row.get("nox_mass_lbs") is not None else (row.get("noxmass") if row.get("noxmass") is not None else row.get("noxMass")))
        co2_mass = try_cast_float(row.get("co2_mass_tons") if row.get("co2_mass_tons") is not None else (row.get("co2mass") if row.get("co2mass") is not None else row.get("co2Mass")))

        if (is_sentinel(gross_load) or is_sentinel(heat_input) or 
            is_sentinel(so2_mass) or is_sentinel(nox_mass) or is_sentinel(co2_mass)):
            rows_changed += 1

        rec = {
            "orispl_code": orispl,
            "unit_id": unit_id,
            "date_key": date_key,
            "hour_of_day": hour_of_day,
            "gross_load_mw": gross_load,
            "heat_input_mmbtu": heat_input,
            "so2_mass_lbs": so2_mass,
            "nox_mass_lbs": nox_mass,
            "co2_mass_tons": co2_mass,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        # Deduplication check
        dedup_key = (orispl, unit_id, date_key, hour_of_day)
        if dedup_key in seen_keys:
            rows_removed += 1
            conformed[seen_keys[dedup_key]] = rec
        else:
            seen_keys[dedup_key] = len(conformed)
            conformed.append(rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_EMISSIONS_HOURLY",
        target_table="silver_emissions_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined
```

### 2. Purpose of This Function
The U.S. Environmental Protection Agency (EPA) requires power plant smokestacks to have Continuous Emission Monitoring Systems (CEMS) measuring pollution every hour. 

This function cleans that massive data stream:
1. Validates the plant ID and smokestack unit ID.
2. Converts date strings (`"2023-01-01"`) into integer date keys (`20230101`).
3. Validates that the hour is strictly between 0 and 23.
4. Coerces missing sentinels for electricity load and pollution numbers:
   * $\text{SO}_2$ (Sulfur Dioxide, causes acid rain).
   * $\text{NO}_x$ (Nitrogen Oxides, causes smog).
   * $\text{CO}_2$ (Carbon Dioxide, greenhouse gas).
5. Eliminates duplicate readings on the natural key `(plant, unit, date, hour)`.

### 3. Parameters and Data Types
* **`raw_emissions`** (`List[Dict[str, Any]]`): Raw EPA hourly smokestack rows.
* **`batch_id`** (`str`): Pipeline batch ID.
* **`spark_session`** (`Optional[Any]`, default `None`): Cloud Spark connection.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Clean conformed emissions records.
  2. Quarantined bad emissions records.

### 4. Step-by-Step Explanation of Important Lines
* `if hour_of_day is None or hour_of_day < 0 or hour_of_day > 23:`
  * A day only has 24 hours (0 to 23). If a row contains hour 25 or hour -1, it is quarantined as `"INVALID_HOUR_RANGE"`.
* `dedup_key = (orispl, unit_id, date_key, hour_of_day)`
  * A single smokestack unit can only have one emissions measurement for a specific hour on a specific date. This compound key guarantees deduplication.

### 5. Data Engineering Concept: Transactional Grain Enforcement
* **What is the concept?** The "grain" of a table is the exact real-world definition of what one single row represents. Here, the grain is: *"One smokestack unit, during one specific hour, on one specific day."*
* **Why do data engineers care?** Enforcing the grain prevents accidental duplicate records from corrupting the dimensional fact table.

---

## Function 14: `conform_grid_hourly`

### 1. Code of the Function
```python
def conform_grid_hourly(
    raw_grid: List[Dict[str, Any]],
    batch_id: str,
    spark_session=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Conforms EIA-930 Hourly Balancing Authority Grid Telemetry:
    - Sentinel coercion on power flow and generation mix metrics.
    - Standardizes ba_code (uppercase) and ba_name (Title Case).
    - Timestamp parsing (extracts date_key YYYYMMDD and hour_of_day 0-23); invalid timestamps quarantined.
    - Deduplication on (ba_code, date_key, hour_of_day), keeping latest.
    - Records cleaning metrics (rows_in, rows_changed, rows_removed, rows_quarantined).
    """
    conformed = []
    quarantined = []
    rows_in = len(raw_grid)
    rows_changed = 0
    rows_removed = 0
    seen_keys = {}  # (ba_code, date_key, hour) -> index in conformed

    for row in raw_grid:
        raw_ba = row.get("ba_code", row.get("balancing_auth_code"))
        ba_code = standardize_text(raw_ba, mode="upper")
        if not ba_code:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-930",
                source_table="bronze_staging.raw_eia930_hourly_grid",
                source_row_identifier=f"UNKNOWN_BA_{row.get('timestamp_utc')}",
                rejection_reason="MISSING_BA_CODE",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        raw_ba_name = row.get("ba_name")
        ba_name = standardize_text(raw_ba_name, mode="title") or ba_code

        # Parse timestamp
        raw_ts = row.get("timestamp_utc", row.get("timestamp"))
        date_key = None
        hour_of_day = None
        if raw_ts is not None:
            try:
                dt = datetime.fromisoformat(str(raw_ts).strip().replace("Z", "+00:00"))
                date_key = int(dt.strftime("%Y%m%d"))
                hour_of_day = dt.hour
            except Exception:
                pass

        if date_key is None or hour_of_day is None:
            q_rec = quarantine_record(
                batch_id=batch_id,
                source_system="EIA-930",
                source_table="bronze_staging.raw_eia930_hourly_grid",
                source_row_identifier=f"{ba_code}_{raw_ts}",
                rejection_reason="INVALID_GRID_TIMESTAMP",
                raw_payload=row,
                spark_session=spark_session
            )
            quarantined.append(q_rec)
            continue

        demand_mw = try_cast_float(row.get("demand_mw"))
        forecast_mw = try_cast_float(row.get("demand_forecast_mw"))
        gen_coal = try_cast_float(row.get("gen_coal_mw"))
        gen_gas = try_cast_float(row.get("gen_natgas_mw", row.get("gen_gas_mw")))
        gen_nuclear = try_cast_float(row.get("gen_nuclear_mw"))
        gen_hydro = try_cast_float(row.get("gen_hydro_mw"))
        gen_wind = try_cast_float(row.get("gen_wind_mw"))
        gen_solar = try_cast_float(row.get("gen_solar_mw"))
        interchange = try_cast_float(row.get("net_interchange_mw"))

        if (ba_name != raw_ba_name or ba_code != raw_ba or
            is_sentinel(row.get("demand_mw")) or is_sentinel(row.get("demand_forecast_mw"))):
            rows_changed += 1

        rec = {
            "ba_code": ba_code,
            "ba_name": ba_name,
            "interconnect": str(row.get("interconnect", "Unknown")).strip(),
            "timestamp_utc": str(raw_ts),
            "date_key": date_key,
            "hour_of_day": hour_of_day,
            "demand_mw": demand_mw,
            "demand_forecast_mw": forecast_mw,
            "gen_coal_mw": gen_coal,
            "gen_natgas_mw": gen_gas,
            "gen_nuclear_mw": gen_nuclear,
            "gen_hydro_mw": gen_hydro,
            "gen_wind_mw": gen_wind,
            "gen_solar_mw": gen_solar,
            "net_interchange_mw": interchange,
            "_batch_id": batch_id,
            "_conformed_at": datetime.now(timezone.utc).isoformat()
        }

        dedup_key = (ba_code, date_key, hour_of_day)
        if dedup_key in seen_keys:
            rows_removed += 1
            conformed[seen_keys[dedup_key]] = rec
        else:
            seen_keys[dedup_key] = len(conformed)
            conformed.append(rec)

    record_cleaning_step(
        batch_id=batch_id,
        step_name="CONFORM_GRID_HOURLY",
        target_table="silver_grid_hourly",
        rows_in=rows_in,
        rows_changed=rows_changed,
        rows_removed=rows_removed,
        rows_quarantined=len(quarantined),
        rows_out=len(conformed),
        spark_session=spark_session
    )
    return conformed, quarantined
```

### 2. Purpose of This Function
The electrical grid is managed by regional coordinators called Balancing Authorities (such as `"PJM"`, `"MISO"`, `"CAISO"`). They report hourly electricity demand, demand forecasts, and how much electricity was generated by coal, natural gas, nuclear, hydro, wind, and solar.

This function cleans that grid telemetry:
1. Standardizes grid authority codes to uppercase and names to Title Case.
2. Parses international ISO-8601 UTC timestamps (e.g. `"2023-01-01T05:00:00Z"`) into our standard `date_key` (`20230101`) and `hour_of_day` (`5`).
3. Coerces missing sentinels across all power generation types.
4. Deduplicates records on `(ba_code, date_key, hour_of_day)`.

### 3. Parameters and Data Types
* **`raw_grid`** (`List[Dict[str, Any]]`): Raw grid telemetry records (EIA-930).
* **`batch_id`** (`str`): Pipeline execution ID.
* **`spark_session`** (`Optional[Any]`, default `None`): Cloud Spark connection.

* **Returns** (`Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`):
  1. Conformed hourly grid telemetry records.
  2. Quarantined bad grid records.

### 4. Step-by-Step Explanation of Important Lines
* `dt = datetime.fromisoformat(str(raw_ts).strip().replace("Z", "+00:00"))`
  * Robustly parses international timestamps regardless of whether they end in `"Z"` (Zulu/UTC) or numeric offsets.
* `date_key = int(dt.strftime("%Y%m%d")); hour_of_day = dt.hour`
  * Extracts the calendar date and the exact hour (0 to 23) for simple joining.

### 5. Data Engineering Concept: Temporal Grain Synchronization
* **What is the concept?** When combining data from multiple completely different organizations (the Department of Energy, the EPA, and regional power grids), they all record time differently.
* **Why do data engineers care?** By breaking timestamps down into the universal pair `(date_key, hour_of_day)`, we allow business analysts to join smokestack emissions directly with grid stress and freezing winter weather!

---

# CATEGORY 6: Master Pipeline Orchestrator

The final function pulls all the pieces together into an automated, fault-tolerant workflow.

---

## Function 15: `run_silver_conformance_suite`

### 1. Code of the Function
```python
def run_silver_conformance_suite(
    spark_session=None,
    master_batch_id: Optional[str] = None,
    raw_inputs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Runs the complete Silver Conformance, Data Quality Filtering, and SCD-2 Pipeline.
    Loads raw Bronze inputs, validates thermodynamic bounds, routes dirty rows to quarantine,
    and produces conformed Silver tables in `dwbi_catalog.silver_conformed`.
    """
    master_batch_id = master_batch_id or bronze.generate_batch_id("SILVER_MASTER")
    start_time = datetime.now(timezone.utc)

    print("====================================================================")
    print(f"STARTING MASTER SILVER CONFORMANCE PIPELINE [Batch: {master_batch_id}]")
    print("====================================================================")

    # 1. Ingest Bronze baseline (use supplied raw inputs, read from Bronze Delta tables, or read from sample files)
    raw_weather_stations = None
    if raw_inputs:
        raw_gen = raw_inputs.get("raw_generators", [])
        raw_plants = raw_inputs.get("raw_plants", [])
        raw_gen923 = raw_inputs.get("raw_gen923_monthly", [])
        raw_weather = raw_inputs.get("raw_weather_hourly", [])
        raw_cems = raw_inputs.get("raw_cems_hourly", [])
        raw_grid = raw_inputs.get("raw_grid_hourly", [])
        raw_weather_stations = raw_inputs.get("raw_weather_stations")
    elif spark_session is not None:
        try:
            print("-> Reading raw records from Bronze Delta staging tables...")
            t_gen = config.get_table_fqn("BRONZE", "raw_eia860_generator")
            t_plants = config.get_table_fqn("BRONZE", "raw_eia860_plant")
            t_gen923 = config.get_table_fqn("BRONZE", "raw_eia923_monthly_generation")
            t_weather = config.get_table_fqn("BRONZE", "raw_noaa_isd_weather")
            t_cems = config.get_table_fqn("BRONZE", "raw_epa_hourly_emissions")
            t_grid = config.get_table_fqn("BRONZE", "raw_eia930_hourly_grid")
            t_stations = config.get_table_fqn("BRONZE", "raw_noaa_isd_station_history")

            raw_gen = [r.asDict() for r in spark_session.read.table(t_gen).collect()]
            raw_plants = [r.asDict() for r in spark_session.read.table(t_plants).collect()]
            raw_gen923 = [r.asDict() for r in spark_session.read.table(t_gen923).collect()]
            raw_weather = [r.asDict() for r in spark_session.read.table(t_weather).collect()]
            raw_cems = [r.asDict() for r in spark_session.read.table(t_cems).collect()]
            raw_grid = [r.asDict() for r in spark_session.read.table(t_grid).collect()]
            try:
                raw_weather_stations = [r.asDict() for r in spark_session.read.table(t_stations).collect()]
            except Exception:
                raw_weather_stations = None
            print(f"   ✓ Read from Bronze Delta: {len(raw_plants)} plants, {len(raw_gen)} generators, {len(raw_gen923)} monthly gen, {len(raw_weather)} weather, {len(raw_cems)} emissions, {len(raw_grid)} grid.")
        except Exception as e:
            print(f"! Notice: Could not read from Bronze Delta ({e}). Falling back to sample files.")
            raw_gen = None
    else:
        raw_gen = None

    if raw_gen is None and not raw_inputs:
        raw_eia860_gen_headers, raw_gen = bronze.extract_csv_records(
            "archived/scratch_api_tests/sample_data/sample_eia860_generator.csv",
            scan_keys=["Plant Code"],
            batch_id=master_batch_id
        )
        raw_eia860_plant_headers, raw_plants = bronze.extract_csv_records(
            "archived/scratch_api_tests/sample_data/sample_eia860_plant.csv",
            scan_keys=["Plant Code"],
            batch_id=master_batch_id
        )
        raw_eia923_headers, raw_gen923 = bronze.extract_csv_records(
            "archived/scratch_api_tests/sample_data/sample_eia923_monthly_generation.csv",
            scan_keys=["Plant Id"],
            batch_id=master_batch_id
        )
        raw_noaa_headers, raw_weather = bronze.extract_json_records(
            "archived/scratch_api_tests/sample_data/sample_noaa_isd_weather.json",
            batch_id=master_batch_id
        )
        _, raw_cems = bronze.extract_json_records(
            "archived/scratch_api_tests/sample_data/sample_epa_hourly_emissions.json",
            batch_id=master_batch_id
        )
        _, raw_grid = bronze.extract_json_records(
            "archived/scratch_api_tests/sample_data/sample_eia930_hourly_grid.json",
            batch_id=master_batch_id
        )

    # 2. Conform Plants Master
    print("-> Conforming Plants Master...")
    silver_plants, q_plants = conform_plants(raw_plants, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Plants: {len(silver_plants)} | Quarantined: {len(q_plants)}")

    # 3. Conform Generators (SCD Type 2 Lifecycle)
    print("-> Conforming Generators with SCD Type 2 tracking...")
    silver_generators, q_gen = conform_generators_scd2(
        raw_gen,
        batch_id=master_batch_id,
        effective_timestamp="2021-01-01 00:00:00"
    )
    raw_gen_updates = raw_inputs.get("raw_generator_updates", []) if raw_inputs else []
    if raw_gen_updates:
        silver_generators, q_gen_up = conform_generators_scd2(
            raw_gen_updates,
            batch_id=master_batch_id,
            existing_dim_records=silver_generators
        )
        q_gen.extend(q_gen_up)
    print(f"   ✓ Conformed Generators: {len(silver_generators)} | Quarantined: {len(q_gen)}")

    # 4. Conform Monthly Generation & Validate Heat Rates
    print("-> Conforming Monthly Generation & Fuel (Heat Rate Auditing)...")
    silver_923, q_923 = conform_monthly_generation(raw_gen923, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Monthly Generation: {len(silver_923)} | Quarantined: {len(q_923)}")

    # 5. Conform NOAA Weather & Coerce Sentinels
    print("-> Conforming NOAA Weather Observations...")
    silver_weather, q_weather = conform_weather_hourly(raw_weather, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Weather: {len(silver_weather)} | Quarantined: {len(q_weather)}")

    # 6. Conform EPA Hourly Emissions
    print("-> Conforming EPA Hourly Emissions Telemetry...")
    silver_emissions, q_emissions = conform_emissions_hourly(raw_cems, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Emissions: {len(silver_emissions)} | Quarantined: {len(q_emissions)}")

    # 7. Conform EIA-930 Grid Telemetry
    print("-> Conforming EIA-930 Hourly Grid Telemetry...")
    silver_grid, q_grid = conform_grid_hourly(raw_grid, batch_id=master_batch_id, spark_session=spark_session)
    print(f"   ✓ Clean Grid Telemetry: {len(silver_grid)} | Quarantined: {len(q_grid)}")

    total_conformed = (len(silver_plants) + len(silver_generators) + len(silver_923) + 
                       len(silver_weather) + len(silver_emissions) + len(silver_grid))
    total_quarantined = (len(q_plants) + len(q_gen) + len(q_923) + 
                         len(q_weather) + len(q_emissions) + len(q_grid))
    total_raw_read = (len(raw_plants) + len(raw_gen) + len(raw_gen923) + 
                      len(raw_weather) + len(raw_cems) + len(raw_grid))

    # Persist Conformed Silver Tables to Delta Lake in Databricks
    if spark_session is not None:
        try:
            from pyspark.sql.types import (
                StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, TimestampType
            )

            # Schemas defined here... (Plants, Gen, 923, Weather, Emissions, Grid, Quarantine)
            # ...
            if silver_plants:
                t_plants = config.get_table_fqn("SILVER", "silver_plants_master")
                spark_session.createDataFrame(silver_plants, schema=schema_plants).write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(t_plants)
                print(f"   ✓ Delta Table Saved: {t_plants}")

            # ... writing other silver tables and quarantine table ...
        except Exception as e:
            print(f"[WARN] Failed to write silver tables to Delta: {e}")

    # 8. Log Silver pipeline execution to etl_run_log
    bronze.log_etl_run(
        spark_session=spark_session,
        batch_id=master_batch_id,
        pipeline_step="SILVER_CONFORMANCE",
        source_system="MEDALLION_SILVER",
        records_read=total_raw_read,
        records_inserted=total_conformed,
        records_updated=0,
        records_rejected=total_quarantined,
        execution_status="SUCCESS",
        start_time=start_time,
        end_time=datetime.now(timezone.utc)
    )

    summary = {
        "master_batch_id": master_batch_id,
        "conformed_plants_count": len(silver_plants),
        "conformed_generators_count": len(silver_generators),
        "conformed_monthly_gen_count": len(silver_923),
        "conformed_weather_count": len(silver_weather),
        "conformed_emissions_count": len(silver_emissions),
        "conformed_grid_count": len(silver_grid),
        "total_conformed_records": total_conformed,
        "total_quarantined_records": total_quarantined,
        "execution_status": "SUCCESS",
        "silver_data": {
            "silver_plants": silver_plants,
            "silver_generators": silver_generators,
            "silver_monthly_generation": silver_923,
            "silver_weather_hourly": silver_weather,
            "silver_emissions_hourly": silver_emissions,
            "silver_grid_hourly": silver_grid,
            "raw_weather_stations": raw_weather_stations
        }
    }
    return summary
```

### 2. Purpose of This Function
This is the **Master Conductor** of the Silver Layer orchestra. It coordinates the entire workflow:
1. Loads raw data from the Bronze layer (either from cloud Delta Lake tables, sample files, or test inputs).
2. Sequentially executes the 6 specialized cleaning functions (Plants, Generators, Monthly Generation, Weather, Emissions, Grid).
3. Enforces strict schema definitions (`StructType` and `StructField`) to ensure every column has the exact right datatype.
4. Saves all cleaned tables to Databricks Delta Lake (`dwbi_catalog.silver_conformed.*`).
5. Appends all defective rows into the quarantine table (`dwbi_catalog.quarantine.rejected_records`).
6. Logs the complete run to the master audit log (`bronze_staging.etl_run_log`).
7. Returns a detailed dictionary summary for downstream Gold processing.

### 3. Parameters and Data Types
* **`spark_session`** (`Optional[Any]`, default `None`): The active Databricks Spark session. If provided, writes directly to cloud Delta Lake. If `None`, runs in pure Python standalone mode.
* **`master_batch_id`** (`Optional[str]`, default `None`): Master batch ID tracking the entire run.
* **`raw_inputs`** (`Optional[Dict[str, Any]]`, default `None`): In-memory raw datasets used during fast unit testing.

* **Returns** (`Dict[str, Any]`): A master summary report containing counts of conformed and quarantined records across all 6 tables, the execution status (`"SUCCESS"`), and the clean data dictionaries.

### 4. Step-by-Step Explanation of Important Lines
* `master_batch_id = master_batch_id or bronze.generate_batch_id("SILVER_MASTER")`
  * Generates a unique traceable batch identifier (e.g. `BATCH_SILVER_MASTER_20261118_123456`).
* `schema_plants = StructType([StructField("orispl_code", IntegerType(), True), ...])`
  * **Strict Schema Definition:** Explicitly defines the schema for Delta Lake so corrupt columns cannot sneak in.
* `spark_session.createDataFrame(...).write.format("delta").mode("overwrite").saveAsTable(...)`
  * Atomically saves the conformed table into cloud Delta Lake with ACID transaction protection.
* `bronze.log_etl_run(...)`
  * Automatically writes a permanent governance record into `dwbi_catalog.bronze_staging.etl_run_log`.

### 5. Data Engineering Concept: Pipeline Orchestration & End-to-End Governance
* **What is the concept?** Data engineering is not just about isolated functions; it is about building reliable, repeatable, self-documenting data pipelines.
* **Why do data engineers care?** If an automated job runs every night at 2:00 AM, the master orchestrator ensures that:
  - If a step fails, the error is caught and logged.
  - Data quality is verified before data ever reaches executive dashboards.
  - Full governance and data lineage are preserved from raw files to final analytics.

---

## Summary Comparison Table of All 15 Functions

| # | Function Name | Category | Primary Purpose | Key Data Engineering Concept |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `is_sentinel` | Foundation Cleaners | Detects fake missing-data symbols (`"."`, `"-9999"`, `"NM"`). | Missing Data Sentinel Detection |
| **2** | `coerce_sentinel` | Foundation Cleaners | Replaces fake symbols with official SQL `NULL` (`None`). | NULL Value Normalization |
| **3** | `try_cast_float` | Foundation Cleaners | Converts text with commas to floats without crashing. | Defensive Type Casting (`TRY_CAST`) |
| **4** | `try_cast_int` | Foundation Cleaners | Converts text/floats to clean whole integers. | Surrogate Key Type Coercion |
| **5** | `standardize_text` | Foundation Cleaners | Fixes accidental spaces and normalizes letter casing. | Text Harmonization & Case Normalization |
| **6** | `record_cleaning_step`| Quality & Auditing | Logs rows in, fixed, removed, and quarantined to CSV/Delta. | Row Conservation & Pipeline Observability |
| **7** | `quarantine_record` | Quality & Auditing | Routes defective records to a Dead-Letter Queue table. | Dead-Letter Queue (DLQ) & Zero-Data-Loss |
| **8** | `calculate_and_validate_heat_rate` | Domain Physics | Checks if fuel efficiency obeys laws of thermodynamics. | Domain-Driven Physics Validation |
| **9** | `conform_generators_scd2` | Historical Tracking | Tracks operational status changes over time. | Slowly Changing Dimensions (SCD Type 2) |
| **10**| `conform_plants` | Entity Conformance | Cleans and deduplicates master power plant directory. | Master Data Management (MDM) |
| **11**| `conform_monthly_generation` | Entity Conformance | Cleans monthly fuel/generation and builds date keys. | Periodic Snapshot Fact Preparation |
| **12**| `conform_weather_hourly` | Entity Conformance | Fixes weather sensor dropouts and cleans stations. | IoT Telemetry Missing Value Scrubbing |
| **13**| `conform_emissions_hourly` | Entity Conformance | Cleans smokestack CEMS emissions and validates hours. | High-Frequency Transactional Grain Enforcement |
| **14**| `conform_grid_hourly` | Entity Conformance | Parses UTC timestamps and standardizes grid regions. | Temporal Grain Synchronization |
| **15**| `run_silver_conformance_suite` | Master Orchestration| Runs all 6 steps, saves to Delta Lake, and logs run. | Pipeline Orchestration & End-to-End Governance |

---

*This reference document was generated for students and engineers working on the DL3004 Data Warehousing & Business Intelligence (DWBI) project at FAST-NUCES.*
