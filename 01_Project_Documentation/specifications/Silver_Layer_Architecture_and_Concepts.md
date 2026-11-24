# Silver Layer Architecture, Data Quality & Engineering Concepts
## U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse
**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)  
**Academic Institution:** FAST National University of Computer and Emerging Sciences  
**Work Package:** WP2 — Data Quality & Silver Conformance Lead (Rai Fahad Sultan, 24L-2509)  
**Target Platform:** Databricks Serverless Cloud Lakehouse (Apache Spark & Delta Lake)  
**Target Catalog:** `dwbi_catalog` (`silver_conformed`, `quarantine`)  

---

## 1. Executive Summary & Medallion Architecture Role

In the Databricks Medallion Lakehouse architecture, the data processing lifecycle is structured into three progressive tiers: **Bronze (Raw Staging)**, **Silver (Conformed & Cleansed)**, and **Gold (Dimensional Star Schema & Analytical Marts)**.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MEDALLION LAKEHOUSE LIFECYCLE                         │
└─────────────────────────────────────────────────────────────────────────────────┘

 ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
 │       BRONZE LAYER        │      │       SILVER LAYER        │      │        GOLD LAYER         │
 │     (Raw Staging)         │ ───► │   (Conformed & Cleansed)  │ ───► │  (Star Schema & Marts)    │
 │                           │      │                           │      │                           │
 │ • Append-only ingestion   │      │ • Sentinel coercion       │      │ • Kimball Star Schema     │
 │ • Preserves source quirks │      │ • Text standardization    │      │ • Conformed dimensions    │
 │ • Shifting Excel headers  │      │ • Defensive TRY_CAST      │      │ • Multi-grain facts       │
 │ • Multi-source raw files  │      │ • Thermodynamic bounds    │      │ • Liquid clustering       │
 │ • etl_run_log audit trail │      │ • SCD Type 2 tracking     │      │ • Power BI DirectQuery    │
 └───────────────────────────┘      │ • Dead-letter quarantine  │      └───────────────────────────┘
                                    └─────────────┬─────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │     QUARANTINE LAYER      │
                                    │   (Dead-Letter Queue)     │
                                    │                           │
                                    │ • Isolated bad records    │
                                    │ • Typed rejection reasons │
                                    │ • Full JSON raw payloads  │
                                    │ • Zero data destruction   │
                                    └───────────────────────────┘
