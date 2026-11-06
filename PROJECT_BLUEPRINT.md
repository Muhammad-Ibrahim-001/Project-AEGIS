# Master Project Specification: U.S. Power Generation, Smokestack Emissions & Synoptic Weather Lakehouse / Warehouse

> **System Purpose & Audience:**  
> This document is the **canonical technical blueprint** for the DL3004 Data Warehousing & Business Intelligence (DWBI) Final Project. It contains the complete architectural, algorithmic, dimensional, and operational context required for an AI coding assistant or software engineer to understand, implement, debug, and expand the project across sessions without loss of context.

---

## 1. Project Overview & Course Requirements

### 1.1 Academic & Portfolio Context
* **Course:** DL3004 Data Warehousing and Business Intelligence (DWBI) Final Project.
* **Objective:** Implement an enterprise-grade, end-to-end analytical data pipeline:
  $$\text{Source Systems} \longrightarrow \text{Ingestion} \longrightarrow \text{Bronze (Staging)} \longrightarrow \text{Data Quality/Quarantine} \longrightarrow \text{Silver} \longrightarrow \text{Data Warehouse} \longrightarrow \text{OLAP Analysis} \longrightarrow \text{BI Reporting}$$
* **Architecture Tracks:**
  * **Track 1 (University Submission Default):** Zero-cost local execution stack:
    * **Database & Engine:** PostgreSQL 16+ (`localhost:5432`, `dwbi_power_grid`).
    * **Schemas:** `project_staging`, `quarantine`, `project_dw`, `project_reporting`.
    * **ETL & Data Engineering:** Python 3.10+ (Pandas, openpyxl, requests, psycopg2).
    * **Visualization & BI:** Microsoft Power BI Desktop (`PowerBI.pbix` connecting to `localhost:5432`).
    * **Design & Schemas:** Draw.io (architecture diagram), GitHub (code repository).
  * **Track 2 (Modern Cloud Lakehouse Extension):** Databricks Serverless Compute + Delta Lake + Unity Catalog (`dwbi_catalog`) + Power BI DirectQuery. Detailed in [`DATABRICKS_SERVERLESS_ARCHITECTURE.md`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md).

