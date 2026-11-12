# ==============================================================================
# ANALYTICAL QUERIES EXECUTION PLAN & OLAP MAPPING
# Project: U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Catalog: dwbi_catalog (Databricks Serverless Cloud Lakehouse)
# ==============================================================================

This document specifies the execution plan, clustering optimization, aggregation mechanics, and mapping for all 10 analytical business questions and OLAP SQL queries in `05_Analytics/olap_queries.sql`.

---

## 1. Matrix: Business Questions to SQL Artifacts

| Question ID | Short Title | Core Fact Table | Dimension Joins | Analytical Technique | Live View / OLAP Query |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BQ1** | Emissions Intensity | `fact_hourly_emissions_weather` | `dim_plant`, `dim_date` | Aggregation, Ratio, Dense Rank | `vw_emissions_intensity` & Query 4 |
| **BQ2** | Weather Extremes | `fact_hourly_emissions_weather` | `dim_plant`, `dim_weather_station`, `dim_date` | Case Binning, Multi-Metric Avg | `vw_emissions_intensity` & Query 6 |
| **BQ3** | Heat Rate Benchmarking | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | Multi-dimensional `CUBE` | `vw_plant_performance` & Query 1 |
| **BQ4** | Auxiliary Outages | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | Filter `< 0`, Frequency Ratios | `vw_plant_performance` & Query 7 |
| **BQ5** | Grid Demand & Renewables| `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | Hierarchical `ROLLUP` | `vw_grid_stress` & Query 2 |
| **BQ6** | EPA vs EIA Reconciliation| `fact_hourly_emissions_weather`, `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | CTE Join, Thermodynamic Ratio | DQ `ACC_AUX_LOAD_RECON` & Query 8 |
| **BQ7** | Generator Asset SCD-2 | `dim_generator` (SCD Type 2) | `dim_plant` | Window Count, Timeline Slicing | Query 9 |
| **BQ8** | Extreme Climatic Stress | `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | Rolling 24hr Window, Dense Rank| `vw_grid_stress` & Query 10 |
| **BQ9** | Top 5% Peak Demand Slicing| `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | Percentile Window `PERCENT_RANK` | `vw_grid_stress` & Query 11 |
| **BQ10**| Generation Mix & Decarb | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | `LAG`, MoM % Growth, Moving Avg | `vw_monthly_generation_mix` & Query 3 |

---

## 2. Performance & Clustering Execution Strategy

### 2.1 Liquid Clustering Data Skipping
Rather than legacy Hive directory partitioning (`/year=2023/month=01`), tables utilize Delta Lake Liquid Clustering:
1. `fact_hourly_emissions_weather`: `CLUSTER BY (date_key, plant_key)`
   * *Benefit:* Queries filtering on date ranges (e.g. `WHERE date_key BETWEEN 20230101 AND 20230131`) or specific facilities (e.g. `WHERE plant_key = 1`) prune over 95% of Parquet data files via Delta min/max file statistics (demonstrated in OLAP Query 5 via `EXPLAIN EXTENDED`).
2. `fact_monthly_plant_operations`: `CLUSTER BY (month_start_date_key, plant_key)`
   * *Benefit:* Accelerates multi-year plant trend calculations and month-over-month lag queries.
3. `fact_regional_grid_demand`: `CLUSTER BY (date_key, ba_key)`
   * *Benefit:* Eliminates full-table scans for regional grid stress and balancing authority aggregations.

---

## 3. Detailed Query Plans

### Query 1: Multi-Dimensional OLAP CUBE (BQ3)
* **Goal:** Generate full combinatorial cross-tabulations across Year, State, and Fuel Source.
* **SQL Clause:** `GROUP BY CUBE (d.calendar_year, p.state_code, f.energy_source_code)`
* **Aggregations:** `COUNT(DISTINCT plant_key)`, `SUM(net_generation_mwh)`, `SUM(fuel_consumed_mmbtu)`, Weighted Heat Rate.

### Query 2: Hierarchical OLAP ROLLUP (BQ5)
* **Goal:** Produce hierarchical aggregations with running subtotals and grand totals along the temporal path.
* **SQL Clause:** `GROUP BY ROLLUP (d.calendar_year, d.calendar_quarter, d.calendar_month, ba.ba_code)`
* **Aggregations:** Average demand, peak demand, total renewable MWh, and renewable coverage percent.