```

### Why Can't We Jump Directly from Bronze to Gold?
Raw government and environmental feeds are inherently heterogeneous, inconsistent, and dirty:
1. **Federal Missing Sentinels:** EIA and NOAA datasets do not use standard database `NULL` values; they use literal strings (`"."`, `"NM"`, `"--"`) and sensor dropouts (`-9999`).
2. **Text Inconsistencies:** Agency data includes arbitrary casing (`"BARRY"`, `"barry "`), inconsistent whitespace, and formatting commas in numeric fields (`"1,250.5"`).
3. **Physical Impossibilities:** Transmission errors and reporting bugs can introduce heat rates that violate the laws of thermodynamics.
4. **Temporal State Drift:** Power plant generators change operational statuses over time (operating, standby, retired). Directly loading raw snapshots into facts causes historical distortion.

The **Silver Layer** acts as the definitive enterprise gatekeeper. It enforces data quality, conforms entities into an integrated crosswalk topology, tracks historical evolution, and quarantines defective records without destroying raw evidence.

---

## 2. Concept 1: Sentinel Value Coercion & Missing Data Handling

### The Problem in Federal Datasets
Public government datasets employ legacy alphanumeric codes called **sentinels** to explain why data is absent:
* **EIA-860 & EIA-923 (Department of Energy):**
  * `"."` = Data is withheld to protect commercial confidentiality.
  * `"NM"` = Not Meaningful (e.g., heat rate cannot be calculated).
  * `"*"` = Data is negligible or rounded to zero.
  * `"--"` = Value was omitted by the reporting utility.
* **NOAA ISD (National Oceanic & Atmospheric Administration):**
  * `-9999` or `-9999.0` = Weather sensor dropout or communications failure.

### The Analytical Risk
If an analyst executes an aggregation query on raw data:
```sql
SELECT AVG(air_temperature_c) FROM bronze_staging.raw_noaa_isd_weather;
```
If sensor dropouts (`-9999`) remain in the dataset, the average temperature calculated will be absurd (e.g., $-450^\circ\text{C}$). If string sentinels (`"."`) reside in numeric columns, modern SQL warehouses running in ANSI SQL mode **abort the query immediately with a fatal conversion exception**.

### The Silver Coercion Policy
The Silver Layer enforces a universal policy: **All federal sentinels must be coerced to SQL `NULL` (`None` in Python)** before entering downstream processing.
* Standard SQL aggregations (`AVG()`, `SUM()`, `MIN()`, `MAX()`) natively ignore `NULL` values.
* Coercing sentinels to `NULL` enables seamless mathematical computations while mathematically preserving row counts.

---

## 3. Concept 2: Defensive Type Casting & ANSI SQL Mode Compliance

### Fatal Casting vs. Defensive Casting
Modern enterprise cloud data warehouses (Databricks Photon, Snowflake, PostgreSQL 16) enable **ANSI SQL compliance** by default:
* **Legacy Mode:** Invalid casts silently converted bad data to `0` or `NULL`.
* **ANSI SQL Mode:** A statement like `CAST('12.5A' AS DOUBLE)` or `CAST('.' AS INT)` throws a **fatal runtime exception** and halts the entire pipeline.

### The Defensive Casting Pattern (`TRY_CAST`)
To guarantee that a batch containing millions of rows is not aborted due to a single malformed cell, the Silver Layer enforces **defensive casting**:
1. **Cleaning Outer Characters:** Strips leading/trailing spaces and removes formatting commas (`"1,500.25"` $\rightarrow$ `"1500.25"`).
2. **Sentinel Pre-Check:** Immediately evaluates if the string belongs to `SENTINEL_SET`.
3. **Safe Evaluation (`TRY_CAST`):** If conversion succeeds, returns the typed value; if conversion throws a `ValueError` or `TypeError`, it safely returns `None`.

In Databricks SQL, this is written as:
```sql
SELECT 
    TRY_CAST(REPLACE(gross_load_mw, ',', '') AS DOUBLE) AS gross_load_mw,
    TRY_CAST(plant_code AS INT) AS orispl_code