### 1.2 Alignment with Official Course Architecture
The course syllabus provides a conceptual retail example ("CampusCart") and an architecture flowchart (`Sample Project Architecture Diagram.png`). This project **replaces the toy retail data with a real-world industrial and climate dataset**, while maintaining an exact **1-to-1 structural mapping** across all 11 architectural components:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          11-STAGE ARCHITECTURE MAPPING                                 │
├────┬─────────────────────────────┬─────────────────────────────────────────────────────┤
│ #  │ Architecture Diagram Box    │ Project Implementation                              │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 1  │ Multiple Data Sources       │ EIA-860 (Excel), EIA-923 (Excel), EIA-930 (API),    │
│    │                             │ EPA CAMPD (JSON/CSV), NOAA ISD (Fixed-width), Crosswalk│
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 2  │ Pipeline Orchestration      │ Python controller: Ingest → Validate → Silver →     │
│    │                             │ Load Dims → Load Facts → Marts → Audit & Reconcile  │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 3  │ Bronze Layer (Landing)      │ Immutable raw tables + metadata: `batch_id`,        │
│    │                             │ `source_system`, `ingested_at`                      │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 4  │ Data Quality & Quarantine   │ Rejection rules → Dead-letter quarantine table with │
│    │                             │ `rejection_reason`, `source_batch_id`, `rejected_at`│
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 5  │ Silver Layer                │ Cleaned, conformed units (MWh, MMBtu, lbs, tons);   │
│    │                             │ Deduplicated ORISPL plant codes; Watermark tracking │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ SCD│ SCD Processing              │ SCD Type 1 (typo fixes) & SCD Type 2 (generator     │
│    │                             │ operating status: Operating → Retired + timestamps) │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 6  │ Dimensional Data Warehouse  │ Kimball Star Schema: 3 Fact types (Transactional,   │
│    │                             │ Periodic Snapshot, Factless) + Conformed Dimensions │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 7  │ Warehouse Performance       │ PostgreSQL declarative table partitioning by month, │
│    │                             │ B-Tree indexes on FKs/dates, EXPLAIN ANALYZE tests  │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 8  │ Gold Layer (Data Marts)     │ Materialized Views: Emissions Intensity Mart, Heat  │
│    │                             │ Rate Anomaly Mart, Regional Grid Stress Mart        │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 9  │ Analytics & BI              │ Analytical SQL: Window functions (`LAG`, `LEAD`),   │
│    │                             │ OLAP (`ROLLUP`, `CUBE`), Power BI visual dashboard  │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 10 │ Audit & Reconciliation      │ ETL run logging: Rows read/inserted/rejected;       │
│    │                             │ Conservation audits: EPA Gross MWh vs EIA Net MWh   │
├────┼─────────────────────────────┼─────────────────────────────────────────────────────┤
│ 11 │ Metadata & Lineage          │ Complete data catalog tracing source → DW → Power BI│
└────┴─────────────────────────────┴─────────────────────────────────────────────────────┘
```

---

## 2. Authoritative Data Sources Directory

All sources are 100% public, verified, and free.

| Source System | Agency | Primary Entity & Measure | Native File Format | Native Grain | Official Access URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EIA-860** | EIA | Plant & generator asset inventory; `6_1_EnviroAssoc` crosswalk | Multi-tab Excel (`.xlsx`) | Annual per Generator / Boiler | [EIA-860 Archive](https://www.eia.gov/electricity/data/eia860/) |
| **EIA-860M** | EIA | Monthly updates to operating/retired generators | Excel (`.xlsx`) | Monthly per Generator | [EIA-860M Portal](https://www.eia.gov/electricity/data/eia860m/) |
| **EIA-923** | EIA | Monthly net generation (`Netgen_MWh`), fuel consumed, thermal MMBtu, fuel stocks | Multi-tab Excel (`.xlsx`) | Monthly per Prime Mover / Fuel | [EIA-923 Archive](https://www.eia.gov/electricity/data/eia923/) |
| **EIA-930** | EIA | Real-time regional grid electrical demand, generation by fuel mix, interconnector flows | REST JSON API / CSV | Hourly per Balancing Authority (BA) | [EIA Grid Monitor](https://www.eia.gov/electricity/gridmonitor/dashboard/electric_overview/US48/US48) |
| **EPA CAMPD** | EPA | Continuous Emission Monitoring (CEMS): Gross MW, heat input, $\text{SO}_2, \text{NO}_x, \text{CO}_2$ emissions | REST JSON API / Bulk CSV | Hourly per Smokestack / Boiler Unit | [EPA CAMPD Portal](https://campd.epa.gov/) & [Bulk Files](https://campd.epa.gov/data/bulk-data-files) |
| **EPA–EIA Crosswalk** | EPA / EIA | Authoritative identifier crosswalk bridging ORISPL, Boiler ID, and Generator ID | CSV / Excel | Bipartite Adjacency Linkage | [EPA-EIA Crosswalk](https://www.epa.gov/power-sector/power-sector-data-crosswalk) |
| **NOAA ISD** | NOAA NCEI | Hourly synoptic weather observations: temperature, wind speed, dew point, pressure | Fixed-width / CSV | Hourly per Weather Station | [NOAA ISD Portal](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database) |
| **FERC Form 1** | FERC | Utility financial ledger, O&M costs, plant capital, joint-venture ownership shares | Visual FoxPro `.dbf` & XBRL | Annual per Utility / Plant | [FERC Form 1 VFP](https://www.ferc.gov/general-information-0/electric-industry-forms/form-1-1-f-3-q-electric-historical-vfp-data) |

---

## 3. Empirical Stress-Test Benchmarks & Real-World Gotchas

The pipeline must defensively handle the following verified upstream anomalies:

### 3.1 Shifting Header Row Offsets in Excel
* **EIA-860 (`6_1_EnviroAssoc_Y2023.xlsx`):** Header row is on **Row 2** (0-indexed row 1). Row 1 is a single title string.
* **EIA-923 (`EIA923_Schedules_2_3_4_5_M_12_2023_Final_Revision.xlsx`):** Header row is on **Row 6** (0-indexed row 5). Rows 1–3 are metadata, Row 4 is completely blank, and Row 5 contains grouped category labels.
* **Pipeline Requirement:** Bronze extractors must dynamically search for rows containing `'Plant Code'` or `'Plant Id'` rather than using hardcoded row indices.

### 3.2 String Sentinels in Numeric Columns
* **EIA-923:** Missing numeric values in columns like `Quantity\nJanuary` and `Nuclear Unit Id` are populated with literal strings like `"."` and `"NM"` (Not Meaningful).
* **NOAA Weather Feeds:** Missing sensor measurements are hardcoded as integer **`-9999`**. Single-character quality flags (`QFLAG` = `Z`, `T`) are directly appended to numbers without delimiters.
* **Pipeline Requirement:** Data type coercion must replace `"."`, `"NM"`, and `-9999` with SQL `NULL` and extract flags into separate quality-indicator fields before inserting into typed PostgreSQL columns.

### 3.3 Negative Net Generation (Station Service Outages)
* **Empirical Fact:** In EIA-923 January 2023 data alone, **41 plants reported negative net generation** (e.g., Plant 26 `E C Gaston` reported `-3,555.565 MWh`; Plant 30 `Madelia` reported `-12.78 MWh`).
* **Root Cause:** When generating units are offline for maintenance, they draw electrical power *from* the grid to operate safety systems, pumps, draft fans, and building heating.
* **Pipeline Requirement:** Database constraints must allow negative net generation, but flag records where $\text{Net Generation} < 0$ with an audit condition code (`STATION_SERVICE_EXCEEDS_OUTPUT`).

### 3.4 Population Discrepancy & Non-Thermal Orphan Keys
* **EIA-860 `EnviroAssoc`:** Contains 1,568 thermal generating plants with combustion boilers.
* **EIA-923 Generation:** Contains 12,308 plants across all fuel sources.
* **The Trap:** Exactly **10,955 plants** in EIA-923 have no records in `EnviroAssoc` because hydroelectric dams (e.g., `Plant Id 2: Bankhead Dam`), solar farms, and wind turbines do not have combustion boilers.
* **Pipeline Requirement:** Never execute a raw `INNER JOIN` between generation fact tables and boiler environmental schedules. Non-thermal assets must route through conditional dimensional bridges with default surrogate keys (`-1 = Not Applicable`).

---

## 4. Dimensional Modeling & Star Schema Specification

The warehouse implements a **Kimball Dimensional Model** optimized for analytical queries and Power BI integration.

```
                                  ┌──────────────────────────┐
                                  │         Dim_Date         │
                                  ├──────────────────────────┤
                                  │ PK  Date_Key (YYYYMMDD)  │
                                  │     Calendar_Year        │
                                  │     Calendar_Month       │
                                  │     Day_Of_Week          │
                                  │     Is_Weekend           │
                                  └─────────────┬────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │ 1:M                          │ 1:M                          │ 1:M
                 ▼                              ▼                              ▼
  ┌──────────────────────────────┐┌──────────────────────────────┐┌──────────────────────────────┐
  │Fact_Hourly_Emissions_Weather ││Fact_Monthly_Plant_Operations ││Fact_Regional_Grid_Demand     │
  ├──────────────────────────────┤├──────────────────────────────┤├──────────────────────────────┤
  │ FK Date_Key                  ││ FK Date_Key (Month Start)    ││ FK Date_Key                  │
  │ FK Time_Key (Hour 0-23)      ││ FK Plant_Key                 ││ FK Balancing_Authority_Key   │
  │ FK Plant_Key                 ││ FK Prime_Mover_Key           ││    Demand_MW                 │
  │ FK Unit_Key (Boiler/Stack)   ││ FK Fuel_Key                  ││    Forecast_Demand_MW        │
  │ FK Station_Key (Nearest NOAA)││    Net_Generation_MWh        ││    Net_Generation_Coal_MW    │
  │    Gross_Load_MW             ││    Fuel_Consumed_Physical    ││    Net_Generation_Gas_MW     │
  │    Heat_Input_MMBtu          ││    Fuel_Consumed_MMBtu       ││    Net_Generation_Solar_MW   │
  │    SO2_Mass_lbs              ││    Delivered_Cost_Per_MMBtu  ││    Net_Generation_Wind_MW    │
  │    NOx_Mass_lbs              ││    Ending_Fuel_Stock_Qty     ││    Interchange_Flow_MW       │
  │    CO2_Mass_Tons             │└──────────────────────────────┘└──────────────────────────────┘
  │    Hourly_Temperature_C      │    (Kimball Periodic Snapshot)     (Kimball Aggregate Grid Fact)
  │    Hourly_Wind_Speed_mps     │
  │    Weather_Distance_KM       │
  └──────────────────────────────┘
    (Kimball Transactional Fact)
                 │                              │                              │
                 ├──────────────────────────────┼──────────────────────────────┘
                 │ M:1                          │ M:1
                 ▼                              ▼
  ┌──────────────────────────────┐┌──────────────────────────────┐
  │          Dim_Plant           ││  Dim_Balancing_Authority     │
  ├──────────────────────────────┤├──────────────────────────────┤
  │ PK  Plant_Key (Surrogate)    ││ PK  BA_Key (Surrogate)       │
  │     ORISPL_Code (Nat. Key)   ││     BA_Code (PJM, CISO, etc.)│
  │     Plant_Name               ││     BA_Name                  │
  │     Latitude / Longitude     ││     NERC_Region              │
  │     County / State           │└──────────────────────────────┘
  │     EPA_Region               │
  │     Balancing_Authority_Code │
  └──────────────┬───────────────┘
                 │ 1:M
                 ▼
  ┌──────────────────────────────┐
  │     Dim_Generator (SCD 2)    │
  ├──────────────────────────────┤
  │ PK  Generator_Key (Surrogate)│
  │     ORISPL_Code              │
  │     Generator_ID             │
  │     Prime_Mover_Code         │
  │     Nameplate_Capacity_MW    │
  │     Operating_Status         │  <-- SCD 2 Monitored: OP, SB, RE
  │     Row_Effective_Date       │
  │     Row_Expiration_Date      │
  │     Is_Current (Boolean)     │
  └──────────────────────────────┘
