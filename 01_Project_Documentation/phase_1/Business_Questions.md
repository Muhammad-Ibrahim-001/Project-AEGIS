# ==============================================================================
# BUSINESS QUESTIONS SPECIFICATION (PROJECT-AEGIS)
# Project: U.S. Bulk Power Generation, Smokestack Emissions & Weather Lakehouse
# Course:  DL3004 Data Warehousing & Business Intelligence (DWBI)
# Catalog: dwbi_catalog (Databricks Serverless Cloud Lakehouse)
# ==============================================================================

This document provides the authoritative, standalone specification of all 10 core analytical Business Questions (BQ1 through BQ10) that govern the dimensional architecture, fact and dimension design, and reporting delivery of Project-AEGIS.

---

## 1. Executive Summary & Analytical Scope

Project-AEGIS integrates four federal energy and environmental datasets across the contiguous United States for the 2021–2024 compliance window:
- **EIA-860 & EIA-860M:** Generator technology, prime movers, operating statuses, and nameplate capacity.
- **EIA-923:** Monthly net generation and fuel thermal heat input by plant and prime mover.
- **EPA CAMPD (CEMS):** Continuous smokestack monitoring of hourly electrical gross output and $\text{CO}_2, \text{SO}_2, \text{NO}_x$ emissions.
- **NOAA ISD:** Synoptic surface meteorological observations (ambient dry-bulb temperature, surface wind velocity, barometric pressure).
- **EIA-930:** Hourly regional balancing authority electric load demand, day-ahead forecast, and fuel dispatch mix.

The 10 business questions below are mapped directly to Kimball star schema artifacts, analytical reporting marts (`dwbi_catalog.gold_marts`), and OLAP SQL queries (`05_Analytics/olap_queries.sql`).

---

## 2. Business Questions Specification (BQ1 – BQ10)

### BQ1: Facility Emissions Intensity & Regional Distribution
* **Question Statement:** Which power generating facilities and states emit the highest rates of $\text{CO}_2$, $\text{SO}_2$, and $\text{NO}_x$ per unit of gross generation (tons/MW or lbs/MW), and how does emissions intensity fluctuate month-over-month?
* **Business Intent:** Environmental compliance auditing, regional carbon footprint benchmarking, and identifying high-polluting peaker units under federal Clean Air Act standards.
* **Target Persona:** Environmental Regulators & Corporate Sustainability Officers (Power BI Page 1).
* **Fact Table:** `gold_warehouse.fact_hourly_emissions_weather` (Transactional Fact)
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `gross_load_mw` (Additive)
  * `co2_mass_tons` (Additive)
  * `so2_mass_lbs` (Additive)
  * `nox_mass_lbs` (Additive)
  * `co2_intensity_tons_per_mw` (Calculated Ratio / Non-Additive)
* **Grain:** Hourly per generating plant and CEMS monitoring unit (`date_key`, `hour_of_day`, `plant_key`, `unit_id`).
* **Matching Reporting View / Query:** `gold_marts.vw_emissions_intensity` & OLAP Query 4 (Window Functions: Facility Emissions Intensity Benchmarking & Dense Ranking).

---

### BQ2: Synoptic Weather Stress vs. Emissions & Generation
* **Question Statement:** How do extreme ambient temperatures (polar freeze below 0°C and heat waves above 28°C) and surface wind speeds affect hourly generation load and smokestack emissions intensity?
* **Business Intent:** Thermodynamic derating assessment, cooling water intake stress evaluation during droughts, and gas turbine compressor performance benchmarking across temperature regimes.
* **Target Persona:** Plant Performance Engineers (Power BI Page 2).
* **Fact Table:** `gold_warehouse.fact_hourly_emissions_weather` (Transactional Fact)
* **Dimension Tables:** `dim_plant`, `dim_weather_station`, `dim_date`
* **Measures:** 
  * `gross_load_mw` (Additive)
  * `co2_mass_tons` (Additive)
  * `ambient_temp_celsius` (Non-Additive / Semi-Additive average)
  * `wind_speed_mps` (Non-Additive / Semi-Additive average)
  * `weather_distance_km` (Semi-Additive)
* **Grain:** Hourly per generating plant and nearest surface weather station (`date_key`, `hour_of_day`, `plant_key`, `unit_id`).
* **Matching Reporting View / Query:** `gold_marts.vw_emissions_intensity` & OLAP Query 6 (Weather Extremes vs Emissions & Load Slicing).

---