### Query 3: Window Functions - MoM Ramp Rate & Decarbonization (BQ10)
* **Goal:** Track month-over-month net generation growth and 3-month moving averages by facility.
* **SQL Window Clauses:**
  * `LAG(current_net_mwh, 1) OVER (PARTITION BY plant_key ORDER BY calendar_year, calendar_month)`
  * `AVG(current_net_mwh) OVER (PARTITION BY plant_key ORDER BY calendar_year, calendar_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`

### Query 4: Window Functions - Emissions Intensity Benchmarking (BQ1)
* **Goal:** Rank all operational power plants from cleanest to highest emitters per calendar year.
* **SQL Window Clause:**
  * `DENSE_RANK() OVER (PARTITION BY calendar_year ORDER BY co2_intensity_tons_per_mw ASC NULLS LAST)`
  * `annual_co2_tons / NULLIF(SUM(annual_co2_tons) OVER (PARTITION BY calendar_year), 0) * 100` (Cumulative share)

### Query 5: Execution Plan Optimization Verification
* **Goal:** Verify that Databricks Serverless Photon Engine leverages Delta Liquid Clustering min/max metadata skipping.
* **SQL Clause:** `EXPLAIN EXTENDED SELECT ... FROM fact_hourly_emissions_weather WHERE date_key BETWEEN 20230101 AND 20230131 AND plant_key = 1`

### Query 6: Weather Extremes vs Emissions & Load (BQ2)
* **Goal:** Segment hourly operations into freezing (<0°C), cold (0-15°C), moderate (15-28°C), and extreme heat (>28°C) regimes.
* **SQL Clause:** `CASE WHEN ... THEN ... END AS temperature_regime`, `GROUP BY temperature_regime`.

### Query 7: Plant Auxiliary Load Outages & Negative NetGen (BQ4)
* **Goal:** Audit maintenance outages where station service load exceeds generation (`net_generation_mwh < 0`).
* **SQL Clause:** `HAVING COUNT(CASE WHEN f.net_generation_mwh < 0 THEN 1 END) > 0`.

### Query 8: Cross-Agency Generation Reconciliation (BQ6)
* **Goal:** Reconcile CAMPD gross generation with EIA-923 net generation by plant-month and compute auxiliary load ratio `(gross - net) / gross`.
* **SQL Clause:** CTEs `epa_monthly_gross` and `eia_monthly_net` joined on `(plant_key, calendar_year, calendar_month)`.

### Query 9: SCD Type 2 Generator Decommissioning Trajectory (BQ7)
* **Goal:** Track generator status changes over time (Operating -> Retired) and revision history count.
* **SQL Clause:** `COUNT(*) OVER (PARTITION BY orispl_code, generator_id) AS total_historical_revisions` from `dim_generator`.

### Query 10: Climatic Stress Grid Dispatch & Reserve Margin (BQ8)
* **Goal:** Analyze demand forecast error residuals during polar vortex freezes (`is_winter_freeze = TRUE`) and summer heat domes (`is_summer_peak = TRUE`).
* **SQL Window Clause:**
  * `AVG(g.demand_mw) OVER (PARTITION BY g.ba_key ORDER BY g.date_key, g.hour_of_day ROWS BETWEEN 23 PRECEDING AND CURRENT ROW)` (24-hour rolling average).
  * `DENSE_RANK() OVER (PARTITION BY g.ba_key, d.is_winter_freeze, d.is_summer_peak ORDER BY (demand_mw - demand_forecast_mw) DESC)`.

### Query 11: Top 5% Peak Demand Hours vs Thermal Peaker Fuel Mix (BQ9)
* **Goal:** Isolate top 5% peak demand hours within each balancing authority to measure peaker gas/coal dependency.
* **SQL Window Clause:**
  * `PERCENT_RANK() OVER (PARTITION BY g.ba_key ORDER BY g.demand_mw ASC) AS demand_percentile`
  * Outer query filters `WHERE demand_percentile >= 0.95`.
