# 06_Dashboard

This directory houses the interactive **Microsoft Power BI Desktop** report (`PowerBI.pbix`) for the project.

---

## Required Dashboard Architecture (Phase 3 Rubric)

Per **`DWBI Lab Phase 3.pdf`**, the Power BI dashboard must include a **3-Page Report**:

1. **Page 1: Executive Overview**
   * High-level sector KPIs: Total Net Generation (MWh), Gross MW, Total Emissions ($\text{CO}_2, \text{SO}_2, \text{NO}_x$).
   * Carbon & pollutant emissions intensity metrics ($\text{CO}_2\text{ tons/MWh}$) by state, balancing authority, and fuel type.
   * Time-series trend of national electricity generation vs. emissions.
   * Primary View: `project_reporting.vw_emissions_intensity` (or Databricks `gold_marts.vw_emissions_intensity`).

2. **Page 2: Detailed Engineering Analysis (Plant Performance)**
   * Scatter plot / quadrant analysis of Plant Thermal Efficiency (Heat Rate in $\text{Btu/kWh}$) vs. Fuel Costs.
   * Filtering by prime mover technology (CCGT, Steam Turbine, Gas Peaker) and fuel source.
   * Identification of offline/maintenance facilities reporting negative net generation.
   * Primary View: `project_reporting.vw_plant_performance` (or Databricks `gold_marts.vw_plant_performance`).

3. **Page 3: Grid Decision Support (Synoptic Weather & Demand)**
   * Correlation between extreme ambient temperature (°C) and hourly balancing authority electricity demand (MW).
   * Fuel dispatch mix breakdown (Coal, Gas, Nuclear, Hydro, Wind, Solar) under grid peak loads.
   * Net interchange flows and renewable penetration rates.
   * Primary View: `project_reporting.vw_monthly_generation` (or Databricks `gold_marts.vw_grid_stress`).

---

## Supported Connection Configurations

### Track 1: Local PostgreSQL (Academic Submission Default)
* **Connector:** Power BI Desktop $\longrightarrow$ **Get Data** $\longrightarrow$ **PostgreSQL database**
* **Server:** `localhost:5432`
* **Database:** `dwbi_power_grid`
* **Target Schemas:** `project_reporting` (Gold Mart Views) and `project_dw` (Star Schema)
* **Mode:** Import / DirectQuery

### Track 2: Databricks Serverless SQL Warehouse (Cloud Lakehouse Option)
* **Connector:** Power BI Desktop $\longrightarrow$ **Get Data** $\longrightarrow$ **Databricks**
* **Server Hostname:** `dbc-xxxxxxxx-xxxx.cloud.databricks.com`
* **HTTP Path:** `/sql/1.0/warehouses/xxxxxxxxxxxxxxxx`
* **Port:** `443`
* **Default Catalog:** `dwbi_catalog`
* **Default Schema:** `gold_marts`
* **Mode:** DirectQuery / Import