```

---

## 5. Mathematical Algorithms & Physical Validation Rules

### 5.1 Technology-Specific Heat Rate Validation Bounds
Heat rate measures thermal efficiency:
$$\text{Heat Rate } (\text{Btu}/\text{kWh}) = \frac{\text{Fuel Consumed } (\text{Btu})}{\text{Net Generation } (\text{kWh})} = \frac{\text{Total Fuel MMBtu} \times 10^6}{\text{Net Generation MWh} \times 10^3} = \frac{\text{MMBtu} \times 1,000}{\text{Net MWh}}$$

Rather than applying a universal Carnot limit, the Data Quality Engine applies **technology-specific physical thresholds**:

```sql
-- PostgreSQL Data Quality Validation Logic
CASE 
    -- Combined Cycle Gas Turbine (CCGT): High efficiency (55% - 63%)
    WHEN prime_mover_code IN ('CA', 'CT', 'CS', 'CC') AND (heat_rate < 5000 OR heat_rate > 14000)
        THEN 'REJECT_CCGT_HEAT_RATE_OUT_OF_BOUNDS'
        
    -- Coal-Fired Steam Turbines (ST): Moderate efficiency (30% - 38%)
    WHEN prime_mover_code = 'ST' AND energy_source_1 IN ('BIT', 'SUB', 'LIG') AND (heat_rate < 8500 OR heat_rate > 18000)
        THEN 'REJECT_COAL_HEAT_RATE_OUT_OF_BOUNDS'
        
    -- Simple Cycle Gas Turbines (Peakers): Lower efficiency (25% - 35%)
    WHEN prime_mover_code = 'GT' AND (heat_rate < 9000 OR heat_rate > 22000)
        THEN 'REJECT_PEAKER_HEAT_RATE_OUT_OF_BOUNDS'
        
    ELSE 'VALID'