FROM dwbi_catalog.bronze_staging.raw_epa_hourly_emissions;
```

---

## 4. Concept 3: Text Normalization & Categorical Conformance

### The Analytical Problem of Dirty Text
When different agencies report on the same entity, textual divergence causes severe business intelligence defects:
* Utility A reports: `"ALABAMA"`
* Utility B reports: `"Alabama "` (with a trailing space)
* Utility C reports: `"alabama"`

In SQL, executing `GROUP BY state_code` will treat these as three completely different geographic regions, creating duplicate bars in Power BI charts and corrupting geographic drill-downs.

### Conformance Transformations
The Silver Layer standardizes every text attribute according to strict categorical rules:
1. **Whitespace Trimming:** Removes leading and trailing spaces via `.strip()`.
2. **Internal Space Collapsing:** Replaces multi-space gaps (`"Barry    Plant"`) with a single space using regular expressions (`\s+`).
3. **Casing Standardization:**
   * **Title Case (`mode="title"`):** Descriptive natural language entities (`plant_name`, `county_name`, `utility_name`, `ba_name`) $\rightarrow$ `"Barry Steam Plant"`.
   * **Uppercase (`mode="upper"`):** Relational keys, codes, and abbreviations (`state_code`, `ba_code`, `prime_mover_code`, `operating_status`) $\rightarrow$ `"AL"`, `"PJM"`, `"CC"`, `"OP"`.

---

## 5. Concept 4: Domain-Driven Semantic Validation & Thermodynamic Physics

### Syntactic Quality vs. Semantic Quality
* **Syntactic Quality:** Verifies that a field is a valid decimal number (e.g., `12.5` is a valid float).
* **Semantic Quality:** Verifies that the number obeys the physical laws of the real-world domain.

### The Physics of Heat Rate
In power engineering, thermal efficiency is measured by the **Heat Rate**: the quantity of fuel energy burned to produce one unit of electrical energy:
$$\text{Heat Rate (Btu/kWh)} = \frac{\text{Fuel Consumed (MMBtu)} \times 1,000}{\text{Net Generation (MWh)}}$$

* Lower heat rate = More efficient plant (less fuel required per kWh).
* Higher heat rate = Less efficient plant (more fuel wasted as heat).

### Technology-Specific Thermodynamic Boundaries
Mechanical engineers have established rigorous thermodynamic limits for each prime mover technology:

| Technology | Prime Mover Codes | Minimum Realistic Heat Rate | Maximum Realistic Heat Rate | Physical Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **Combined Cycle Gas Turbine (CCGT)** | `CA`, `CT`, `CS`, `CC` | **5,000 Btu/kWh** | **14,000 Btu/kWh** | Modern CCGT waste-heat recovery achieves thermal efficiencies between 40% and 60%. Values $< 5,000$ violate the Carnot cycle limit. |
| **Coal Steam Turbines** | `ST` | **8,500 Btu/kWh** | **18,000 Btu/kWh** | Subcritical and supercritical boilers operate between 25% and 38% efficiency. Values $> 18,000$ indicate massive fuel leaks or measurement failures. |
| **Simple Cycle Gas Peakers** | `GT` | **9,000 Btu/kWh** | **22,000 Btu/kWh** | Aeroderivative turbines designed for rapid peaking service operate at lower thermal efficiency. |
| **General Thermal Fleet** | Other thermal | **4,500 Btu/kWh** | **30,000 Btu/kWh** | Fleet-wide sanity boundary for internal combustion and biomass units. |

Records with heat rates outside these boundaries are physically impossible and indicate corrupted telemetry or unit misreporting. They are routed directly to the quarantine layer.

---

## 6. Concept 5: Real-World Business Rule Exceptions (Negative Net Generation)

### The Station Service / Auxiliary Power Draw Phenomenon
A common beginner mistake in energy data engineering is adding a naive check: `CHECK (net_generation_mwh >= 0)`.

**In the real world, Net Generation can be legitimately negative:**
1. Power plants require massive amounts of electrical power to run auxiliary equipment: boiler feedwater pumps, emissions scrubbers, cooling tower fans, transformer banks, and safety instrumentation.
2. During scheduled maintenance or forced outages, the turbine generators are completely offline ($\text{Gross Generation} = 0\text{ MWh}$).
3. However, the plant **continues to draw electricity from the high-voltage transmission grid** to maintain auxiliary systems.
4. Because $\text{Net Generation} = \text{Gross Output} - \text{Auxiliary Power}$, the resulting net generation is negative:
   $$\text{Net Generation} = 0 - 50\text{ MWh} = -50\text{ MWh}$$

### The Silver Handling Rule
The Silver layer explicitly recognizes negative net generation as a **valid business event**:
* It is **never** quarantined.
* Heat rate calculation is bypassed (flagged as `STATION_SERVICE_EXCEEDS_OUTPUT`), because dividing fuel by negative generation produces a nonsensical negative heat rate.
* The negative value is preserved intact for downstream financial and grid stress accounting.

---

## 7. Concept 6: The Dead-Letter Queue (DLQ) & Quarantine Isolation Pattern

### The Anti-Pattern of Silent Row Dropping
In traditional ETL, defective rows are frequently discarded via `WHERE` clauses:
```sql
-- DANGEROUS ANTI-PATTERN: SILENT DATA DESTRUCTION
INSERT INTO silver_plants
SELECT * FROM bronze_plants WHERE orispl_code IS NOT NULL;
```
This violates fundamental data governance:
* Data simply vanishes with no record of who dropped it, when, or why.
* Pipeline audits cannot prove whether records were lost in transmission or intentionally rejected.
* Corrupted records cannot be repaired or reprocessed.

### The Quarantine Pattern (`quarantine.rejected_records`)
The Silver Layer implements a formal **Dead-Letter Queue (DLQ)** pattern:
```
Raw Bronze Record ───► [Quality & Physics Validation]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
      [Passed All Rules]                    [Violated Rule]
            │                                     │
            ▼                                     ▼
   dwbi_catalog.silver_*             dwbi_catalog.quarantine.rejected_records
   (Conformed Delta Tables)          ├─ batch_id
                                     ├─ source_system ('EIA-923')
                                     ├─ source_table ('bronze_staging.raw_eia923')
                                     ├─ source_row_identifier ('Plant_3_Month_1')
                                     ├─ rejection_reason ('HEAT_RATE_OUT_OF_BOUNDS')
                                     ├─ raw_payload_json ('{"plant_id": 3, ...}')
                                     └─ rejected_at (UTC Timestamp)
