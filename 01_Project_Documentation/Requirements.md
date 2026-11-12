# DL3004 DWBI Project Requirements & Formal Specification

> **Official Phase 1 Deliverables Location:**  
> The complete academic Phase 1 proposal and design artifacts conforming to APA 7th Edition are preserved in the [archived/Phase_1_Submission/](../archived/Phase_1_Submission/) directory:
> 1. [Phase_1_Project_Proposal_and_Design_Document.md](../archived/Phase_1_Submission/Phase_1_Project_Proposal_and_Design_Document.md) – The master 8-chapter academic project proposal.
> 2. [Data_Dictionary.xlsx](../archived/Phase_1_Submission/Data_Dictionary.xlsx) – Authoritative multi-tab Excel data dictionary (4 schemas).
> 3. [Phase_1_Data_Dictionary.md](../archived/Phase_1_Submission/Phase_1_Data_Dictionary.md) – Formatted markdown data dictionary specification.
> 4. [Architecture_Pipeline_Diagram.png](../archived/Phase_1_Submission/Architecture_Pipeline_Diagram.png) – Visual 8-stage pipeline architecture flowchart.
> 5. [Schema_Diagram.jpg](../archived/Phase_1_Submission/Schema_Diagram.jpg) – Visual Kimball Star Schema entity-relationship blueprint.
> 6. [Phase_1_Architecture_and_Schema_Specification.md](../archived/Phase_1_Submission/Phase_1_Architecture_and_Schema_Specification.md) – 11-stage pipeline blueprint, validation formulas, and DDL.
> 7. [Phase_1_Project_Execution_Plan.md](../archived/Phase_1_Submission/Phase_1_Project_Execution_Plan.md) – Team collaboration framework, Git workflow, and 8-week roadmap.
> 8. [Phase_1_Executive_Summary_and_Checklist.md](../archived/Phase_1_Submission/Phase_1_Executive_Summary_and_Checklist.md) – Compliance audit matrix and docx/pdf export guide.

---

## 1. Project Title and Metadata
* **Project Name:** U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Lakehouse / Warehouse
* **Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)
* **Institution:** FAST National University of Computer and Emerging Sciences
* **Academic Term:** Fall 2026

## 2. Project Team Members & Collaborative Structure
* **Muhammad Ibrahim [24L-2602]**
* **Rai Fahad Sultan [24L-2509]**
* **Muhammad Ayyan [24L-2568]**
* **Taha Imran [24L-2560]**

*Collaboration Model:* Cross-functional agile collaboration. All members participate equally and flexibly across all data engineering, dimensional modeling, data quality, OLAP, and Power BI reporting tasks without rigid role boundaries.

## 3. Technology Stack (Databricks Serverless Cloud Lakehouse)
* **Lakehouse Platform:** Databricks Serverless Compute (Photon Engine) + Databricks SQL Warehouse.
* **Storage & Governance:** Delta Lake + Unity Catalog (`dwbi_catalog` schemas: `bronze_staging`, `silver_conformed`, `gold_warehouse`, `gold_marts`, `quarantine`).
* **ETL & Data Engineering:** Apache Spark / PySpark & Databricks SQL (Delta `MERGE INTO`).
* **Visualization & BI:** Microsoft Power BI Desktop (`PowerBI.pbix` via Native Databricks DirectQuery).
* **Modeling & Architecture:** Draw.io & Markdown.

## 4. Summary of Data Sources
* **EIA-860:** Generator asset inventory and boiler-generator environmental associations.
* **EIA-923:** Monthly net electrical generation, fuel consumed, and thermal heat rates.
* **EIA-930:** Hourly regional grid electrical demand and fuel mix telemetry.
* **EPA CAMPD:** Continuous Emission Monitoring System (CEMS) gross MW, heat input, $\text{SO}_2, \text{NO}_x, \text{CO}_2$ emissions.
* **EPA-EIA Crosswalk:** Official federal bipartite crosswalk bridging boilers to generators.
* **NOAA ISD:** Hourly synoptic surface weather observations (ambient temperature, wind speed).

## 5. Formal Analytical Business Questions (10 Core Questions)
See [Business_Requirements_Document.md](Business_Requirements_Document.md) for full metadata, measure classifications, and grain statements.

