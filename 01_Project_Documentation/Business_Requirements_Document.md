# ==============================================================================
# BUSINESS REQUIREMENTS DOCUMENT (BRD)
# Project: U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse (Project-AEGIS)
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Catalog: dwbi_catalog (Databricks Serverless Cloud Lakehouse)
# ==============================================================================

## 1. Executive Summary & Document Overview

Project-AEGIS establishes an enterprise-grade cloud data warehouse and analytical platform analyzing bulk electric power generation, Continuous Emission Monitoring System (CEMS) smokestack air pollution, synoptic surface weather observations, and regional transmission grid operations across the contiguous United States from 2021 through 2024.

This Business Requirements Document (BRD) provides the authoritative specification for all analytical questions, Kimball dimensional star schemas, grain definitions, dimension hierarchies, and reporting views required by the DL3004 course syllabus and academic grading rubrics.

### 1.1 Stakeholders & Analytical Personas
1. **Executive Leadership & Regulators (Power BI Page 1):** National overview of carbon emissions intensity, thermal fuel mix trends, and interstate power transmission.
2. **Plant Performance & Plant Engineers (Power BI Page 2):** Plant-level thermodynamic heat rate benchmarks, fuel consumption, auxiliary load consumption during outages, and CEMS sensor tracking.
3. **Transmission Grid Operators & Energy Traders (Power BI Page 3):** Hourly grid electrical demand, day-ahead forecast error residuals, renewable penetration (wind and solar), and climatic extreme stress alerts.

---

## 2. Formal Analytical Business Questions (10 Core Questions)

Below are the 10 formal analytical business questions driving the dimensional lakehouse design, each mapped to its underlying Kimball fact tables, conformed dimensions, quantitative measures, grain definition, and matching SQL view or OLAP query.

### BQ1: Facility Emissions Intensity & Regional Distribution
* **Question Statement:** Which power generating facilities and states emit the highest rates of $\text{CO}_2$, $\text{SO}_2$, and $\text{NO}_x$ per unit of gross generation (tons/MW or lbs/MW), and how does emissions intensity fluctuate month-over-month?
* **Business Intent:** Environmental compliance auditing, regional carbon footprint benchmarking, and identifying high-polluting peaker units under federal Clean Air Act standards.
* **Fact Table:** `gold_warehouse.fact_hourly_emissions_weather`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `gross_load_mw` (Additive), `co2_mass_tons` (Additive), `so2_mass_lbs` (Additive), `nox_mass_lbs` (Additive), `co2_intensity_tons_per_mw` (Calculated Ratio / Non-Additive).
* **Grain:** Hourly per generating plant and CEMS monitoring unit (`date_key`, `hour_of_day`, `plant_key`, `unit_id`).
* **Matching Reporting View / Query:** `gold_marts.vw_emissions_intensity` & OLAP Query 4 (Window Functions: Facility Emissions Intensity Benchmarking & Dense Ranking).

### BQ2: Synoptic Weather Stress vs. Emissions & Generation
* **Question Statement:** How do extreme ambient temperatures (polar freeze below 0°C and heat waves above 28°C) and surface wind speeds affect hourly generation load and smokestack emissions intensity?
* **Business Intent:** Thermodynamic derating assessment, cooling water intake stress evaluation during droughts, and gas turbine compressor performance benchmarking across temperature regimes.
* **Fact Table:** `gold_warehouse.fact_hourly_emissions_weather`
* **Dimension Tables:** `dim_plant`, `dim_weather_station`, `dim_date`
* **Measures:** `gross_load_mw` (Additive), `co2_mass_tons` (Additive), `ambient_temp_celsius` (Non-Additive / Semi-Additive average), `wind_speed_mps` (Non-Additive / Semi-Additive average), `weather_distance_km` (Semi-Additive).
* **Grain:** Hourly per generating plant and nearest surface weather station (`date_key`, `hour_of_day`, `plant_key`, `unit_id`).
* **Matching Reporting View / Query:** `gold_marts.vw_emissions_intensity` & OLAP Query 6 (Weather Extremes vs. Emissions & Load Impact).