```

**Key Advantages:**
1. **Zero Data Loss:** Every rejected record is preserved in full JSON fidelity.
2. **Actionable Triage:** Engineers can query `SELECT rejection_reason, COUNT(*) FROM quarantine.rejected_records GROUP BY rejection_reason` to diagnose telemetry defects.
3. **Re-Injectability:** Once upstream bugs or mapping errors are corrected, quarantined payloads can be re-parsed without re-downloading source files.

---

## 8. Concept 7: Slowly Changing Dimensions Type 2 (SCD Type 2)

### Preserving Point-in-Time History
In dimension modeling (Ralph Kimball methodology), dimension entities change attributes over time. 
* **SCD Type 1 (Overwrite):** Updates the row directly. Old values are lost.
* **SCD Type 2 (Version History):** Retains the old row, closes its validity horizon, and inserts a new row representing the new state.

### Power Plant Generator Lifecycle Tracking
Power plant generators transition through discrete lifecycle stages:
$$\text{Operating (OP)} \longrightarrow \text{Standby (SB)} \longrightarrow \text{Retired (RE)}$$

#### The Dimension Schema Contract
Every SCD Type 2 table in the Silver layer includes three mandatory temporal tracking columns:
1. `valid_from` (`TIMESTAMP`): The date and time when this attribute state became active.
2. `valid_to` (`TIMESTAMP`): The date and time when this attribute state ceased to be active. Active records use the open horizon constant: `'9999-12-31 23:59:59'`.
3. `is_current` (`BOOLEAN`): `TRUE` for the currently active record; `FALSE` for superseded historical records.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SCD TYPE 2 GENERATOR LIFECYCLE TIMELINE                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

Generator: Plant 3 (Barry), Unit 1
Operating Status Changes: OP (2021-01-01) -> SB (2023-01-01) -> RE (2024-06-01)

Record 1: [valid_from: 2021-01-01] ────────► [valid_to: 2023-01-01] (is_current: FALSE)
          Status: OP (Operating) | Capacity: 150 MW

Record 2:                           [valid_from: 2023-01-01] ──► [valid_to: 2024-06-01] (is_current: FALSE)
                                    Status: SB (Standby)   | Capacity: 150 MW

Record 3:                                                        [valid_from: 2024-06-01] ──► [valid_to: 9999-12-31] (is_current: TRUE)
                                                                 Status: RE (Retired)   | Capacity: 150 MW
```

### Point-in-Time Fact Resolution
When transactional fact records (e.g., hourly smokestack emissions from 2022) join to the generator dimension, they join on:
```sql
SELECT 
    f.date_key,
    f.hour_of_day,
    g.operating_status,
    f.co2_mass_tons
FROM gold_warehouse.fact_hourly_emissions_weather f
JOIN gold_warehouse.dim_generator g
  ON f.orispl_code = g.orispl_code
 AND f.unit_id = g.generator_id
 AND TO_TIMESTAMP(CAST(f.date_key AS STRING), 'yyyyMMdd') >= g.valid_from
 AND TO_TIMESTAMP(CAST(f.date_key AS STRING), 'yyyyMMdd') <  g.valid_to;
```
This guarantees that 2022 emissions are joined against the generator when it was **Operating (`OP`)**, rather than incorrectly reporting that an active generator was retired.