### BQ3: Thermal Efficiency (Heat Rate) Degradation by Prime Mover
* **Question Statement:** Which prime mover technologies (Combined Cycle, Steam Turbine, Combustion Turbine Peakers) exhibit the highest thermodynamic heat rates (Btu/kWh), and what is the seasonal efficiency penalty during summer peak conditions?
* **Business Intent:** Identifies aging or fouled thermal generators that consume excessive fuel per MWh produced, driving merit-order economic dispatch and carbon pricing models.
* **Target Persona:** Power Generation Fleet Managers (Power BI Page 2).
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations` (Periodic Snapshot Fact)
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `net_generation_mwh` (Additive)
  * `fuel_consumed_mmbtu` (Additive)
  * `avg_heat_rate_btu_kwh` (Non-Additive Weighted Avg)
* **Grain:** Monthly per generating plant, prime mover, and energy source code (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 1 (Multi-Dimensional CUBE Aggregation).

---

### BQ4: Auxiliary Load Consumption & Outage Auditing
* **Question Statement:** Which generating facilities experience extended maintenance shutdowns where station service power consumption results in negative net generation (`net_generation_mwh < 0`), and what is the total energy consumed from the grid during these periods?
* **Business Intent:** Audits auxiliary transformer load consumption, uncovers forced outages and maintenance schedules, and verifies correct accounting of station service power.
* **Target Persona:** Generation Asset Managers & NERC Reliability Auditors (Power BI Page 2).
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations` (Periodic Snapshot Fact)
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `net_generation_mwh` (Additive)
  * `fuel_consumed_mmbtu` (Additive)
  * `outage_frequency` (Additive Count)