END AS dq_heat_rate_flag
```
Violations are routed into `quarantine.rejected_records` with the corresponding reason, input batch ID, and timestamp.

### 5.2 Physical Conservation Reconciliation Rule
$$\text{Net Generation (EIA-923 MWh)} \le \text{Gross Generation (EPA CAMPD MWh)}$$
The pipeline calculates a monthly plant-level reconciliation check:
$$\text{Auxiliary Load Ratio} = 1 - \frac{\text{Net Generation (MWh)}}{\text{Gross Generation (MWh)}}$$
* Typical expected range: $3\%\text{ to }10\%$ for gas; $6\%\text{ to }14\%$ for coal (due to running flue-gas desulfurization scrubbers).
* If $\text{Net} > \text{Gross}$ by more than $2\%$ without a Combined Heat & Power (CHP) steam credit, the plant is flagged in the audit mart as a cross-source reporting discrepancy.

### 5.3 Spatial Nearest-Neighbor Weather Imputation
Power plants do not have dedicated weather stations. Spatial joins use the **Haversine Great-Circle Formula**:
$$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
* For each plant $(\phi_{\text{plant}}, \lambda_{\text{plant}})$, select the nearest NOAA ISD station within a maximum radius of **50 km**.
* Link plant hourly operations to weather using an **ASOF temporal join** (closest weather record within $\pm 60$ minutes).
* Preserve lineage metadata: `nearest_station_id`, `station_distance_km`, and `time_difference_minutes`.

---

## 6. Required Repository Structure & File Deliverables

The repository structure matches the exact guidelines from `DWBI Final Project Overview.pdf` and course rubrics:

```
DWBI-Final-Project/
├── .agents                           # Binding AI Agent operational directives & file scan rules
├── .gitignore                        # Git exclusion specifications
├── README.md                         # Master repository guide, architecture tracks & team roles
├── PROJECT_BLUEPRINT.md              # THIS DOCUMENT (Canonical Kimball DW Specification)
├── DATABRICKS_SERVERLESS_ARCHITECTURE.md # Modern Cloud Lakehouse Specification
│
├── 01_Project_Documentation/
│   ├── Requirements.pdf              # Official course submission: Problem statement & scope
│   ├── Schema.pdf                    # Official course submission: Visual Star Schema diagram
│   ├── Data_Dictionary.xlsx          # Official course submission: Complete 7-tab data catalog
│   ├── Architecture.pdf / .png       # High-resolution pipeline architecture diagram
│   ├── Schema.jpg / .png             # High-resolution Star Schema raster diagrams
│   ├── schema_diagram_mermaid.md     # Verified Mermaid code for Draw.io diagram rendering
│   ├── Requirements.md               # Markdown summary linking to Phase 1 documents
│   ├── README.md                     # Documentation folder index and guidelines
│   ├── course_requirements/          # ⚠️ MANDATORY: University syllabus, rubrics, architecture
│   ├── research/                     # ⛔ ARCHIVED: Exploratory notes (DO NOT PARSE)
│   └── Team_Guides/                  # ⛔ HUMAN ONBOARDING: Word .docx guides (DO NOT PARSE)
│
├── Phase_1_Submission/               # Complete formal academic Phase 1 package
│   ├── Phase_1_Project_Proposal_and_Design_Document.md
│   ├── Phase_1_Architecture_and_Schema_Specification.md
│   ├── Phase_1_Data_Dictionary.md
│   ├── Phase_1_Project_Execution_Plan.md
│   ├── Phase_1_Executive_Summary_and_Checklist.md
│   ├── Data_Dictionary.xlsx
│   ├── Requirements.pdf
│   ├── Schema.pdf
│   ├── Architecture.pdf
│   ├── Architecture_Pipeline_Diagram.png
│   └── Schema_Diagram.jpg
│
├── 02_Data/
│   ├── raw_data/                     # Sample raw downloads (EIA-860/923, EPA CAMPD, NOAA)
│   └── cleaned_data/                 # Sample cleaned CSV outputs from Silver processing
│
├── 03_ETL/
│   ├── staging.sql                   # DDL creating staging (project_staging) & quarantine tables
│   └── quality_checks.sql            # DQ rules routing invalid records to quarantine
│
├── 04_Data_Warehouse/
│   └── warehouse.sql                 # Production DDL for Star Schema (project_dw Tables, PKs, FKs)
│
├── 05_Analytics/
│   ├── OLAP.sql                      # Multi-dimensional aggregations (ROLLUP, CUBE)
│   └── Views.sql                     # Gold Layer Materialized Views (project_reporting)
│
├── 06_Dashboard/
│   ├── README.md                     # 3-Page Power BI specification & connection guide
│   └── PowerBI.pbix                  # Interactive Power BI report connected to PostgreSQL / Databricks
│
└── scripts/
    ├── build_team_docs.py            # Generator script for Team Onboarding Word guides
    └── archive/                      # Historical/scratch utility scripts
