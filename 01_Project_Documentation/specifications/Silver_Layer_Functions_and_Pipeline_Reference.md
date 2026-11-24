# Silver Layer Functions & Pipeline Execution Reference
## Deep-Dive Technical Specification & Code Companion
**Source File:** [`03_ETL/02_silver_cleansing_and_scd.py`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py)  
**Work Package:** WP2 — Data Quality & Silver Conformance Lead (Rai Fahad Sultan, 24L-2509)  
**Target Catalog:** `dwbi_catalog.silver_conformed`, `dwbi_catalog.quarantine`  
**Runtime:** Dual Execution Mode (Databricks Serverless Apache Spark & Pure Python Standalone)

---

## Navigation & Function Map

The Silver Layer pipeline consists of **15 modular functions** organized into **6 functional groups**:

| Group | Function Name | Line Range | Primary Role |
| :--- | :--- | :--- | :--- |
| **Group 1: Foundation Cleaners** | [`is_sentinel`](#1-is_sentinelvalue) | Lines 60–75 | Detects missing-data sentinel characters. |
| | [`coerce_sentinel`](#2-coerce_sentinelvalue) | Lines 78–80 | Replaces sentinel characters with `None` (`NULL`). |
| | [`try_cast_float`](#3-try_cast_floatvalue) | Lines 83–95 | Safely converts unformatted text to decimal numbers. |
| | [`try_cast_int`](#4-try_cast_intvalue) | Lines 97–104 | Safely converts text/floats to whole integer keys. |
| | [`standardize_text`](#5-standardize_textvalue-mode) | Lines 106–130 | Strips whitespace and standardizes casing. |
| **Group 2: Auditing & Quarantine** | [`record_cleaning_step`](#6-record_cleaning_step) | Lines 137–196 | Logs row conservation metrics to CSV & Delta tables. |
| | [`quarantine_record`](#7-quarantine_record) | Lines 257–290 | Routes defective records to dead-letter quarantine. |
| **Group 3: Domain Physics** | [`calculate_and_validate_heat_rate`](#8-calculate_and_validate_heat_rate) | Lines 202–250 | Computes heat rate and enforces thermodynamic limits. |
| **Group 4: SCD Type 2 Tracking** | [`conform_generators_scd2`](#9-conform_generators_scd2) | Lines 384–530 | Tracks generator lifecycle transitions over time. |
| **Group 5: Table Conformance** | [`conform_plants`](#10-conform_plants) | Lines 296–382 | Cleans and deduplicates EIA-860 power plants. |
| | [`conform_monthly_generation`](#11-conform_monthly_generation) | Lines 532–648 | Cleans EIA-923 fuel and applies heat rate audits. |
| | [`conform_weather_hourly`](#12-conform_weather_hourly) | Lines 649–721 | Cleans NOAA ISD synoptic weather observations. |
| | [`conform_emissions_hourly`](#13-conform_emissions_hourly) | Lines 723–860 | Cleans EPA CAMPD hourly smokestack emissions. |
| | [`conform_grid_hourly`](#14-conform_grid_hourly) | Lines 862–980 | Cleans EIA-930 hourly grid power telemetry. |
| **Group 6: Master Orchestrator** | [`run_silver_conformance_suite`](#15-run_silver_conformance_suite) | Lines 986–1132 | Orchestrates full pipeline from Bronze to Silver. |

---

# GROUP 1: Foundation Data Cleaners

---

### 1. `is_sentinel(value)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L60-L75`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L60-L75)

#### What is this function doing?
Determines if an input value is a dummy placeholder used by federal agencies or weather sensors to indicate missing data, rather than legitimate information.

#### External & Global Variables Used:
* **`SENTINEL_SET` (Global Set at lines 54–57):**
  ```python
  SENTINEL_SET = {
      ".", "NM", "*", "--", "NA", "N/A", "null", "NULL", "None", "", "   ",
      "-9999", "-9999.0", -9999, -9999.0
  }
  ```
  Contains every documented missing-data symbol across EIA, EPA, and NOAA datasets.

#### Inputs & Outputs:
* **Inputs:** `value: Any` (Can be string, float, integer, or `None`).
* **Output:** `bool` (`True` if the value is a placeholder, `False` if real data).

#### How is this function being used?
Called by `coerce_sentinel()`, `try_cast_float()`, and `standardize_text()`. It is the central authority on what constitutes missing data across the entire repository.

#### Main Lines in Code:
```python
if value is None:
    return True
if isinstance(value, str):
    v_stripped = value.strip()
    if v_stripped in SENTINEL_SET:
        return True
    try:
        return float(v_stripped) == -9999.0
    except ValueError:
        return False
if isinstance(value, (int, float)):
    return value == -9999 or value == -9999.0
return False
```
* Safely strips whitespace so `" . "` matches `"."`.
* Safely converts strings to float to detect decimal formats of sensor dropouts like `"-9999.00"`.

#### Apache Spark Connection:
Maps directly to Spark SQL expressions:
```sql
CASE WHEN raw_col IN ('.', 'NM', '*', '--') OR raw_col = '-9999' THEN TRUE ELSE FALSE END
```

#### Data Engineering Concept:
* **Missing Value Sentinel Auditing:** Standardizing diverse domain-specific absence representations.

---

### 2. `coerce_sentinel(value)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L78-L80`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L78-L80)

#### What is this function doing?
Replaces any identified sentinel placeholder with Python `None` (which translates to SQL `NULL`), leaving legitimate values unchanged.

#### External & Global Variables Used:
* Calls `is_sentinel(value)`.

#### Inputs & Outputs:
* **Inputs:** `value: Any`.
* **Output:** `Optional[Any]` (`None` if sentinel, else original value).

#### How is this function being used?
Used across all conformance engines when non-numeric text columns need sentinels removed without altering valid string contents.

#### Main Lines in Code:
```python
return None if is_sentinel(value) else value
```

#### Apache Spark Connection:
Equivalent to Databricks SQL `NULLIF()`:
```sql
NULLIF(raw_col, '.')
```

#### Data Engineering Concept:
* **Null Normalization:** Ensuring all absence representations collapse to a single database primitive.

---

### 3. `try_cast_float(value)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L83-L95`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L83-L95)

#### What is this function doing?
Defensively converts text, numbers, or unformatted strings into floating-point decimals. Automatically removes commas and returns `None` on unparseable data rather than raising exceptions.

#### External & Global Variables Used:
* Calls `is_sentinel(value)`.

#### Inputs & Outputs:
* **Inputs:** `value: Any` (e.g. `"1,500.5"`, `"45.2"`, `"."`, `"ERROR"`).
* **Output:** `Optional[float]` (`1500.5`, `45.2`, or `None`).

#### How is this function being used?
Called by all fact and measure parsers: fuel quantities, generation megawatt-hours, emissions masses ($\text{SO}_2, \text{NO}_x, \text{CO}_2$), and temperatures.

#### Main Lines in Code:
```python
if is_sentinel(value):
    return None
try:
    cleaned_str = str(value).replace(",", "").strip()
    return float(cleaned_str)
except (ValueError, TypeError):
    return None
```
* `.replace(",", "")` removes formatting commas that crash standard numeric conversion routines.
* `except (ValueError, TypeError)` catches corrupted inputs without terminating the batch.

#### Apache Spark Connection:
Replicates Databricks Photon and Spark SQL's ANSI `TRY_CAST`:
```sql
TRY_CAST(REPLACE(col, ',', '') AS DOUBLE)
```

#### Data Engineering Concept:
* **Defensive Type Casting & Fault-Tolerant Parsing:** Prevents runtime aborts on petabyte-scale pipelines.

---

### 4. `try_cast_int(value)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L97-L104`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L97-L104)

#### What is this function doing?
Safely converts inputs to whole integers (`int`), resolving decimal formatting glitches introduced by Excel.

#### External & Global Variables Used:
* Calls `try_cast_float(value)`.

#### Inputs & Outputs:
* **Inputs:** `value: Any` (e.g. `"2021"`, `"3.0"`, `3.0`, `"."`).
* **Output:** `Optional[int]` (`2021`, `3`, or `None`).

#### How is this function being used?
Called when parsing primary keys, surrogate foreign keys, calendar years, and operating hours (`0–23`).

#### Main Lines in Code:
```python
f_val = try_cast_float(value)
return int(round(f_val)) if f_val is not None else None
```
* Reuses `try_cast_float()` to strip commas, sentinels, and spaces.
* `round()` handles Excel decimal artifacts like `"3.0"`, which cause Python's raw `int("3.0")` to throw `ValueError`.

#### Apache Spark Connection:
Equivalent to Databricks SQL:
```sql
TRY_CAST(col AS BIGINT)
```

#### Data Engineering Concept:
* **Key Normalization:** Preparing integer relational keys for high-performance hash joins.

---

### 5. `standardize_text(value, mode="title")`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L106-L130`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L106-L130)

#### What is this function doing?
Cleans string columns by stripping outer whitespace, collapsing multiple internal spaces into a single space, removing sentinels, and enforcing consistent letter casing.

#### External & Global Variables Used:
* `re` module (Regular Expressions, standard library).
* Calls `is_sentinel(value)`.

#### Inputs & Outputs:
* **Inputs:**
  * `value: Any`: String or object to standardize.
  * `mode: str`: Casing mode: `"title"` (default), `"upper"`, or `"lower"`.
* **Output:** `Optional[str]` (Cleaned string or `None`).

#### How is this function being used?
Called by all dimensional entity cleaners:
* `plant_name`, `utility_name`, `county_name`, `ba_name` $\rightarrow$ `mode="title"`
* `state_code`, `ba_code`, `prime_mover_code`, `generator_id` $\rightarrow$ `mode="upper"`

#### Main Lines in Code:
```python
val_str = str(value).strip()
collapsed = re.sub(r"\s+", " ", val_str)
if mode == "title":
    return collapsed.title()
elif mode == "upper":
    return collapsed.upper()
```
* `re.sub(r"\s+", " ", val_str)` collapses `"Barry    Plant"` into `"Barry Plant"`.

#### Apache Spark Connection:
Equivalent Spark SQL:
```sql
INITCAP(REGEXP_REPLACE(TRIM(col), '\\s+', ' '))  -- For Title Case
UPPER(TRIM(col))                                  -- For Uppercase
```

#### Data Engineering Concept:
* **Categorical Standardization:** Eliminating grouping fragmentation in OLAP cubes and dashboards.

---

# GROUP 2: Audit Logging & Dead-Letter Quarantine

---

### 6. `record_cleaning_step(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L137-L196`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L137-L196)

#### What is this function doing?
Maintains an immutable audit ledger of transformation metrics for every conformed dataset. Records rows in, rows modified, rows deduplicated, rows quarantined, and rows out.

#### External & Global Variables Used:
* **`CLEANING_STEP_LOG` (Global List at line 134):** In-memory storage for test assertion.
* **`MODULE_DIR` (Path at line 33):** Locates `02_Data/cleaned_data/cleaning_step_log.csv`.
* **`config.get_table_fqn("SILVER", "cleaning_step_log")`:** Unity Catalog 3-tier table name.
* **`csv` & `datetime` modules.**

#### Inputs & Outputs:
* **Inputs:**
  * `batch_id: str`: Execution run UUID.
  * `step_name: str`: Task label (e.g. `"CONFORM_PLANTS"`).
  * `target_table: str`: Destination table name.
  * `rows_in: int`, `rows_changed: int`, `rows_removed: int`, `rows_quarantined: int`.
  * `rows_out: Optional[int]`: Final row count (auto-computed if omitted).
  * `spark_session`: Active Databricks Spark session (optional).
* **Output:** `Dict[str, Any]` (Audit record dictionary).

#### How is this function being used?
Invoked at the final return statement of **every table conformance function** in Group 5.

#### Main Lines in Code:
```python
if rows_out is None:
    rows_out = rows_in - rows_removed - rows_quarantined
entry = {...}
CLEANING_STEP_LOG.append(entry)
# Persist to CSV and Delta Lake:
if spark_session is not None:
    df_log = spark_session.createDataFrame([Row(**entry)])
    df_log.write.format("delta").mode("append").saveAsTable(log_table)
```

#### Apache Spark Connection:
Appends records into Delta Lake with full ACID transaction guarantees:
```python
df_log.write.format("delta").mode("append").saveAsTable("dwbi_catalog.silver_conformed.cleaning_step_log")
```

#### Data Engineering Concept:
* **Pipeline Observability & Conservation of Rows:** Guarantees $\text{Rows In} = \text{Rows Out} + \text{Quarantined} + \text{Deduplicated}$.

---

### 7. `quarantine_record(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L257-L290`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L257-L290)

#### What is this function doing?
Isolates defective, malformed, or physically impossible records into a Dead-Letter Queue (DLQ) table without halting the pipeline or discarding raw evidence.

#### External & Global Variables Used:
* **`QUARANTINE_HISTORY` (Global List at line 47):** In-memory storage.
* **`config.get_table_fqn("QUARANTINE", "rejected_records")`:** `"dwbi_catalog.quarantine.rejected_records"`.
* **`json.dumps(..., default=str)`:** Safely serializes raw dictionaries to JSON strings.

#### Inputs & Outputs:
* **Inputs:**
  * `batch_id: str`: Execution run ID.
  * `source_system: str`: Agency name (`"EIA-860"`, `"EPA-CAMPD"`).
  * `source_table: str`: Staging table name.
  * `source_row_identifier: str`: Natural key of bad row.
  * `rejection_reason: str`: Standardized failure code.
  * `raw_payload: Dict[str, Any]`: Complete raw row dictionary.
  * `spark_session`: Active Databricks session (optional).
* **Output:** `Dict[str, Any]` (Quarantine envelope record).

#### How is this function being used?
Called by conformance engines whenever a record has missing natural keys, invalid timestamps, or out-of-bounds heat rates.

#### Main Lines in Code:
```python
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
```

#### Apache Spark Connection:
Directly writes into the Delta Lake table `dwbi_catalog.quarantine.rejected_records`.

#### Data Engineering Concept:
* **Dead-Letter Queue (DLQ) Pattern:** Isolating poisoned records for post-mortem diagnostics and zero data destruction.

---

# GROUP 3: Domain Physics & Thermodynamic Validation

---

### 8. `calculate_and_validate_heat_rate(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L202-L250`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L202-L250)

#### What is this function doing?
Calculates thermal heat rate efficiency ($\text{Btu/kWh}$) and validates the result against technology-specific physical boundaries. Identifies and protects negative net generation maintenance events.

#### External & Global Variables Used:
* **`config.DATA_QUALITY_RULES["HEAT_RATE_BOUNDS"]`:**
  * `CCGT`: 5,000–14,000 Btu/kWh
  * `COAL_ST`: 8,500–18,000 Btu/kWh
  * `PEAKER_GT`: 9,000–22,000 Btu/kWh
* Calls `try_cast_float()`.

#### Inputs & Outputs:
* **Inputs:**
  * `fuel_mmbtu_val: Any`: Fuel consumed in MMBtu.
  * `netgen_mwh_val: Any`: Net electrical output in MWh.
  * `prime_mover_code: Optional[str]`: Engine type (`"CC"`, `"ST"`, `"GT"`).
* **Output:** `Tuple[Optional[float], bool, Optional[str]]`
  * Item 1: `heat_rate` value (or `None`).
  * Item 2: `is_valid` (`True` if valid or handled exception; `False` if physical violation).
  * Item 3: `status_code` (`"PHYSICALLY_VALID"`, `"STATION_SERVICE_EXCEEDS_OUTPUT"`, or rejection reason).

#### How is this function being used?
Called by `conform_monthly_generation()` inside its monthly iteration loop.

#### Main Lines in Code:
```python
if netgen_mwh < 0:
    return None, True, "STATION_SERVICE_EXCEEDS_OUTPUT"
if netgen_mwh == 0:
    return None, True, "ZERO_GENERATION_STANDBY"
heat_rate = (fuel_mmbtu * 1000.0) / netgen_mwh
# Boundary comparison:
if heat_rate < bounds["min"] or heat_rate > bounds["max"]:
    return round(heat_rate, 2), False, f"HEAT_RATE_OUT_OF_BOUNDS_{category}..."
return round(heat_rate, 2), True, "PHYSICALLY_VALID"
```

#### Apache Spark Connection:
Replicated in Databricks SQL Quality Checks ([`04_SQL/quality_checks.sql#L55-L84`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/04_SQL/quality_checks.sql#L55-L84)).

#### Data Engineering Concept:
* **Domain-Driven Semantic Validation:** Verifying scientific and mechanical reality in engineering datasets.

---

# GROUP 4: Slowly Changing Dimensions (SCD Type 2)

---

### 9. `conform_generators_scd2(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L384-L530`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L384-L530)

#### What is this function doing?
Implements Ralph Kimball's **SCD Type 2** design pattern to track the historical operational lifecycle of electric power generators (`OP` $\rightarrow$ `SB` $\rightarrow$ `RE`) across time horizons.

#### External & Global Variables Used:
* Calls `quarantine_record()`, `record_cleaning_step()`, `try_cast_int()`, `try_cast_float()`, `standardize_text()`.

#### Inputs & Outputs:
* **Inputs:**
  * `raw_generators: List[Dict[str, Any]]`: Raw EIA-860 generator rows.
  * `batch_id: str`: Run UUID.
  * `existing_dim_records: Optional[List[Dict[str, Any]]]`: Current table state (if incremental update).
  * `effective_timestamp: Optional[str]`: State transition timestamp.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]` (`(all_conformed, quarantined)`).

#### How is this function being used?
Called by `run_silver_conformance_suite()` in two passes:
1. Baseline load (`effective_timestamp="2021-01-01 00:00:00"`).
2. Incremental updates (when unit status transitions are processed).

#### Main Lines in Code:
```python
nat_key = (orispl, gen_id)
if nat_key in existing_map:
    prior = existing_map[nat_key]
    if prior["operating_status"] != std_status:
        # Expire old row:
        prior["valid_to"] = row_effective_time
        prior["is_current"] = False
        conformed_updates.append(dict(prior))
        # Insert new active version:
        new_version = dict(prior)
        new_version["operating_status"] = std_status
        new_version["valid_from"] = row_effective_time
        new_version["valid_to"] = "9999-12-31 23:59:59"
        new_version["is_current"] = True
        existing_map[nat_key] = new_version
```

#### Apache Spark Connection:
Implemented on Databricks Delta Lake via `MERGE INTO ... WHEN MATCHED ... UPDATE SET * EXCEPT (generator_key)`.

#### Data Engineering Concept:
* **Slowly Changing Dimension Type 2 (SCD-2):** Preserves point-in-time analytical truth.

---

# GROUP 5: Table Conformance Engines

---

### 10. `conform_plants(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L296-L382`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L296-L382)

#### What is this function doing?
Conforms and deduplicates EIA-860 Plant Master records. Standardizes plant, county, and utility names to Title Case; sets state and BA codes to Uppercase; coerces coordinates to floats; and quarantines invalid ORISPL codes.

#### Inputs & Outputs:
* **Inputs:** `raw_plants: List[Dict[str, Any]]`, `batch_id: str`, `spark_session=None`.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]` (`(conformed_plants, quarantined)`).

#### Deduplication & Quarantine Rules:
* **Natural Key:** `orispl_code`.
* **Quarantine Trigger:** `orispl is None or orispl <= 0` $\rightarrow$ `"INVALID_ORISPL_CODE"`.
* **Deduplication:** Keeps latest record, increments `rows_removed`.

---

### 11. `conform_monthly_generation(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L532-L648`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L532-L648)

#### What is this function doing?
Conforms EIA-923 Monthly Generation & Fuel data. Unpivots or standardizes monthly records, calls `calculate_and_validate_heat_rate()`, allows negative net generation, computes `month_start_date_key` (`YYYYMMDD`), and quarantines thermodynamic violations.

#### Inputs & Outputs:
* **Inputs:** `raw_gen_records: List[Dict[str, Any]]`, `batch_id: str`, `spark_session=None`.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`.

#### Deduplication & Quarantine Rules:
* **Natural Key:** `(orispl_code, prime_mover_code, energy_source_code, month_start_date_key)`.
* **Quarantine Trigger:** `is_valid == False` from heat rate validation $\rightarrow$ `"HEAT_RATE_OUT_OF_BOUNDS_..."`.

---

### 12. `conform_weather_hourly(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L649-L721`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L649-L721)

#### What is this function doing?
Conforms NOAA ISD surface weather observations. Coerces `-9999` sensor dropouts to `NULL`, standardizes `station_id` to uppercase, validates UTC timestamps, and logs cleaning metrics.

#### Inputs & Outputs:
* **Inputs:** `raw_weather_records: List[Dict[str, Any]]`, `batch_id: str`, `spark_session=None`.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`.

#### Deduplication & Quarantine Rules:
* **Quarantine Trigger:** Corrupt timestamps or missing `station_id` $\rightarrow$ `"INVALID_OR_CORRUPT_TIMESTAMP"`.
* **Sentinel Rule:** Air temp or wind speed equal to `-9999` $\rightarrow$ coerced to `None` (`NULL`).

---

### 13. `conform_emissions_hourly(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L723-L860`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L723-L860)

#### What is this function doing?
Conforms EPA CAMPD Continuous Emission Monitoring System (CEMS) hourly smokestack telemetry. Validates dates (`YYYY-MM-DD` $\rightarrow$ `YYYYMMDD`), checks hour ranges ($0 \le \text{hour} \le 23$), parses emissions masses ($\text{SO}_2, \text{NO}_x, \text{CO}_2$), and deduplicates on `(orispl_code, unit_id, date_key, hour_of_day)`.

#### Inputs & Outputs:
* **Inputs:** `raw_emissions: List[Dict[str, Any]]`, `batch_id: str`, `spark_session=None`.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`.

#### Deduplication & Quarantine Rules:
* **Quarantine Triggers:**
  * Missing plant code $\rightarrow$ `"INVALID_ORISPL_CODE"`
  * Invalid date $\rightarrow$ `"INVALID_DATE_KEY"`
  * Hour not in 0–23 $\rightarrow$ `"INVALID_HOUR_RANGE"`

---

### 14. `conform_grid_hourly(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L862-L980`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L862-L980)

#### What is this function doing?
Conforms EIA-930 hourly grid telemetry across regional Balancing Authorities. Coerces sentinels on power demand and fuel generation mix (coal, gas, nuclear, hydro, wind, solar), parses ISO timestamps into `date_key` and `hour_of_day`, and standardizes `ba_code` to uppercase.

#### Inputs & Outputs:
* **Inputs:** `raw_grid: List[Dict[str, Any]]`, `batch_id: str`, `spark_session=None`.
* **Output:** `Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`.

#### Deduplication & Quarantine Rules:
* **Natural Key:** `(ba_code, date_key, hour_of_day)`.
* **Quarantine Triggers:** Missing `ba_code` $\rightarrow$ `"MISSING_BA_CODE"`, Unparseable timestamp $\rightarrow$ `"INVALID_GRID_TIMESTAMP"`.

---

# GROUP 6: Master Pipeline Orchestrator

---

### 15. `run_silver_conformance_suite(...)`
* **Location:** [`03_ETL/02_silver_cleansing_and_scd.py#L986-L1132`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/03_ETL/02_silver_cleansing_and_scd.py#L986-L1132)

#### What is this function doing?
The top-level orchestrator for the entire Silver Layer. Executes all 5 conformance steps in sequence, logs overall pipeline metrics to `dwbi_catalog.bronze_staging.etl_run_log`, and returns a structured summary payload containing all conformed datasets for the Gold Star Schema loader.

#### External & Global Variables Used:
* Calls all functions from Groups 1 through 5.
* **`bronze.generate_batch_id("SILVER_MASTER")`**
* **`bronze.log_etl_run(...)`**

#### Inputs & Outputs:
* **Inputs:**
  * `spark_session`: Active Databricks session (optional).
  * `master_batch_id: Optional[str]`: Global run UUID.
  * `raw_inputs: Optional[Dict[str, Any]]`: Pre-loaded Bronze tables (if executing from pipeline runner).
* **Output:** `Dict[str, Any]` (Execution summary holding record counts, status, and cleaned data structures).

#### Execution Sequence:
1. Generates master batch ID.
2. Ingests raw inputs from Bronze or extracts from disk.
3. Conforms Plants $\rightarrow$ `silver_plants`.
4. Conforms Generators with SCD-2 $\rightarrow$ `silver_generators`.
5. Conforms Monthly Generation & Heat Rates $\rightarrow$ `silver_monthly_generation`.
6. Conforms Weather Observations $\rightarrow$ `silver_weather_hourly`.
7. Conforms Smokestack Emissions $\rightarrow$ `silver_emissions_hourly`.
8. Conforms Regional Grid Telemetry $\rightarrow$ `silver_grid_hourly`.
9. Logs pipeline execution metrics to `etl_run_log`.
10. Returns clean dataset dictionary to Gold Warehouse.

---

## 3. How to Run and Test This Pipeline

### Run Standalone via Terminal:
```powershell
uv run python 03_ETL/02_silver_cleansing_and_scd.py
```

### Run Full Unit Test Suite:
```powershell
uv run python -m unittest tests/unit/test_silver_cleansing.py
```

### Run End-to-End Medallion Pipeline (Bronze $\rightarrow$ Silver $\rightarrow$ Gold):
```powershell
uv run python 03_ETL/05_run_pipeline.py
```