* **Grain:** Monthly per generating plant, prime mover, and energy source (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 7 (Plant Auxiliary Load Outages & Negative NetGen Audit).

---

### BQ5: Regional Transmission Grid Demand & Renewable Penetration
* **Question Statement:** What is the hourly correlation between total balancing authority electrical load demand and clean renewable dispatch (wind + solar), and during which seasonal hours does clean energy penetration peak versus thermal baseload?
* **Business Intent:** Transmission capacity expansion planning, curtailment mitigation, battery energy storage sizing, and NERC grid adequacy compliance.
* **Target Persona:** Transmission Grid Operators & Energy Traders (Power BI Page 3).
* **Fact Table:** `gold_warehouse.fact_regional_grid_demand` (Aggregate Transmission Grid Fact)
* **Dimension Tables:** `dim_balancing_authority`, `dim_date`
* **Measures:** 
  * `demand_mw` (Semi-Additive)
  * `net_gen_wind_mw` (Additive)
  * `net_gen_solar_mw` (Additive)
  * `total_renewable_generation_mw` (Additive)
  * `renewable_penetration_pct` (Calculated Ratio)
* **Grain:** Hourly per Balancing Authority territory (`date_key`, `hour_of_day`, `ba_key`).
* **Matching Reporting View / Query:** `gold_marts.vw_grid_stress` & OLAP Query 2 (Hierarchical ROLLUP Aggregation).

---

### BQ6: Physical Auxiliary Reconciliation (EPA Gross vs. EIA Net)
* **Question Statement:** Does gross generation reported by EPA CAMPD continuous smokestack monitors exceed net generation reported by EIA-923 monthly utility schedules by the physical thermodynamic auxiliary load ratio ($3\% \le \text{Aux Ratio} \le 14\%$)?
* **Business Intent:** Cross-agency data quality auditing, reconciling Continuous Emission Monitoring Systems (CEMS) against billing meters, and detecting sensor calibration drift.
* **Target Persona:** Data Quality Engineers & Regulatory Compliance Auditors.
* **Fact Tables:** `gold_warehouse.fact_hourly_emissions_weather`, `gold_warehouse.fact_monthly_plant_operations`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `total_gross_mw` (Additive)
  * `total_net_mwh` (Additive)
  * `auxiliary_load_ratio_pct` (Calculated Ratio / Non-Additive)
* **Grain:** Monthly per generating facility (`plant_key`, `calendar_year`, `calendar_month`). Pre-aggregated in CTEs before joining.
* **Matching Reporting View / Query:** DQ Validation Suite (`ACC_AUX_LOAD_RECON`) & OLAP Query 8 (Cross-Agency Generation Reconciliation).

---

### BQ7: Generator Asset Lifecycle & SCD Type 2 Tracking
* **Question Statement:** How do generator operating statuses (Operating $\rightarrow$ Standby $\rightarrow$ Retired) and nameplate capacities evolve over time, and what is the cumulative retired thermal capacity across coal and gas fleets?
* **Business Intent:** Tracking the clean energy transition, coal decommissioning trajectory, peaker reserve standby capacity, and stranded asset risk.
* **Target Persona:** Strategic Resource Planners & Regulatory Economists.
* **Dimension Table:** `gold_warehouse.dim_generator` (Slowly Changing Dimension Type 2)
* **Measures:** 
  * `nameplate_capacity_mw` (Additive)
  * `total_historical_revisions` (Calculated Window Count)
  * `cumulative_retired_mw` (Additive)
* **Grain:** Current and historical generator asset versions tracked via `valid_from`, `valid_to`, and `is_current`.
* **Matching Reporting View / Query:** OLAP Query 9 (SCD Type 2 Generator Decommissioning Trajectory).

---

### BQ8: Extreme Climatic Stress vs. Regional Grid Dispatch & Reserve Deficits
* **Question Statement:** During severe meteorological stress events (polar vortex freezes and summer heat domes), how do regional demand forecast error residuals ($\text{Demand} - \text{Forecast}$) escalate, and how does thermal generation ramp up to maintain grid reliability?
* **Business Intent:** Evaluates grid vulnerability to under-forecasting during climatic extremes, loss-of-load probability (LOLP), and emergency spinning reserve adequacy.
* **Target Persona:** ISO/RTO Reliability Coordinators & Dispatch Engineers (Power BI Page 3).
* **Fact Tables:** `gold_warehouse.fact_regional_grid_demand`, `gold_warehouse.fact_hourly_emissions_weather`
* **Dimension Tables:** `dim_balancing_authority`, `dim_plant`, `dim_date`
* **Measures:** 
  * `demand_mw` (Semi-Additive)
  * `demand_forecast_mw` (Semi-Additive)
  * `forecast_residual_error_mw` (Calculated Additive Residual)
  * `grid_thermal_dispatch_mw` (Additive)
  * `plant_monitored_gross_mw` (Additive)
* **Grain:** Hourly per balancing authority during flagged climatic freeze and peak dates (`date_key`, `hour_of_day`, `ba_code`). Pre-aggregated in CTEs before joining.
* **Matching Reporting View / Query:** `gold_marts.vw_grid_stress` & OLAP Query 10 (Climatic Stress Grid Dispatch & Reserve Margin Window Analysis).

---

### BQ9: Thermal Efficiency Degradation & Out-of-Bounds Heat Rate Operating Frequency by Plant
* **Question Statement:** How many operating months per calendar year do thermal power plants run at degraded thermodynamic efficiencies exceeding standard technology heat-rate thresholds (CCGT > 10,000 Btu/kWh, Coal Steam > 14,000 Btu/kWh, Peakers > 16,000 Btu/kWh), and what is the associated fuel consumption penalty and carbon impact?
* **Business Intent:** Identifies generating units suffering boiler fouling, cooling tower derating, or severe compressor degradation, prioritizing thermal units for maintenance overhaul, heat rate improvement, or retirement.
* **Target Persona:** Generation Asset Reliability Engineers & Environmental Compliance Officers.
* **Fact Tables:** `gold_warehouse.fact_monthly_plant_operations`, `gold_warehouse.fact_hourly_emissions_weather`
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `net_generation_mwh` (Additive)
  * `fuel_consumed_mmbtu` (Additive)
  * `avg_heat_rate_btu_kwh` (Non-Additive Weighted Avg)
  * `degraded_efficiency_months_count` (Additive)
  * `degraded_operating_pct` (Calculated Ratio)
  * `annual_co2_tons` (Additive)
* **Grain:** Annual per generating plant, prime mover, and energy source (`plant_key`, `calendar_year`). Pre-aggregated in CTEs before joining.
* **Matching Reporting View / Query:** `gold_marts.vw_plant_performance` & OLAP Query 11 (Thermal Efficiency Degradation & Heat-Rate Exceedance Frequency).

---

### BQ10: Multi-Year Generation Trends & Decarbonization by Prime Mover
* **Question Statement:** How has the generation mix, total net generation volume, and weighted heat rate transitioned across prime mover technologies (Combined Cycle, Steam Turbine, Gas Turbine, Wind, Solar) over the 2021-2024 compliance window?
* **Business Intent:** Evaluates long-term fleet transition from coal baseload to natural gas and renewables, measuring fleet carbon productivity and decarbonization velocity.
* **Target Persona:** Executive Leadership & Energy Policy Makers (Power BI Page 2 & BQ10).
* **Fact Table:** `gold_warehouse.fact_monthly_plant_operations` (Periodic Snapshot Fact)
* **Dimension Tables:** `dim_plant`, `dim_date`
* **Measures:** 
  * `total_net_generation_mwh` (Additive)
  * `total_fuel_mmbtu` (Additive)
  * `weighted_heat_rate_btu_kwh` (Non-Additive Weighted Avg)
  * `mom_net_gen_growth_mwh` (Calculated Window Metric)
  * `moving_3month_avg_net_gen_mwh` (Calculated Window Metric)
* **Grain:** Monthly per state, prime mover, and energy source code (`calendar_year`, `calendar_month`, `state_code`, `prime_mover_code`, `energy_source_code`).
* **Matching Reporting View / Query:** `gold_marts.vw_monthly_generation_mix` & OLAP Query 3 (Window Functions: MoM Net Generation Growth & Moving Averages).