```

---

## 7. PostgreSQL DDL Reference Specification

### 7.1 Staging & Quarantine Layer
```sql
CREATE SCHEMA IF NOT EXISTS project_staging;
CREATE SCHEMA IF NOT EXISTS quarantine;
CREATE SCHEMA IF NOT EXISTS project_dw;
CREATE SCHEMA IF NOT EXISTS project_reporting;

-- Dead-Letter Quarantine Table
CREATE TABLE quarantine.rejected_records (
    rejection_id         BIGSERIAL PRIMARY KEY,
    source_system        VARCHAR(50) NOT NULL,
    source_table         VARCHAR(100) NOT NULL,
    source_row_identifier VARCHAR(100),
    rejection_reason     VARCHAR(255) NOT NULL,
    raw_payload_json     JSONB NOT NULL,
    batch_id             UUID NOT NULL,
    rejected_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ETL Pipeline Audit Log
CREATE TABLE project_staging.etl_run_log (
    run_id               BIGSERIAL PRIMARY KEY,
    batch_id             UUID NOT NULL,
    pipeline_step        VARCHAR(100) NOT NULL,
    source_system        VARCHAR(50) NOT NULL,
    records_read         INTEGER DEFAULT 0,
    records_inserted     INTEGER DEFAULT 0,
    records_updated      INTEGER DEFAULT 0,
    records_rejected     INTEGER DEFAULT 0,
    execution_status     VARCHAR(30) NOT NULL,
    start_time           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time             TIMESTAMP WITH TIME ZONE,
    error_message        TEXT
);
```

### 7.2 Conformed Dimensions (with SCD Type 2)
```sql
-- Dim_Date
CREATE TABLE project_dw.dim_date (
    date_key             INTEGER PRIMARY KEY, -- YYYYMMDD
    calendar_date        DATE NOT NULL UNIQUE,
    calendar_year        SMALLINT NOT NULL,
    calendar_quarter     SMALLINT NOT NULL,
    calendar_month       SMALLINT NOT NULL,
    month_name           VARCHAR(15) NOT NULL,
    day_of_month         SMALLINT NOT NULL,
    day_of_week          SMALLINT NOT NULL,
    day_name             VARCHAR(15) NOT NULL,
    is_weekend           BOOLEAN NOT NULL
);

-- Dim_Plant
CREATE TABLE project_dw.dim_plant (
    plant_key            SERIAL PRIMARY KEY,
    orispl_code          INTEGER NOT NULL UNIQUE,
    plant_name           VARCHAR(150) NOT NULL,
    utility_id           INTEGER,
    utility_name         VARCHAR(150),
    latitude             NUMERIC(9, 6),
    longitude            NUMERIC(9, 6),
    state_code           CHAR(2) NOT NULL,
    county_name          VARCHAR(100),
    balancing_auth_code  VARCHAR(20),
    epa_region           SMALLINT,
    is_combined_heat_power BOOLEAN DEFAULT FALSE,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dim_Generator (SCD Type 2)
CREATE TABLE project_dw.dim_generator (
    generator_key        SERIAL PRIMARY KEY,
    orispl_code          INTEGER NOT NULL,
    generator_id         VARCHAR(20) NOT NULL,
    prime_mover_code     VARCHAR(10) NOT NULL,
    primary_energy_source VARCHAR(10) NOT NULL,
    nameplate_capacity_mw NUMERIC(10, 2),
    operating_status     VARCHAR(30) NOT NULL, -- OP, SB, OA, RE
    row_effective_date   DATE NOT NULL,
    row_expiration_date  DATE NOT NULL DEFAULT '9999-12-31',
    is_current           BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (orispl_code) REFERENCES project_dw.dim_plant(orispl_code)
);
CREATE INDEX idx_dim_gen_lookup ON project_dw.dim_generator(orispl_code, generator_id, is_current);
```

### 7.3 Fact Tables (Transactional, Periodic Snapshot & Grid Aggregate)
```sql
-- Transactional Fact: Hourly Smokestack Emissions & Weather (Partitioned by Month)
CREATE TABLE project_dw.fact_hourly_emissions_weather (
    date_key             INTEGER NOT NULL,
    hour_of_day          SMALLINT NOT NULL,
    plant_key            INTEGER NOT NULL,
    unit_id              VARCHAR(20) NOT NULL,
    station_id           VARCHAR(20),
    gross_load_mw        NUMERIC(10, 2),
    heat_input_mmbtu     NUMERIC(12, 3),
    so2_mass_lbs         NUMERIC(12, 3),
    nox_mass_lbs         NUMERIC(12, 3),
    co2_mass_tons        NUMERIC(12, 3),
    ambient_temp_celsius NUMERIC(5, 2),
    wind_speed_mps       NUMERIC(5, 2),
    weather_distance_km  NUMERIC(6, 2),
    PRIMARY KEY (date_key, hour_of_day, plant_key, unit_id)
) PARTITION BY RANGE (date_key);

-- Periodic Snapshot Fact: Monthly Plant Fuel Consumption & Net Generation
CREATE TABLE project_dw.fact_monthly_plant_operations (
    snapshot_key         SERIAL PRIMARY KEY,
    month_start_date_key INTEGER NOT NULL,
    plant_key            INTEGER NOT NULL,
    prime_mover_code     VARCHAR(10) NOT NULL,
    energy_source_code   VARCHAR(10) NOT NULL,
    net_generation_mwh   NUMERIC(14, 3) NOT NULL, -- Can be negative during station outages
    fuel_consumed_physical NUMERIC(14, 3),
    fuel_consumed_mmbtu  NUMERIC(14, 3),
    avg_heat_rate_btu_kwh NUMERIC(10, 2),
    delivered_fuel_cost_per_mmbtu NUMERIC(8, 2),
    ending_fuel_stock_physical NUMERIC(14, 3),
    FOREIGN KEY (plant_key) REFERENCES project_dw.dim_plant(plant_key)
);

-- Aggregate Grid Fact: Hourly Balancing Authority Telemetry
CREATE TABLE project_dw.fact_regional_grid_demand (
    date_key             INTEGER NOT NULL,
    hour_of_day          SMALLINT NOT NULL,
    balancing_auth_code  VARCHAR(20) NOT NULL,
    demand_mw            NUMERIC(12, 2),
    demand_forecast_mw   NUMERIC(12, 2),
    net_gen_coal_mw      NUMERIC(12, 2),
    net_gen_gas_mw       NUMERIC(12, 2),
    net_gen_nuclear_mw   NUMERIC(12, 2),
    net_gen_hydro_mw     NUMERIC(12, 2),
    net_gen_wind_mw      NUMERIC(12, 2),
    net_gen_solar_mw     NUMERIC(12, 2),
    net_interchange_mw   NUMERIC(12, 2),
    PRIMARY KEY (date_key, hour_of_day, balancing_auth_code)
);
```

---

## 8. Analytical SQL & OLAP Queries Specification

### 8.1 Multi-Dimensional OLAP Cube
```sql
-- OLAP.sql: Aggregating Monthly Generation by Geography and Fuel Source
SELECT 
    d.calendar_year,
    p.state_code,
    f.energy_source_code,
    SUM(f.net_generation_mwh) AS total_net_mwh,
    ROUND(AVG(f.avg_heat_rate_btu_kwh), 2) AS weighted_heat_rate
FROM project_dw.fact_monthly_plant_operations f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
JOIN project_dw.dim_date d ON f.month_start_date_key = d.date_key
GROUP BY CUBE (d.calendar_year, p.state_code, f.energy_source_code)
ORDER BY d.calendar_year, p.state_code, f.energy_source_code;
```

### 8.2 Moving Window Function (Emissions vs. Temperature Sensitivity)
```sql
-- Views.sql: 7-Day Moving Average Heat Rate & Peak Temperature Impact
SELECT 
    f.plant_key,
    p.plant_name,
    f.date_key,
    AVG(f.ambient_temp_celsius) AS daily_avg_temp_c,
    SUM(f.gross_load_mw) AS daily_gross_mw,
    SUM(f.co2_mass_tons) AS daily_co2_tons,
    -- 7-Day Moving Average CO2 Intensity (Tons CO2 per Gross MW)
    AVG(SUM(f.co2_mass_tons) / NULLIF(SUM(f.gross_load_mw), 0)) OVER (
        PARTITION BY f.plant_key 
        ORDER BY f.date_key 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_7day_co2_intensity
FROM project_dw.fact_hourly_emissions_weather f
JOIN project_dw.dim_plant p ON f.plant_key = p.plant_key
GROUP BY f.plant_key, p.plant_name, f.date_key;
```

---

## 9. Future Session Initialization Protocol

Whenever a new AI session or development sprint begins, execute the following startup sequence:

1. **Verify Local Environment:**
   * Run `python --version` (requires Python 3.10+; current system has Python 3.14).
   * Confirm PostgreSQL service is active on `localhost:5432`.
2. **Review Binding Directives & Ground Truths:**
   * Read [`.agents`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/.agents) for strict file access and execution directives.
   * Read [`01_Project_Documentation/course_requirements/`](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/01_Project_Documentation/course_requirements/) for university grading rubrics and schema mandates.
   * Reference [PROJECT_BLUEPRINT.md](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/PROJECT_BLUEPRINT.md) as the ground truth for local Kimball PostgreSQL implementation.
   * Reference [DATABRICKS_SERVERLESS_ARCHITECTURE.md](file:///d:/Semester%20Projects/DWBI%20LAB%20Project/DATABRICKS_SERVERLESS_ARCHITECTURE.md) for the cloud lakehouse implementation.
   * Maintain the required folder layout matching Section 6.
3. **Do Not Hallucinate Simplifications:**
   * Never read `01_Project_Documentation/research/` or `01_Project_Documentation/Team_Guides/`.
   * Always account for shifting Excel header rows (Row 2 in EIA-860, Row 6 in EIA-923).
   * Use **NOAA ISD (Hourly)** for hourly joins; never treat GHCN-Daily as hourly.
   * Keep EIA-930 at the **Balancing Authority** grain; do not force it down to individual plants.
   * Use **technology-specific heat rate bounds** (5,000–14,000 for CCGT; 8,500–18,000 for Coal).
   * Allow negative net generation for plants reporting station service load during maintenance.