---

## 9. Concept 8: Row Count Conservation & Pipeline Observability

### The Fundamental Conservation Equation
In audited financial and engineering systems, data pipelines must satisfy the **Law of Conservation of Records**:
$$\text{Rows In} = \text{Rows Out} + \text{Quarantined} + \text{Deduplicated}$$

* If $\text{Rows In} = 1,000$
* And $\text{Quarantined} = 30$, $\text{Deduplicated} = 20$
* Then $\text{Rows Out}$ **must equal exactly 950**.
* If $\text{Rows Out} = 948$, two rows vanished unaccounted for—a critical failure in data integrity.

### Pipeline Observability (`cleaning_step_log`)
To enforce this conservation law, every Silver transformation records its exact input/output metrics to the `cleaning_step_log` table:
* `batch_id`: Global execution run identifier.
* `step_name`: Transformation task (e.g. `CONFORM_PLANTS`).
* `target_table`: Output Silver table (`silver_plants`).
* `rows_in`: Initial record count received.
* `rows_changed`: Count of records whose text or sentinels were modified.
* `rows_removed`: Count of exact duplicate natural keys dropped.
* `rows_quarantined`: Count of records routed to dead-letter storage.
* `rows_out`: Count of clean records written.
* `logged_at`: Universal UTC timestamp.

This log is evaluated during automated testing to confirm that the discrepancy between $\text{Rows In}$ and $(\text{Rows Out} + \text{Quarantined} + \text{Deduplicated})$ is **strictly 0**.

---

## 10. Concept 9: Multi-Source Entity Conformance (The Crosswalk Graph)

### The Structural Disconnect between Federal Agencies
The U.S. bulk power system is regulated by multiple federal entities that use completely different identification schemas:
* **EIA (Energy Information Administration):** Tracks commercial assets by **Plant Code (ORISPL)** and **Generator ID** (e.g. Plant `3`, Generator `1`).
* **EPA (Environmental Protection Agency):** Tracks smokestack emissions by **Facility ID** and **Boiler / Stack Unit ID** (e.g. Facility `3`, Unit `1`).

In simple facilities, Unit 1 connects to Generator 1. However, in complex power generation engineering:
1. **Multiple Boilers to One Turbine:** Two coal-fired boilers feed steam into a single massive turbine generator ($2:1$).
2. **Combined Cycle Power Trains:** Two combustion gas turbines feed their exhaust heat into a single steam turbine generator ($2:1$ or $3:1$).
3. **Shared Smokestack Flues:** Multiple units vent through a single combined chimney stack.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     EPA-EIA STRUCTURAL CROSSWALK TOPOLOGY                       │
└─────────────────────────────────────────────────────────────────────────────────┘

          EPA CAMPD (Smokestack CEMS)               EIA-860 / EIA-923 (Turbines)
          ┌─────────────────────────┐               ┌─────────────────────────┐
          │  Facility 3, Unit 1     │ ────────────► │   Plant 3, Gen 1 (CT)   │
          └─────────────────────────┘       │       └─────────────────────────┘
                                            │
          ┌─────────────────────────┐       ├─────► ┌─────────────────────────┐
          │  Facility 3, Unit 2     │ ──────┘       │   Plant 3, Gen 2 (CA)   │
          └─────────────────────────┘               └─────────────────────────┘
```

### The Silver Conformance Crosswalk
The Silver layer ingests the official EPA-EIA Crosswalk mapping file. It conforms and links:
$$\text{(facility\_id, unit\_id)} \longleftrightarrow \text{(orispl\_code, generator\_id)}$$
This crosswalk enables the Gold layer to successfully reconcile EPA smokestack emissions against EIA monthly fuel burn, unlocking Business Question 6 (Gross vs. Net Auxiliary Reconciliation).
