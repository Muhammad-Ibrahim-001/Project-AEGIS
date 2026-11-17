# Phase 2: End-to-End ETL Pipeline Architecture & Engineering Runbook

**Catalog:** `dwbi_catalog` (Databricks Unity Catalog)  
**Schemas:** `bronze_staging`, `silver_conformed`, `gold_warehouse`, `gold_marts`, `quarantine`  
**Execution Runtime:** Apache Spark 3.5+ / Serverless Photon Engine / Local Python Fallback  
**Storage Format:** Delta Lake (`USING DELTA`) with Liquid Clustering (`CLUSTER BY`)

---

## 1. Five-Stage Medallion Pipeline Flow

```
                      [Federal & Synoptic Sources]
      EIA-860 (XLSX) | EIA-923 (XLSX) | EPA CAMPD (CSV) | NOAA ISD (CSV) | EIA-930 (CSV)
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: BRONZE STAGING (bronze_staging)                                       │
│ • Raw Volume Landing (/Volumes/dwbi_catalog/bronze_staging/raw_landing/)        │
│ • Dynamic Excel Header Discovery (Row 2 vs Row 6 scanner)                      │
│ • Append-Only Delta Landing Tables (raw_eia*, raw_epa*, raw_noaa*)             │
│ • Immutable Execution Audit Logging (etl_run_log)                               │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: SILVER CONFORMANCE & CLEANSING (silver_conformed)                      │
│ • Text Normalization: TRIM(), UPPER(), TitleCase()                             │
│ • Federal Sentinel Coercion: '.', 'NM', -9999 -> NULL                           │
│ • Thermodynamic Heat Rate Clamping: 5,000 - 22,000 Btu/kWh                     │
│ • Legitimacy Preservation: Negative Net Generation (Maintenance Outages)        │
│ • Spatial Proximity Crosswalk: Haversine near-neighbor station matching         │
│ • SCD Type 2 Lifecycle Tracking: (valid_from, valid_to, is_current)             │
│ • Dead-Letter Quarantine: corrupt records -> quarantine.rejected_records       │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: GOLD KIMBALL STAR SCHEMA (gold_warehouse)                             │
│ • Conformed Dimensions (5):                                                    │
│     - dim_date (1,461 calendar days, 2021-2024)                                │
│     - dim_plant (Surrogate plant_key, orispl_code, coordinates, EPA region)   │
│     - dim_generator (Surrogate generator_key, SCD-2 tracked lifecycle)         │
│     - dim_balancing_authority (Surrogate ba_key, ba_code, region)              │
│     - dim_weather_station (Surrogate station_key, USAF-WBAN, elevation)        │
│ • Multi-Grain Fact Tables (3):                                                  │
│     - fact_hourly_emissions_weather (Transactional, 12,500 rows, CLUSTER BY)   │
│     - fact_monthly_plant_operations (Periodic Snapshot, 1,680 rows, CLUSTER BY)│
│     - fact_regional_grid_demand (Aggregate Grid, 2,002 rows, CLUSTER BY)       │
│ • Referential Integrity: COALESCE(dim_key, -1) guarantees 0 orphan FKs         │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: GOLD REPORTING MARTS (gold_marts)                                     │
│ • Materialized DirectQuery Views feeding Power BI:                              │
│     - vw_emissions_intensity (Air quality & CO2/SO2/NOx rates per MWh)          │
│     - vw_plant_performance (Monthly heat rates & fuel consumption)             │
│     - vw_grid_stress (Hourly BA demand, fuel dispatch mix, interchange)         │
│     - vw_monthly_generation_mix (Regional generation by energy source)          │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: DATA QUALITY AUDIT ENGINE (05_data_quality_validation.py)              │
│ • 66 Automated Tests across 6 Dimensions:                                      │
│     1. Completeness: 40 tests (0.00% null on mandatory keys)                    │
│     2. Accuracy & Reconciliation: 4 tests (Auxiliary ratio = 9.75%)             │
│     3. Referential Integrity: 8 tests (0 orphan FKs, default -1 rate < 0.5%)   │
│     4. Uniqueness: 8 tests (0 duplicate PKs or UKs)                             │
│     5. Row Count Conservation: 2 tests (Rows In = Rows Out + Quarantined)       │
│     6. Date Coverage: 4 tests (1,461 calendar days without gaps)               │
│ • Automated PDF Report Generation (ReportLab 5.x & Edge Headless)              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Execution Instructions

### Running in Local Terminal / Offline CI Mode
```bash
# Execute end-to-end lakehouse pipeline with full university grading rubric scale:
python 03_ETL/master_pipeline_runner.py --synthetic

# Execute automated quality check suite:
python 03_ETL/05_data_quality_validation.py

# Recompile all Phase 2 PDF and SQL deliverables:
python archived/Phase_2_Submissions/scripts/compile_all_phase2_deliverables.py
```

### Running in Databricks Cloud Lakehouse
1. Upload `/03_ETL/` notebooks to your Databricks Workspace (`/Workspace/Shared/DWBI_Project/03_ETL/`).
2. Attach to a **Databricks Serverless Notebook Compute** cluster (Photon Engine, Databricks Runtime 15.4+ / Serverless Environment Version 5).
3. Execute `master_pipeline_runner.py` directly from the Databricks notebook cell. All tables, volumes, and views will be created inside `dwbi_catalog`.
