# Phase 1: Draw.io Diagram Instructions & Mermaid Source Code

Use these Mermaid codes in **[Draw.io](https://app.diagrams.net)** to generate your required **`Schema.pdf`** and architecture charts.

---

## How to Import into Draw.io

1. Open [app.diagrams.net](https://app.diagrams.net).
2. Create a new blank diagram.
3. In the top toolbar, click **`+`** (or **Arrange**) $\longrightarrow$ **Insert** $\longrightarrow$ **Advanced** $\longrightarrow$ **Mermaid**.
4. Paste either Code Block below and click **Insert**.
5. Adjust styling if desired, then click **File** $\longrightarrow$ **Export as** $\longrightarrow$ **PDF...** to save as `Schema.pdf`.

---

## 1. Dimensional Star Schema (Save as `Schema.pdf`)

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_HOURLY_EMISSIONS_WEATHER : "1:M"
    DIM_DATE ||--o{ FACT_MONTHLY_PLANT_OPERATIONS : "1:M"
    DIM_DATE ||--o{ FACT_REGIONAL_GRID_DEMAND : "1:M"
    DIM_PLANT ||--o{ FACT_HOURLY_EMISSIONS_WEATHER : "1:M"
    DIM_PLANT ||--o{ FACT_MONTHLY_PLANT_OPERATIONS : "1:M"
    DIM_PLANT ||--o{ DIM_GENERATOR : "1:M (SCD Type 2)"
    DIM_BALANCING_AUTHORITY ||--o{ FACT_REGIONAL_GRID_DEMAND : "1:M"
    DIM_WEATHER_STATION ||--o{ FACT_HOURLY_EMISSIONS_WEATHER : "1:M"

    DIM_DATE {
        int date_key PK "YYYYMMDD"
        date calendar_date
        smallint calendar_year
        smallint calendar_quarter
        smallint calendar_month
        varchar month_name
        smallint day_of_month
        smallint day_of_week
        varchar day_name
        boolean is_weekend
    }

    DIM_PLANT {
        int plant_key PK "Surrogate Key"
        int orispl_code UK "Master Business Key"
        varchar plant_name
        int utility_id
        varchar utility_name
        numeric latitude
        numeric longitude
        char state_code
        varchar county_name
        varchar ba_code
        smallint epa_region
        boolean is_combined_heat_power
    }

    DIM_GENERATOR {
        int generator_key PK "Surrogate Key"
        int orispl_code FK
        varchar generator_id
        varchar prime_mover_code
        varchar primary_energy_source
        numeric nameplate_capacity_mw
        varchar operating_status "OP, SB, RE"
        date row_effective_date "SCD Type 2"
        date row_expiration_date "SCD Type 2"
        boolean is_current "SCD Type 2"
    }

    DIM_BALANCING_AUTHORITY {
        int ba_key PK "Surrogate Key"
        varchar ba_code UK "PJM, CISO, ERCOT, MISO"
        varchar ba_name
        varchar region
        boolean is_active
    }

    DIM_WEATHER_STATION {
        int station_key PK "Surrogate Key"
        varchar station_id UK "USAF-WBAN / GHCN"
        varchar station_name
        char state_code
        numeric latitude
        numeric longitude
        numeric elevation_m
    }

    FACT_HOURLY_EMISSIONS_WEATHER {
        int date_key FK
        smallint hour_of_day PK
        int plant_key FK
        varchar unit_id PK
        int station_key FK
        numeric gross_load_mw "Gross Output"
        numeric heat_input_mmbtu "Thermal Fuel Energy"
        numeric so2_mass_lbs "Sulfur Dioxide"
        numeric nox_mass_lbs "Nitrogen Oxides"
        numeric co2_mass_tons "Carbon Dioxide"
        numeric ambient_temp_celsius "NOAA ISD Temp"
        numeric wind_speed_mps "NOAA ISD Wind"
        numeric weather_distance_km "Spatial Lineage"
    }

    FACT_MONTHLY_PLANT_OPERATIONS {
        int snapshot_key PK
        int month_start_date_key FK
        int plant_key FK
        varchar prime_mover_code
        varchar energy_source_code
        numeric net_generation_mwh "Can be negative during outages"
        numeric fuel_consumed_physical "Tons / Barrels / Mcf"
        numeric fuel_consumed_mmbtu
        numeric avg_heat_rate_btu_kwh "Thermal Efficiency"
        numeric delivered_fuel_cost_per_mmbtu
        numeric ending_fuel_stock_physical
    }

    FACT_REGIONAL_GRID_DEMAND {
        int date_key FK
        smallint hour_of_day PK
        int ba_key FK
        numeric demand_mw "Consumer Load"
        numeric demand_forecast_mw
        numeric net_gen_coal_mw
        numeric net_gen_gas_mw
        numeric net_gen_nuclear_mw
        numeric net_gen_hydro_mw
        numeric net_gen_wind_mw "Renewable"
        numeric net_gen_solar_mw "Renewable"
        numeric net_interchange_mw "Imports / Exports"
    }
```

---

## 2. End-to-End Pipeline Architecture Diagram

```mermaid
flowchart TD
    subgraph S1["1. MULTIPLE DATA SOURCES"]
        D1["EIA-930 API<br/>Hourly Grid Telemetry"]
        D2["EIA-860 & 923<br/>Multi-Tab Excel (.xlsx)"]
        D3["EPA CAMPD<br/>Hourly CEMS (JSON/CSV)"]
        D4["EPA-EIA Crosswalk<br/>Adjacency Bridge (CSV)"]
        D5["NOAA ISD<br/>Hourly Weather (Fixed-Width)"]
    end

    subgraph S2["2. PIPELINE ORCHESTRATION (Python)"]
        O1["Master Orchestrator<br/>(Extract & Load Controller)"]
    end

    subgraph S3["3. BRONZE LAYER (project_staging)"]
        B1["raw_eia860_generator"]
        B2["raw_eia860_enviro_assoc"]
        B3["raw_eia923_monthly_gen"]
        B4["raw_epa_hourly_emissions"]
        B5["raw_noaa_isd_weather"]
        B6["Ingestion Metadata<br/>(batch_id, loaded_at, source)"]
    end

    subgraph S4["4. DATA QUALITY & QUARANTINE"]
        Q1{"Data Quality<br/>Validation Engine"}
        Q_ERR["quarantine.rejected_records<br/>• -9999 Sentinels<br/>• '.' and 'NM' Strings<br/>• Heat Rate Boundary Violations<br/>• Referential Integrity Failures"]
    end

    subgraph S5["5. SILVER LAYER (Conformed & Enriched)"]
        SL1["Conformed Physical Units<br/>(MWh, MMBtu, lbs, tons)"]
        SL2["Bipartite Graph Modeling<br/>(Boiler ↔ Generator Crosswalk)"]
        SL3["Spatial ASOF Weather Join<br/>(Haversine Distance ≤ 50km)"]
        SL4["SCD Type 2 Engine<br/>(Generator State OP → RE)"]
    end

    subgraph S6["6. DIMENSIONAL DATA WAREHOUSE (project_dw)"]
        subgraph DIMS["Conformed Dimensions"]
            DIM1["Dim_Date"]
            DIM2["Dim_Plant"]
            DIM3["Dim_Generator (SCD 2)"]
            DIM4["Dim_Balancing_Authority"]
            DIM5["Dim_Weather_Station"]
        end
        subgraph FACTS["Kimball Fact Tables (>10,000 Rows)"]
            F1["Fact_Hourly_Emissions_Weather<br/>(Transactional Fact - Partitioned)"]
            F2["Fact_Monthly_Plant_Operations<br/>(Periodic Snapshot Fact)"]
            F3["Fact_Regional_Grid_Demand<br/>(Aggregate Grid Fact)"]
        end
    end

    subgraph S7["7. GOLD LAYER & REPORTING (project_reporting)"]
        V1["vw_emissions_intensity<br/>(Hourly Air Quality & CO2/MW)"]
        V2["vw_plant_performance<br/>(Monthly Efficiency & Fuel Costs)"]
        V3["vw_monthly_generation<br/>(Regional Renewable Penetration %)"]
    end

    subgraph S8["8. ANALYTICS & BI DASHBOARD"]
        P1["OLAP.sql<br/>(CUBE & ROLLUP)"]
        P2["Query Optimization<br/>(EXPLAIN ANALYZE + Indexes)"]
        P3["Power BI Dashboard<br/>Page 1: Executive Overview<br/>Page 2: Detailed Analysis<br/>Page 3: Grid Decisions"]
    end

    S1 --> O1
    O1 --> S3
    S3 --> Q1
    Q1 -- "Invalid" --> Q_ERR
    Q1 -- "Valid" --> S5
    S5 --> S6
    S6 --> S7
    S7 --> S8
```