### BQ3: Prime Mover & Fuel Thermal Efficiency / Heat Rate Benchmarking
* **Question Statement:** Which prime mover technologies (e.g., Combined Cycle vs. Simple Cycle Combustion Turbines vs. Steam Turbines) and fuel sources run least efficiently (highest heat rate in Btu/kWh), and how do delivered fuel costs vary?
* **Business Intent:** Thermal generation efficiency optimization, fuel procurement cost auditing, and merit-order dispatch economic analysis.
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `net_generation_mwh` (Additive), `fuel_consumed_mmbtu` (Additive), `avg_heat_rate_btu_kwh` (Non-Additive / Weighted Average), `delivered_fuel_cost_per_mmbtu` (Non-Additive average).
* **Grain:** Monthly per generating plant, prime mover code, and energy source code (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 1 (Multi-Dimensional OLAP CUBE by Geography & Fuel Mix).

### BQ4: Station Auxiliary Outages & Negative Net Generation
* **Question Statement:** Which generating facilities report net negative electrical generation due to station auxiliary load exceeding gross output, and what is the frequency and duration of these outage events?
* **Business Intent:** Detection of forced and scheduled maintenance outages, parasitic station power consumption during black-start or startup conditions, and reliability risk profiling.
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `net_generation_mwh` (Additive, allows negative values), `fuel_consumed_mmbtu` (Additive), `outage_frequency_pct` (Calculated Non-Additive).
* **Grain:** Monthly per generating plant, prime mover code, and energy source code (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 7 (Plant Auxiliary Load Outages & Negative Net Generation Audit).

### BQ5: Balancing Authority Peak Demand, Renewable Penetration & Interchanges
* **Question Statement:** Which balancing authorities experience the most severe hourly peak electrical demands, what percentage of hourly load is supplied by wind and solar, and how do regional net interchanges balance grid deficits?
* **Business Intent:** Grid reliability management, transmission intertie capacity evaluation, and tracking renewable integration and curtailment patterns.
* **Fact Table:** `gold_warehouse.fact_regional_grid_demand`
* **Dimension Tables:** `dim_balancing_authority`, `dim_date`
* **Measures:** `demand_mw` (Additive across BAs / Non-Additive across time; peak is Semi-Additive MAX), `demand_forecast_mw` (Semi-Additive), `net_gen_wind_mw` (Additive), `net_gen_solar_mw` (Additive), `renewable_penetration_pct` (Calculated Ratio), `net_interchange_mw` (Additive).
* **Grain:** Hourly per balancing authority (`date_key`, `hour_of_day`, `ba_key`).
* **Matching Reporting View / Query:** `gold_marts.vw_grid_stress` & OLAP Query 2 (Hierarchical OLAP ROLLUP: Temporal & Spatial Grid Demand Slicing).

### BQ6: Physical Reconciliation of EPA Gross vs. EIA Net Generation / Auxiliary Ratio
* **Question Statement:** Does EPA Continuous Emission Monitoring System (CAMPD) hourly gross generation reconcile with EIA-923 monthly reported net generation, and does the auxiliary load ratio conform to physical thermodynamic bounds (3% to 14%)?
* **Business Intent:** Cross-agency data reconciliation and physical thermodynamic validation, auditing reporting fidelity and meter drift.
* **Fact Tables:** `gold_warehouse.fact_hourly_emissions_weather` & `gold_warehouse.fact_monthly_plant_operations`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `gross_load_mw` (Additive), `net_generation_mwh` (Additive), `auxiliary_load_ratio_pct` (Calculated Non-Additive).
* **Grain:** Monthly aggregate per power plant (`plant_key`, `calendar_year`, `calendar_month`).
* **Matching Reporting View / Query:** Data Quality Validation Check `ACC_AUX_LOAD_RECON` & OLAP Query 8 (Cross-Agency Generation Reconciliation & Auxiliary Ratio Audit).

### BQ7: Generator Asset Lifecycle & SCD Type 2 Decommissioning Tracking
* **Question Statement:** How do generator operating statuses (Operating, Standby, Retired) and nameplate capacities change over time, and what is the cumulative generation capacity retired across fuel types?
* **Business Intent:** Asset lifecycle tracking, thermal fleet retirement trajectory under decarbonization policies, and resource adequacy forecasting.
* **Dimension Table (SCD-2):** `gold_warehouse.dim_generator`
* **Associated Dimensions:** `dim_plant`
* **Measures:** `nameplate_capacity_mw` (Semi-Additive across time, Additive across generators), `revision_count` (Additive), `cumulative_retired_mw` (Additive).
* **Grain:** Historical interval per generator asset version (`generator_key`, natural `(orispl_code, generator_id)`, `valid_from`, `valid_to`).
* **Matching Reporting View / Query:** OLAP Query 9 (SCD Type 2 Generator Decommissioning & Retirement Trajectory).

### BQ8: Extreme Climatic Stress vs. Regional Grid Dispatch & Reserve Deficits
* **Question Statement:** How do extreme climatic events (polar vortex winter freezes and summer heat domes) cause day-ahead demand forecast residuals, thermal peaking ramp-ups, and regional grid stress alerts?
* **Business Intent:** Disaster preparedness, emergency grid dispatch resilience (preventing Winter Storm Uri type grid collapse), and fuel security monitoring.
* **Fact Table:** `gold_warehouse.fact_regional_grid_demand`
* **Dimension Tables:** `dim_balancing_authority`, `dim_date`
* **Measures:** `demand_mw` (Semi-Additive), `demand_forecast_mw` (Semi-Additive), `forecast_residual_error_mw` (Additive/Calculated), `thermal_dispatch_mw` (Additive), `grid_stress_alert_level` (Categorical).
* **Grain:** Hourly per balancing authority during flagged climatic freeze and peak dates (`date_key`, `hour_of_day`, `ba_key`).
* **Matching Reporting View / Query:** `gold_marts.vw_grid_stress` & OLAP Query 10 (Climatic Stress Grid Dispatch & Reserve Margin Window Analysis).

### BQ9: Thermal Efficiency Degradation & Out-of-Bounds Heat Rate Operating Frequency by Plant
* **Question Statement:** How many operating months per calendar year do thermal power plants run at degraded thermodynamic efficiencies exceeding standard technology heat-rate thresholds (CCGT > 10,000 Btu/kWh, Coal Steam > 14,000 Btu/kWh, Peakers > 16,000 Btu/kWh), and what is the associated fuel consumption penalty?
* **Business Intent:** Identifies generating units suffering boiler fouling, cooling tower derating, or severe compressor degradation, prioritizing thermal units for maintenance overhaul, heat rate improvement, or retirement.
* **Fact Tables:** `gold_warehouse.fact_monthly_plant_operations`, `gold_warehouse.fact_hourly_emissions_weather`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `net_generation_mwh` (Additive), `fuel_consumed_mmbtu` (Additive), `avg_heat_rate_btu_kwh` (Non-Additive Weighted Avg), `degraded_efficiency_months_count` (Additive), `degraded_operating_pct` (Calculated Ratio).
* **Grain:** Monthly per generating plant, prime mover, and energy source (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 11 (Thermal Efficiency Degradation & Heat-Rate Exceedance Frequency).

### BQ10: Multi-Year Generation Trends & Decarbonization by Prime Mover
* **Question Statement:** How has the generation mix, total net generation volume, and weighted heat rate transitioned across prime mover technologies (Combined Cycle, Steam Turbine, Gas Turbine, Wind, Solar) over the 2021-2024 compliance window?
* **Business Intent:** Fleet-wide decarbonization rate measurement, coal-to-gas transition velocity tracking, and generation market share analysis.
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** `total_net_generation_mwh` (Additive), `total_fuel_mmbtu` (Additive), `weighted_heat_rate_btu_kwh` (Calculated Ratio / Non-Additive), `mom_growth_pct` (Calculated Ratio).
* **Grain:** Monthly per state, prime mover code, and energy source code (`calendar_year`, `calendar_month`, `state_code`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_monthly_generation_mix` & OLAP Query 3 (Month-Over-Month Ramp Rate, Growth % & Prior Year Lag).

---

## 3. Conceptual Schema

The conceptual data model captures the core real-world energy entities and their fundamental business relationships:

```
+--------------------+               +-------------------------+
|   WEATHER STATION  |               |   BALANCING AUTHORITY   |
| (NOAA Surface Obs) |               |  (Electric Grid Entity) |
+---------+----------+               +------------+------------+
          | (Spatial Haversine)                   | (Interconnection)
          v                                       v
+--------------------+  (Assets)     +-------------------------+
|    POWER PLANT     +-------------->+  REGIONAL GRID DEMAND   |
|  (EIA-860 Master)  |               |    (EIA-930 Telemetry)  |
+---------+----------+               +-------------------------+
          |
          | (Generators SCD-2)
          v
+--------------------+
|  GENERATING UNIT   |
| (Nameplate MW/Tech)|
+---------+----------+
          |
          +-----------------------+-----------------------+
          | (Flue Gas Monitoring) | (Thermal Fuel Burn)   |
          v                       v                       v
+--------------------+  +--------------------+  +--------------------+
|  HOURLY EMISSIONS  |  | MONTHLY OPERATIONS |  |    CALENDAR DATE   |
|   (CAMPD CEMS)     |  |   (EIA-923 Gen)    |  |  (2021-2024 Days)  |
+--------------------+  +--------------------+  +--------------------+
```

---

## 4. Logical Schema (Kimball Star Schema)

The logical schema implements a Kimball dimensional warehouse containing 5 conformed dimension tables and 3 multi-grain fact tables.

### 4.1 Conformed Dimension Specifications
1. **`dim_date` (Role-Playing Calendar Dimension):**
   * Primary Key: `date_key` (INT, `YYYYMMDD`)
   * Natural Date: `calendar_date` (DATE, `YYYY-MM-DD`)
   * Attributes: `calendar_year`, `calendar_quarter`, `calendar_month`, `month_name`, `day_of_month`, `day_of_week`, `day_name`, `is_weekend`, `season_name`, `is_summer_peak`, `is_winter_freeze`.
2. **`dim_plant` (Power Generating Facilities):**
   * Surrogate Key: `plant_key` (BIGINT IDENTITY)
   * Business Key: `orispl_code` (INT)
   * Attributes: `plant_name`, `utility_id`, `utility_name`, `state_code`, `county`, `latitude`, `longitude`, `nerc_region`, `ba_code`.
3. **`dim_generator` (Generating Unit Assets - SCD Type 2):**
   * Surrogate Key: `generator_key` (BIGINT IDENTITY)
   * Business Key: `(orispl_code, generator_id)`
   * Foreign Key: `plant_key` -> `dim_plant.plant_key`
   * Attributes: `unit_id`, `prime_mover_code`, `energy_source_code`, `nameplate_capacity_mw`, `summer_capacity_mw`, `winter_capacity_mw`, `operating_status`.
   * SCD-2 Tracking Columns: `valid_from` (DATE), `valid_to` (DATE), `is_current` (BOOLEAN).
4. **`dim_balancing_authority` (Grid Control Entities):**
   * Surrogate Key: `ba_key` (BIGINT IDENTITY)
   * Business Key: `ba_code` (STRING)
   * Attributes: `ba_name`, `region` (NERC), `interconnection` (Eastern, Western, Texas-ERCOT).
5. **`dim_weather_station` (Surface Weather Observation Stations):**
   * Surrogate Key: `station_key` (BIGINT IDENTITY)
   * Business Key: `station_id` (STRING, USAF-WBAN / ICAO)
   * Attributes: `station_name`, `state`, `country`, `latitude`, `longitude`, `elevation_m`, `climate_zone`.

### 4.2 Multi-Grain Fact Tables & Measure Classifications

| Fact Table | Archetype | Fact Measures | Measure Additivity | Grain Description |
| :--- | :--- | :--- | :--- | :--- |
| `fact_hourly_emissions_weather` | Transactional Fact | `gross_load_mw`<br>`steam_load_1000_lbs`<br>`so2_mass_lbs`<br>`co2_mass_tons`<br>`nox_mass_lbs`<br>`heat_input_mmbtu`<br>`ambient_temp_celsius`<br>`dew_point_celsius`<br>`sea_level_pressure_hpa`<br>`wind_speed_mps`<br>`weather_distance_km` | Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Non-Additive (Avg)<br>Non-Additive (Avg)<br>Non-Additive (Avg)<br>Non-Additive (Avg)<br>Semi-Additive | Hourly per plant and CEMS smokestack monitoring unit (`date_key`, `hour_of_day`, `plant_key`, `unit_id`) |
| `fact_monthly_plant_operations` | Periodic Snapshot Fact | `net_generation_mwh`<br>`fuel_consumed_mmbtu`<br>`avg_heat_rate_btu_kwh`<br>`fuel_consumed_for_electricity_mmbtu`<br>`delivered_fuel_cost_per_mmbtu` | Additive (allows negative)<br>Additive<br>Non-Additive (Weighted Avg)<br>Additive<br>Non-Additive (Avg) | Monthly per plant, prime mover, and energy source (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`) |
| `fact_regional_grid_demand` | Aggregate Grid Fact | `demand_mw`<br>`demand_forecast_mw`<br>`net_gen_coal_mw`<br>`net_gen_gas_mw`<br>`net_gen_nuclear_mw`<br>`net_gen_hydro_mw`<br>`net_gen_wind_mw`<br>`net_gen_solar_mw`<br>`net_gen_other_mw`<br>`net_interchange_mw` | Semi-Additive (MAX/AVG across time)<br>Semi-Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Additive<br>Additive across BAs | Hourly per balancing authority (`date_key`, `hour_of_day`, `ba_key`) |

---

## 5. Physical Schema (Delta Lake & Liquid Clustering)

All physical warehouse tables are implemented in Apache Spark SQL and Delta Lake within Unity Catalog (`dwbi_catalog`):

* **Storage Engine:** Delta Lake format with ACID transactions, schema enforcement, and time travel.
* **Liquid Clustering:** Modern multi-dimensional clustering replaces legacy Hive-style directory partitioning:
  * `fact_hourly_emissions_weather`: `CLUSTER BY (date_key, plant_key)`
  * `fact_monthly_plant_operations`: `CLUSTER BY (month_start_date_key, plant_key)`
  * `fact_regional_grid_demand`: `CLUSTER BY (date_key, ba_key)`
* **Identity Columns:** Surrogate primary keys utilize `BIGINT GENERATED ALWAYS AS IDENTITY` (or `GENERATED BY DEFAULT AS IDENTITY` to permit the default `-1` unknown member row).
* **Physical DDL Alignment:** The active DDL is maintained in `04_SQL/warehouse.sql`.

---

## 6. Fact Table Grain Statements

1. **`fact_hourly_emissions_weather` Grain Statement:**  
   *"One row represents the total electrical gross load, flue-gas emissions ($\text{CO}_2, \text{SO}_2, \text{NO}_x$), and matched surface meteorological conditions for a single Continuous Emission Monitoring System (CEMS) monitoring unit at a specific power plant during a single one-hour clock interval on a specific calendar day."*

2. **`fact_monthly_plant_operations` Grain Statement:**  
   *"One row represents the monthly aggregated net electrical generation, total fuel thermal consumption, and weighted thermal heat rate for a specific prime mover technology and fuel energy source code operating at a specific power plant during a single calendar month."*

3. **`fact_regional_grid_demand` Grain Statement:**  
   *"One row represents the instantaneous hourly integrated electric load demand, day-ahead forecast load, gross generation segmented across seven fuel categories, and net transmission intertie interchange for a single Balancing Authority territory during a single one-hour clock interval on a specific calendar day."*

---

## 7. Dimension Hierarchies

Hierarchies enable drill-down, roll-up, and slicing capabilities across OLAP analysis and Power BI interactive reports.

### 7.1 Date Dimension Hierarchy (`dim_date`)
$$\text{Calendar Date (Day)} \longrightarrow \text{Calendar Month} \longrightarrow \text{Calendar Quarter} \longrightarrow \text{Calendar Year}$$
* *Alternative Temporal Hierarchy:* $\text{Day of Week} \longrightarrow \text{Weekend vs. Weekday Indicator}$
* *Climatic Periodicity:* $\text{Calendar Date} \longrightarrow \text{Season (Winter, Spring, Summer, Fall)} \longrightarrow \text{Climatic Stress Peak Flag (Summer Peak / Winter Freeze)}$

### 7.2 Geographic & Plant Hierarchy (`dim_plant`)
$$\text{Generating Unit / CEMS Flue Monitor} \longrightarrow \text{Power Plant (ORISPL)} \longrightarrow \text{County} \longrightarrow \text{State Code} \longrightarrow \text{NERC Grid Region} \longrightarrow \text{National Interconnection}$$

### 7.3 Generator Asset & Technology Hierarchy (`dim_generator`)
$$\text{Generator ID} \longrightarrow \text{ORISPL Plant} \longrightarrow \text{Energy Source Code (Fuel)} \longrightarrow \text{Prime Mover Code (Technology)} \longrightarrow \text{Operating Status (Active / Standby / Retired)}$$
* *Temporal SCD-2 Hierarchy:* $\text{Current Asset State} \longrightarrow \text{Historical Asset State (Tracked via valid\_from, valid\_to)}$

### 7.4 Balancing Authority Grid Hierarchy (`dim_balancing_authority`)
$$\text{Balancing Authority Code (BA)} \longrightarrow \text{Balancing Authority Name} \longrightarrow \text{NERC Sub-Region} \longrightarrow \text{Interconnection (Eastern / Western / ERCOT Texas)}$$

### 7.5 Surface Weather Station Hierarchy (`dim_weather_station`)
$$\text{Station ID (USAF-WBAN)} \longrightarrow \text{Station Name} \longrightarrow \text{State Code} \longrightarrow \text{Climate Zone} \longrightarrow \text{Latitude / Longitude Spatial Grid}$$

---

## 8. Reporting & Analytical Layer Architecture

The lakehouse delivers reporting through two decoupled analytical delivery channels:

1. **Power BI DirectQuery Materialized Views (`dwbi_catalog.gold_marts`):**
   * `vw_emissions_intensity`: Daily/monthly rollup of flue emissions, gross load, and ambient temperature (Feeds Page 1: Executive Overview).
   * `vw_plant_performance`: Monthly fuel consumption, net generation, and heat rate efficiency flags (Feeds Page 2: Engineering Deep Dive).
   * `vw_grid_stress`: Hourly balancing authority demand, day-ahead forecast error, and renewable coverage alerts (Feeds Page 3: Grid Decision Support).
   * `vw_monthly_generation_mix`: Monthly prime mover and fuel generation trends and decarbonization tracking (Feeds Page 2 & BQ10).
2. **OLAP Analytical SQL Suite (`05_Analytics/olap_queries.sql`):**
   * Multi-dimensional OLAP `CUBE` cross-tabulations (Query 1).
   * Hierarchical OLAP `ROLLUP` aggregations (Query 2).
   * Window functions (`LAG`, `LEAD`, moving averages, `DENSE_RANK`) for growth and intensity tracking (Queries 3, 4, 10, 11).
   * Execution plan optimization (`EXPLAIN EXTENDED`) verifying Liquid Clustering data skipping (Query 5).
   * Specialized auditing queries for weather extremes, auxiliary outages, cross-agency reconciliation, and SCD-2 asset tracking (Queries 6, 7, 8, 9).

