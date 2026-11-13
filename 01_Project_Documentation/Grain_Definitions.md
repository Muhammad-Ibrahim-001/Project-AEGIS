# ==============================================================================
# KIMBALL GRAIN DEFINITIONS & MULTI-FACT JOIN PROTOCOL
# Project: U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Catalog: dwbi_catalog (Databricks Serverless Cloud Lakehouse)
# ==============================================================================

This document provides the authoritative, standalone specification for all dimensional grain definitions, primary and composite key architectures, measure additivity rules, and multi-fact query aggregation protocols across Project-AEGIS.

---

## 1. Kimball Dimensional Architecture Principles

In dimensional modeling (Ralph Kimball), establishing the precise physical grain of every fact table is the most critical architectural decision. The grain defines exactly what a single row represents in reality.

In Project-AEGIS, three multi-grain fact archetypes are deployed under `dwbi_catalog.gold_warehouse`:
1. **`fact_hourly_emissions_weather`:** Transactional Fact table (High frequency, atomic granularity).
2. **`fact_monthly_plant_operations`:** Periodic Snapshot Fact table (Monthly census, accounting reconciliation).
3. **`fact_regional_grid_demand`:** Aggregate Transmission Grid Fact table (Interconnected macro-grid telemetry).

---

## 2. Fact Table Grain Statements

### 2.1 `fact_hourly_emissions_weather` (Transactional Fact)
* **Authoritative Grain Statement:**  
  > *"One row represents the total electrical gross output (MW), smokestack emissions ($\text{CO}_2, \text{SO}_2, \text{NO}_x$), and matched surface meteorological conditions for a single Continuous Emission Monitoring System (CEMS) monitoring unit at a specific generating plant during a single one-hour clock interval on a specific calendar day."*
* **Composite Primary Key:** `(date_key, hour_of_day, plant_key, unit_id)`
* **Foreign Keys:**
  * `date_key` $\rightarrow$ `dim_date.date_key`
  * `plant_key` $\rightarrow$ `dim_plant.plant_key`
  * `station_key` $\rightarrow$ `dim_weather_station.station_key` (Resolved via spatial Haversine match within $\le 100\text{ km}$; $-1$ if out of range)
* **Delta Lake Optimization:** Liquid Clustering via `CLUSTER BY (date_key, plant_key)`
* **Measures & Additivity:**
  * Fully Additive: `gross_load_mw`, `co2_mass_tons`, `so2_mass_lbs`, `nox_mass_lbs`, `heat_input_mmbtu`.
  * Semi-Additive / Non-Additive (Averaged across units/hours): `ambient_temp_celsius`, `wind_speed_mps`, `barometric_pressure_kpa`, `weather_distance_km`.

---

### 2.2 `fact_monthly_plant_operations` (Periodic Snapshot Fact)
* **Authoritative Grain Statement:**  
  > *"One row represents the monthly aggregated net electrical generation, total fuel thermal consumption, and weighted thermal heat rate for a specific prime mover technology and fuel energy source code operating at a specific generating plant during a single calendar month."*
* **Surrogate Primary Key:** `snapshot_key` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Natural Business Key:** `(month_start_date_key, plant_key, prime_mover_code, energy_source_code)`
* **Foreign Keys:**
  * `month_start_date_key` $\rightarrow$ `dim_date.date_key` (First day of reporting calendar month, `YYYYMM01`)
  * `plant_key` $\rightarrow$ `dim_plant.plant_key`
* **Delta Lake Optimization:** Liquid Clustering via `CLUSTER BY (month_start_date_key, plant_key)`
* **Measures & Additivity:**
  * Fully Additive: `net_generation_mwh` (allows negative during maintenance), `fuel_consumed_mmbtu`.
  * Non-Additive (Weighted Average Required): `avg_heat_rate_btu_kwh` ($\text{Heat Rate} = \frac{\sum \text{Fuel MMBtu} \times 1,000}{\sum \text{NetGen MWh}}$).
  * Additive Count: `degraded_efficiency_months_count`, `negative_generation_months`.

---

### 2.3 `fact_regional_grid_demand` (Aggregate Transmission Grid Fact)
* **Authoritative Grain Statement:**  
  > *"One row represents the instantaneous hourly integrated electric load demand, day-ahead forecast load, gross generation segmented across seven fuel categories, and net transmission intertie interchange for a single Balancing Authority territory during a single one-hour clock interval on a specific calendar day."*
* **Composite Primary Key:** `(date_key, hour_of_day, ba_key)`
* **Foreign Keys:**
  * `date_key` $\rightarrow$ `dim_date.date_key`
  * `ba_key` $\rightarrow$ `dim_balancing_authority.ba_key`
