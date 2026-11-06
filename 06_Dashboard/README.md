# 06_Dashboard

This directory houses the interactive **Microsoft Power BI Desktop** report (`PowerBI.pbix`) for the project, connected directly to **Databricks Serverless SQL Warehouse**.

---

## Required Dashboard Architecture (Phase 3 Rubric)

Per **`DWBI Lab Phase 3.pdf`**, the Power BI dashboard implements a **3-Page Report**:

1. **Page 1: Executive Overview**
   * High-level sector KPIs: Total Net Generation (MWh), Gross MW, Total Emissions ($\text{CO}_2, \text{SO}_2, \text{NO}_x$).
   * Carbon & pollutant emissions intensity metrics ($\text{CO}_2\text{ tons/MWh}$) by state, balancing authority, and fuel type.
   * Time-series trend of national electricity generation vs. emissions.
   * Primary Source: `dwbi_catalog.gold_marts.vw_emissions_intensity`.

2. **Page 2: Detailed Engineering Analysis (Plant Performance)**
   * Scatter plot / quadrant analysis of Plant Thermal Efficiency (Heat Rate in $\text{Btu/kWh}$) vs. Fuel Costs.
   * Filtering by prime mover technology (CCGT, Steam Turbine, Gas Peaker) and fuel source.
   * Identification of offline/maintenance facilities reporting negative net generation.
   * Primary Source: `dwbi_catalog.gold_marts.vw_plant_performance`.

3. **Page 3: Grid Decision Support (Synoptic Weather & Demand)**
   * Correlation between extreme ambient temperature (°C) and hourly balancing authority electricity demand (MW).
   * Fuel dispatch mix breakdown (Coal, Gas, Nuclear, Hydro, Wind, Solar) under grid peak loads.
   * Net interchange flows and renewable penetration rates.
   * Primary Source: `dwbi_catalog.gold_marts.vw_grid_stress`.

---

## Databricks Power BI Connection Configuration

Connect Power BI Desktop directly to your Databricks Serverless SQL Warehouse:

* **Connector:** Power BI Desktop $\longrightarrow$ **Get Data** $\longrightarrow$ **Databricks**
* **Server Hostname:** `dbc-xxxxxxxx-xxxx.cloud.databricks.com`
* **HTTP Path:** `/sql/1.0/warehouses/xxxxxxxxxxxxxxxx`
* **Port:** `443`
* **Default Catalog:** `dwbi_catalog`
* **Default Database / Schema:** `gold_marts` (and `gold_warehouse`)
* **Connection Mode:** **DirectQuery** (for live real-time queries) or **Import** (for ultra-fast cached slicing).