| ID | Business Question Statement | Fact Table | Reporting View / OLAP Query | Dashboard Page |
| :-: | :--- | :--- | :--- | :-: |
| **BQ1** | Facility emissions intensity & regional distribution ($\text{CO}_2, \text{SO}_2, \text{NO}_x$) | `fact_hourly_emissions_weather` | `vw_emissions_intensity` & OLAP Query 4 | Page 1, 2 |
| **BQ2** | Synoptic weather stress vs. emissions intensity and gross load | `fact_hourly_emissions_weather` | `vw_emissions_intensity` & OLAP Query 6 | Page 2 |
| **BQ3** | Prime mover and fuel thermal efficiency / heat rate benchmarking | `fact_monthly_plant_operations` | `vw_plant_performance` & OLAP Query 1 | Page 2 |
| **BQ4** | Station auxiliary load outages and negative net electrical generation | `fact_monthly_plant_operations` | `vw_plant_performance` & OLAP Query 7 | Page 2 |
| **BQ5** | Balancing authority peak demand, renewable penetration, and interchanges | `fact_regional_grid_demand` | `vw_grid_stress` & OLAP Query 2 | Page 1, 3 |
| **BQ6** | Cross-agency generation reconciliation (EPA Gross vs EIA Net) & auxiliary ratio | `fact_hourly_emissions_weather`, `fact_monthly_plant_operations` | DQ `ACC_AUX_LOAD_RECON` & OLAP Query 8 | Page 2 |
| **BQ7** | Generator asset lifecycle and SCD Type 2 decommissioning tracking | `dim_generator` (SCD Type 2) | OLAP Query 9 | Page 2 |
| **BQ8** | Extreme climatic stress (winter freeze / summer heat) vs. grid dispatch & deficits | `fact_regional_grid_demand` | `vw_grid_stress` & OLAP Query 10 | Page 3 |
| **BQ9** | Thermal efficiency degradation & heat-rate exceedance frequency by plant | `fact_monthly_plant_operations`, `fact_hourly_emissions_weather` | `vw_plant_performance` & OLAP Query 11 | Page 2 |
| **BQ10**| Multi-year generation trends and decarbonization by prime mover technology | `fact_monthly_plant_operations` | `vw_monthly_generation_mix` & OLAP Query 3 | Page 2 |

## 6. Dimensional Architecture, Grains & Hierarchies
* **Fact Table Grains:**
  * `fact_hourly_emissions_weather`: Hourly per plant and CEMS monitoring unit (`date_key`, `hour_of_day`, `plant_key`, `unit_id`).
  * `fact_monthly_plant_operations`: Monthly per plant, prime mover, and energy source (`month_start_date_key`, `plant_key`, `prime_mover_code`, `energy_source_code`).
  * `fact_regional_grid_demand`: Hourly per balancing authority (`date_key`, `hour_of_day`, `ba_key`).
* **Dimension Hierarchies:**
  * **Date:** Day (`calendar_date`) -> Month (`calendar_month`) -> Quarter (`calendar_quarter`) -> Year (`calendar_year`).
  * **Plant:** Unit / CEMS Flue -> Plant (`orispl_code`) -> County -> State (`state_code`) -> NERC Region -> Interconnection.
  * **Generator (SCD-2):** Unit -> Plant -> Energy Source -> Prime Mover -> Operating Status (Tracked via `valid_from`, `valid_to`, `is_current`).
  * **Balancing Authority:** BA Code -> BA Name -> NERC Region -> Interconnection.
  * **Weather Station:** Station ID -> Station Name -> State -> Climate Zone -> Lat/Lon Spatial Grid.

## 7. Reporting Layer Views (`dwbi_catalog.gold_marts`)
* `vw_emissions_intensity`: Flue emissions, gross load, ambient temperature (Feeds Page 1).
* `vw_plant_performance`: Monthly fuel consumption, net generation, and heat rate efficiency flags (Feeds Page 2).
* `vw_grid_stress`: Hourly balancing authority demand, day-ahead forecast error, and renewable coverage alerts (Feeds Page 3).
* `vw_monthly_generation_mix`: Monthly prime mover and fuel generation trends and decarbonization tracking (Feeds Page 2 & BQ10).