* **Delta Lake Optimization:** Liquid Clustering via `CLUSTER BY (date_key, ba_key)`
* **Measures & Additivity:**
  * Fully Additive (Across Balancing Authorities within hour): `net_gen_coal_mw`, `net_gen_gas_mw`, `net_gen_nuclear_mw`, `net_gen_hydro_mw`, `net_gen_wind_mw`, `net_gen_solar_mw`, `net_gen_other_mw`, `total_renewable_generation_mw`.
  * Semi-Additive (Additive across regions, but averaged across time): `demand_mw`, `demand_forecast_mw`, `net_interchange_mw`.
  * Non-Additive (Calculated Ratios): `renewable_penetration_pct` ($\frac{\text{Wind} + \text{Solar}}{\text{Demand}} \times 100$).

---

## 3. Mandatory Multi-Fact Join Protocol (CTE Pre-Aggregation)

### 3.1 The Chasm Trap Hazard
In relational and dimensional data warehousing, **joining fact tables at different grains directly on dimension keys causes a Cartesian fan-out (the Chasm Trap)**.
- For example, joining `fact_hourly_emissions_weather` (unit-level hourly, ~744 rows per plant per month) directly to `fact_monthly_plant_operations` (plant-level monthly, 1 row per plant per month) duplicates the monthly net generation 744 times.
- Similarly, joining `fact_regional_grid_demand` (regional hourly, 1 row per BA-hour) directly to `fact_hourly_emissions_weather` (plant-hourly, multiple plants per BA) inflates grid demand measures by the number of power plants in that region.

### 3.2 Architectural Rule: CTE Pre-Aggregation
To maintain strict mathematical correctness, **multi-fact queries must NEVER join fact tables row-to-row**. Each fact table MUST be aggregated separately to the shared target grain inside independent Common Table Expressions (CTEs) before the outer query joins the summarized results.

#### Query 8 Architecture (Cross-Agency Generation Reconciliation):
* **Shared Grain:** Facility Monthly (`plant_key, calendar_year, calendar_month`).
* **CTE 1 (`epa_monthly_gross`):** Aggregates hourly unit gross load from `fact_hourly_emissions_weather` to `(plant_key, calendar_year, calendar_month)`.
* **CTE 2 (`eia_monthly_net`):** Aggregates monthly generation from `fact_monthly_plant_operations` to `(plant_key, calendar_year, calendar_month)`.
* **Outer Join:** Joins `epa_monthly_gross` to `eia_monthly_net` on `(plant_key, calendar_year, calendar_month)`.

#### Query 10 Architecture (Climatic Stress Grid Dispatch & Reserve Margin):
* **Shared Grain:** Balancing Authority Hourly (`date_key, hour_of_day, ba_code`).
* **CTE 1 (`hourly_grid_demand`):** Aggregates grid demand and fuel dispatch from `fact_regional_grid_demand` to `(date_key, hour_of_day, ba_code)`.
* **CTE 2 (`hourly_ba_emissions`):** Aggregates facility gross load and smokestack emissions from `fact_hourly_emissions_weather` joined to `dim_plant` to `(date_key, hour_of_day, ba_code)`.
* **Outer Join:** Left-joins `hourly_grid_demand` to `hourly_ba_emissions` on `(date_key, hour_of_day, ba_code)`.

#### Query 11 Architecture (Thermal Efficiency Degradation & Out-of-Bounds Heat Rate):
* **Shared Grain:** Facility Annual (`plant_key, calendar_year`).
* **CTE 1 (`plant_monthly_thermal_ops`):** Aggregates monthly heat rates and counts degraded operating months from `fact_monthly_plant_operations` to `(plant_key, calendar_year)`.
* **CTE 2 (`plant_annual_emissions_summary`):** Aggregates annual flue emissions from `fact_hourly_emissions_weather` to `(plant_key, calendar_year)`.
* **Outer Join:** Joins `plant_monthly_thermal_ops` to `plant_annual_emissions_summary` on `(plant_key, calendar_year)`.

---

## 4. Slowly Changing Dimension (SCD Type 2) Grain & Mechanics

`dim_generator` maintains full historical lifecycle tracking for all generating units across the 2021–2024 compliance window:
* **Primary Key:** `generator_key` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Natural Business Key:** `(orispl_code, generator_id)`
* **Temporal Version Attributes:**
  * `valid_from`: Timestamp marking when the version became active.
  * `valid_to`: Timestamp marking when the version was superseded (`9999-12-31 23:59:59` for the current active version).
  * `is_current`: Boolean flag (`TRUE` for active version, `FALSE` for expired historical versions).
* **Monitored Status Transitions:**
  * `OP` (Operating / Active Commercial Generation) $\rightarrow$ `SB` (Standby / Cold Reserve) $\rightarrow$ `RE` (Retired / Decommissioned).
* **Fact Table Lookup Integrity:**
  * Fact table ETL looks up `generator_lookup[(orispl_code, generator_id)]`, ensuring transactional facts link to the active version (`is_current = TRUE`).
