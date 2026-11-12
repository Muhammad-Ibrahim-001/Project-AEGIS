# ==============================================================================
# PROJECT PROPOSAL & BUSINESS PROBLEM STATEMENT
# Project: U.S. Bulk Power Generation, Smokestack Air Emissions & Weather Lakehouse
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Catalog: dwbi_catalog (Databricks Serverless Cloud Lakehouse)
# ==============================================================================

## 1. Executive Summary & Problem Statement

The U.S. electric power sector generates over 4 trillion kilowatt-hours of electrical energy annually, representing one of the largest single industrial contributors to atmospheric greenhouse gases ($\text{CO}_2$) and criteria air pollutants ($\text{SO}_2, \text{NO}_x$). Simultaneously, regional power transmission grids operate under increasing stress driven by clean renewable integration (wind and solar intermittency) and extreme synoptic climatic events (deep winter polar freezes and summer heat domes).

However, critical bulk power data is fragmented across isolated federal data silos:
1. **Federal Energy Information Administration (EIA):**
   * **EIA-860:** Annual physical asset inventories, nameplate capacities, and boiler-generator environmental associations.
   * **EIA-923:** Monthly net electrical generation, fuel heat input, and delivered fuel costs.
   * **EIA-930:** Hourly regional grid balancing authority demand, day-ahead forecasts, generation by fuel mix, and interstate net interchanges.
2. **Environmental Protection Agency (EPA):**
   * **EPA Clean Air Markets Program Data (CAMPD):** Hourly Continuous Emission Monitoring System (CEMS) gross load, heat input, and smokestack mass emissions ($\text{CO}_2, \text{SO}_2, \text{NO}_x$).
   * **EPA-EIA Crosswalk:** Official federal crosswalk mapping complex many-to-many physical relationships between boilers and generators.
3. **National Oceanic and Atmospheric Administration (NOAA):**
   * **Integrated Surface Database (ISD):** Hourly surface meteorological observations (dry-bulb ambient temperature, dew point, barometric pressure, wind speed) from thousands of weather stations.

### Core Business Problem
Energy regulators, transmission grid operators, and power plant reliability engineers lack a unified analytical platform to perform cross-agency data reconciliation, evaluate thermal efficiency derating during extreme weather events, benchmark facility emissions intensities, track generator retirements over time, and alert on day-ahead grid stress conditions.

Project-AEGIS resolves this fragmentation by engineering an enterprise Databricks Serverless Cloud Lakehouse with Delta Lake and Unity Catalog (`dwbi_catalog`), providing automated Medallion data engineering (Bronze -> Silver -> Gold), Kimball dimensional star schemas, extensive data quality auditing, and interactive Microsoft Power BI reporting.

---

## 2. Formal Analytical Business Questions (10 Core Questions)

The lakehouse platform is purpose-built to answer the following 10 formal analytical business questions:

| ID | Business Question Statement | Grain | Fact Table | Dimension Tables | Measures | Matching SQL View / Query |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| **BQ1** | Which power generating facilities and states emit the highest rates of $\text{CO}_2, \text{SO}_2, \text{NO}_x$ per unit of gross generation, and how does intensity vary across calendar months? | Hourly per plant and CEMS monitoring unit | `fact_hourly_emissions_weather` | `dim_plant`, `dim_date` | `gross_load_mw`, `co2_mass_tons`, `so2_mass_lbs`, `nox_mass_lbs`, `co2_intensity_tons_per_mw` | `vw_emissions_intensity` & OLAP Query 4 |
| **BQ2** | How do ambient temperature extremes (below 0°C vs above 28°C) and surface wind speeds impact hourly gross load and emissions intensity across regional climates? | Hourly per plant and nearest surface weather station | `fact_hourly_emissions_weather` | `dim_plant`, `dim_weather_station`, `dim_date` | `gross_load_mw`, `co2_mass_tons`, `ambient_temp_celsius`, `wind_speed_mps`, `weather_distance_km` | `vw_emissions_intensity` & OLAP Query 6 |
| **BQ3** | Which combinations of prime mover technology and energy source run least efficiently (highest heat rate in Btu/kWh), and how do delivered fuel costs fluctuate over time? | Monthly per plant, prime mover, and energy source | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | `net_generation_mwh`, `fuel_consumed_mmbtu`, `avg_heat_rate_btu_kwh`, `delivered_fuel_cost_per_mmbtu` | `vw_plant_performance` & OLAP Query 1 |
| **BQ4** | Which generating facilities experience net negative electrical generation due to station auxiliary load exceeding gross output during maintenance outages, and what is the outage frequency? | Monthly per plant, prime mover, and energy source | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | `net_generation_mwh` (negative values), `fuel_consumed_mmbtu`, `outage_frequency_pct` | `vw_plant_performance` & OLAP Query 7 |
| **BQ5** | Which balancing authorities experience the most severe hourly peak electrical demands, what share of load is met by renewable wind and solar, and how do net interchanges balance the grid? | Hourly per balancing authority | `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | `demand_mw`, `demand_forecast_mw`, `net_gen_wind_mw`, `net_gen_solar_mw`, `renewable_penetration_pct`, `net_interchange_mw` | `vw_grid_stress` & OLAP Query 2 |
| **BQ6** | Does EPA CAMPD hourly gross generation reconcile with EIA-923 monthly net generation, and is the auxiliary load ratio within physical engineering bounds (3% to 14%)? | Monthly aggregate per power plant | `fact_hourly_emissions_weather`, `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | `gross_load_mw`, `net_generation_mwh`, `auxiliary_load_ratio_pct` | DQ Check `ACC_AUX_LOAD_RECON` & OLAP Query 8 |
| **BQ7** | How do generator operating statuses (Operating, Standby, Retired) and nameplate capacities change over time, and what is the cumulative capacity lost to retirements? | Historical revision per generator | `dim_generator` (SCD Type 2) | `dim_plant` | `nameplate_capacity_mw`, `revision_count`, `cumulative_retired_mw` | OLAP Query 9 |
| **BQ8** | How do extreme climatic stress events (polar vortex freezes and summer heat waves) trigger day-ahead forecast residuals, thermal peaking ramp-ups, and regional grid stress alerts? | Hourly per balancing authority during stress dates | `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | `demand_mw`, `demand_forecast_mw`, `forecast_residual_error_mw`, `thermal_dispatch_mw`, `grid_stress_alert_level` | `vw_grid_stress` & OLAP Query 10 |
| **BQ9** | During the top 5% peak demand hours within each balancing authority, what proportion of generation is supplied by rapid-start thermal peakers versus baseload and renewables? | Hourly per balancing authority | `fact_regional_grid_demand` | `dim_balancing_authority`, `dim_date` | `demand_mw`, `net_gen_coal_mw`, `net_gen_gas_mw`, `peaker_thermal_share_pct` | `vw_grid_stress` & OLAP Query 11 |
| **BQ10**| How has the monthly generation mix, total net generation volume, and weighted heat rate transitioned across prime mover technologies over the 2021-2024 compliance window? | Monthly per state, prime mover, and energy source | `fact_monthly_plant_operations` | `dim_plant`, `dim_date` | `total_net_generation_mwh`, `total_fuel_mmbtu`, `weighted_heat_rate_btu_kwh`, `mom_growth_pct` | `vw_monthly_generation_mix` & OLAP Query 3 |

---

## 3. Technology Architecture & Implementation Stack

* **Platform:** Databricks Serverless Cloud Lakehouse (AWS / Azure / GCP).
* **Storage & Governance:** Delta Lake with Liquid Clustering (`CLUSTER BY`) under Unity Catalog 3-tier namespace (`dwbi_catalog`).
* **Schemas:**
  * `bronze_staging`: Append-only raw ingested Delta tables + metadata audit log (`etl_run_log`).
  * `silver_conformed`: Cleansed, conformed units, deduplicated entities, sentinel coercion, text standardization, and SCD-2 tracking.
  * `gold_warehouse`: Kimball Star Schema (5 conformed dimensions + 3 multi-grain fact tables).
  * `gold_marts`: Materialized reporting views for Power BI DirectQuery (`vw_emissions_intensity`, `vw_plant_performance`, `vw_grid_stress`, `vw_monthly_generation_mix`).
  * `quarantine`: Dead-letter quarantine table (`rejected_records`) logging all discarded records with error reason codes.
* **Reporting & Visual BI:** Microsoft Power BI Desktop connected via Native Databricks Connector (DirectQuery pushdown to `gold_marts`).
