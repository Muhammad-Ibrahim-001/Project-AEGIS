# Column Removal Map — Silver → Gold Transformation
**Project:** U.S. Bulk Power Generation, Emissions & Weather Lakehouse  
**System Architecture:** Databricks Serverless Cloud Lakehouse (`dwbi_catalog`)  
**Pipeline Contract:** Bronze tables retain **100% of raw columns** (immutable, append-only raw landing). The column removals documented here occur strictly during the **Silver → Gold projection** step (using explicit `SELECT` statements rather than `SELECT *`).

---

## 1. Executive Summary & Count Conventions

Raw federal energy datasets contain extensive administrative registration numbers, legal filing dockets, pipeline logistics, engineering design classifications, and pre-aggregated totals. Ingesting these extraneous fields into the Gold Dimensional Layer bloats storage, degrades Parquet/Photon vectorization, and risks aggregation double-counting.

### Understanding the Counts
* **Physical Raw Columns:** The exact number of individual fields/columns present in the source files (e.g., Form EIA-923 contains 97 physical columns, of which 72 represent a 12-month series across 6 metrics).
* **Logical Concept Groups:** The high-level business categories (e.g., treating `Netgen January` through `Netgen December` as 1 logical measure group).
* **Total Physical Pruning:** Across all 10 federal datasets, **247 out of 343 physical columns (72.0%) are excluded from the Gold Dimensional Layer** (235 permanently pruned + 12 preserved exclusively in Silver-layer bridge and data quality verification tables).

---

## 2. Categorization Legend

Every pruned attribute is classified using standard color-coded tags:

```
🟥 RED    = Redundant — Attribute already exists in a parent dimension or can be dynamically joined
🟨 YELLOW = Administrative / Regulatory — Legal docket numbers, regulatory status, or constant tags
🟦 BLUE   = Future-Planned / Speculative — Forecasted capacity modifications (scope = 2021–2024 actuals)
🟩 GREEN  = Computed in Gold / Intermediate — Intermediate steps or pre-aggregations derived in Gold marts
🟪 PURPLE = Sub-Technology Flags — Engineering sub-classifications not modeled in the Star Schema
🟧 ORANGE = Outside Scope — Logistics, gas pipelines, coal ash ponds, cooling water, or aviation metrics
⬛ GREY   = API / System Metadata — Web URIs, envelope types, METAR text, or UI icon hyperlinks
```

---

## 3. Master Column Projection Reference Matrix

This quick-lookup table shows how each raw source maps through the Lakehouse tiers into `dwbi_catalog.gold_warehouse`:

| Source System | Raw Physical Cols | Kept in Gold Layer | Silver-Only DQ / Bridge | Physical Cols Removed | Pruning Ratio | Target Gold Entity |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **EIA-860 Sched 2 (Plant Master)** | 42 | 11 | — | 31 | 73.8% | `dim_plant` |
| **EIA-860 Sched 3 (Generator Inventory)** | 73 | 8 | — | 65 | 89.0% | `dim_generator` (SCD Type 2) |
| **EIA-860 Sched 6_1 (Enviro Assoc)** | 7 | 0 (Bridge only) | 3 | 4 | 57.1% | `silver_conformed.boiler_generator_bridge` |
| **EIA-860M (Monthly Updates)** | 6 | 4 (SCD-2 Events) | — | 2 | 33.3% | `dim_generator` (SCD Type 2) |
| **EIA-923 Page 1 (Gen & Fuel)** | 97 | 40 (Unpivoted) | — | 57 | 58.8% | `fact_monthly_plant_operations` |
| **EIA-930 (Grid Telemetry)** | 15 | 14 | — | 1 | 6.7% | `dim_balancing_authority` / `fact_regional_grid_demand` |
| **EPA CAMPD (Hourly CEMS)** | 33 | 9 | 1 (`opTime`) | 23 | 72.7% | `fact_hourly_emissions_weather` |
| **EPA–EIA Crosswalk** | 33 | 0 (Bridge only) | 7 | 26 | 78.8% | `silver_conformed.boiler_generator_bridge` |
| **NOAA ISD Station History** | 11 | 6 (from 7 raw) | 1 (`ICAO`) | 3 | 36.4% | `dim_weather_station` |
| **NOAA ISD Weather Observations** | 26 | 4 | — | 22 | 84.6% | `fact_hourly_emissions_weather` |
| **TOTALS** | **343** | **96** | **12** | **235** | **72.0% Net Drop** | *(247 out of 343 raw columns excluded from Gold)* |

---

## 4. Source-by-Source Column Removal Analysis

---

### Source 1 — EIA-860 Schedule 2 (Plant Master)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia860_plant`
* **Destination Entity:** `gold_warehouse.dim_plant`
* **Column Breakdown:** 42 Total $\longrightarrow$ **11 Kept**, **31 Removed** (73.8% Pruning)

```mermaid
flowchart TD
    SRC["📄 EIA-860 Schedule 2\nPlant Master (42 cols)"]

    subgraph KEEP["✅ KEPT — Map to dim_plant (11 cols)"]
        K1["Plant Code → orispl_code (Natural Key)"]
        K2["Plant Name → plant_name"]
        K3["Utility ID → utility_id"]
        K4["Utility Name → utility_name"]
        K5["Latitude → latitude (WGS 84)"]
        K6["Longitude → longitude (WGS 84)"]
        K7["State → state_code"]
        K8["County → county_name"]
        K9["Balancing Authority Code → ba_code"]
        K10["NERC Region → dim_balancing_authority.region"]
        K11["FERC Cogen Flag → is_combined_heat_power"]
    end

    subgraph ADM["🟨 Administrative / Regulatory (9 cols)"]
        A1["FERC Cogeneration Docket Number\nLegal docket string with zero analytical value"]
        A2["FERC Small Power Producer Status & Docket Number (2 cols)\nAdministrative PURPA exemption tags"]
        A3["FERC Exempt Wholesale Generator Status & Docket Number (2 cols)\nPUHCA legal registration filings"]
        A4["Primary Purpose (NAICS Code)\nConstant value (22 - Utilities) across target fleet"]
        A5["Regulatory Status (RE/NR)\nCost-of-service utility vs merchant producer tag"]
        A6["Sector & Sector Name (2 cols)\nHigh-level industry categorization uniform across plants"]
    end

    subgraph RED["🟥 Redundant / Normalized into dim_ba or Postal (4 cols)"]
        R1["Street Address\nPhysical entrance gate address; spatial joins use Lat/Lon"]
        R2["City\nRedundant; State + County covers geographical rollups"]
        R3["Zip\nPostal routing code; irrelevant to bulk transmission"]
        R4["Balancing Authority Name\nRedundant; conformed in dim_balancing_authority.ba_name via ba_code"]
    end

    subgraph SCOP["🟧 Outside Project Scope (18 cols)"]
        S1["Name of Water Source\nCooling water hydrology; not modeled in Gold facts"]
        S2["Ash Impoundment? / Lined? / Status (3 cols)\nSolid coal ash waste; outside atmospheric/power scope"]
        S3["Transmission System Owner / Owner ID / Owner State (3 cols)\nLocal wire owners; grid modeled at Balancing Authority grain"]
        S4["Grid Voltage kV 1, 2, 3 (3 cols)\nSubstation electrical engineering specifications"]
        S5["Energy Storage\nCollocated battery flag; batteries tracked as distinct units"]
        S6["Natural Gas LDC Name / Pipeline 1, 2, 3 / Pipeline Notes (5 cols)\nUpstream gas supply contracts and free-form text notes"]
        S7["Natural Gas Storage & LNG Storage (2 cols)\nOn-site fuel storage vessels; fuel burn tracked in EIA-923"]
    end

    SRC --> KEEP
    SRC --> ADM
    SRC --> RED
    SRC --> SCOP
```

---

### Source 2 — EIA-860 Schedule 3 (Generator Inventory)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia860_generator`
* **Destination Entity:** `gold_warehouse.dim_generator`
* **Column Breakdown:** 73 Total $\longrightarrow$ **8 Kept**, **65 Removed** (89.0% Pruning)

```mermaid
flowchart TD
    SRC["📄 EIA-860 Schedule 3\nGenerator Inventory (73 cols)"]

    subgraph KEEP["✅ KEPT — Map to dim_generator (8 cols)"]
        K1["Plant Code → orispl_code (FK)"]
        K2["Generator ID → generator_id (Natural Key)"]
        K3["Prime Mover → prime_mover_code (ST, GT, CC, etc.)"]
        K4["Energy Source 1 → primary_energy_source (BIT, NG, etc.)"]
        K5["Nameplate Capacity MW → nameplate_capacity_mw"]
        K6["Status → operating_status (OP, SB, RE - SCD Type 2)"]
        K7["Operating Year → operating_year"]
        K8["Planned Retirement Year → planned_retirement_year"]
    end

    subgraph RED["🟥 Redundant — Already in dim_plant (5 cols)"]
        R1["Utility ID & Utility Name\nAlready stored in parent dim_plant"]
        R2["Plant Name, State, County\nStored in dim_plant; violates 3NF to duplicate at unit grain"]
    end

    subgraph ADM["🟨 Administrative / Operational Design (9 cols)"]
        A1["Ownership (S/J/W)\nJoint-venture corporate ownership equity shares"]
        A2["Sector & Sector Name (2 cols)\nConstant utility sector classifications"]
        A3["Synchronized to Transmission Grid\nAll operational units in scope are grid-synchronized"]
        A4["RTO-ISO LMP Node & FERC Designation (2 cols)\nWholesale nodal pricing nodes; outside physical dispatch scope"]
        A5["Topping or Bottoming\nCHP thermodynamic steam cycle arrangement"]
        A6["Unit Code\nCombined-cycle grouping; resolved via Silver bridge"]
        A7["CHP System Association\nFacility-level flag already tracked in dim_plant.is_combined_heat_power"]
    end

    subgraph FUTPL["🟦 Future-Planned Values (17 physical cols)"]
        F1["Planned Retirement Month\nYear is sufficient for fleet planning"]
        F2["Planned Net Summer/Winter Uprates & Derates (4 cols)\nSpeculative future modifications (Scope = 2021-2024 actuals)"]
        F3["Planned Uprate / Derate Month & Year (4 cols)\nSpeculative modification dates"]
        F4["Planned New Prime Mover, Fuel, Capacity, Repower Dates (5 cols)\nSpeculative repowering engineering plans"]
        F5["Other Planned Modifications?, Month, Year (3 cols)\nUncommitted future maintenance overhauls"]
    end

    subgraph CAPAC["🟧 Secondary Capacity Ratings (7 physical cols)"]
        C1["Summer Capacity MW & Winter Capacity MW (2 cols)\nSeasonal deratings; standard capacity stored in nameplate_capacity_mw"]
        C2["Minimum Load MW\nLowest turndown setpoint; not modeled in Star Schema"]
        C3["Nameplate Power Factor\nApparent reactive power ratio (MW vs MVA)"]
        C4["Uprate or Derate Completed Flag, Month, Year (3 cols)\nHistorical modifications captured dynamically via SCD Type 2"]
    end

    subgraph TECH["🟪 Engineering Sub-Classifications (15 physical cols)"]
        T1["Technology Text Description\nprime_mover_code and primary_energy_source capture classification"]
        T2["Fluidized Bed, Pulverized Coal, Stoker, Other Combustion (4 cols)\nBoiler combustion designs; prime_mover_code (ST) captures type"]
        T3["Subcritical, Supercritical, Ultrasupercritical (3 cols)\nSteam pressure metallurgy; heat rate efficiency measures this directly"]
        T4["Solid Fuel Gasification (IGCC) & Carbon Capture (CCS) (2 cols)\nNiche technologies; CEMS measures actual emissions directly"]
        T5["Duct Burners & HRSG Bypass Damper (2 cols)\nSupplemental firing flags; fuel input measured directly in facts"]
        T6["Turbines or Hydrokinetic Buoys\nEquipment count; project models generation output (MWh)"]
        T7["Time from Cold Shutdown to Full Load\nStartup category; hourly load curves show ramp rates"]
        T8["Operating Month\nCommissioning year provides sufficient temporal grain"]
    end

    subgraph FUELS["🟧 Secondary & Startup Fuels (12 physical cols)"]
        FL1["Energy Source 2 through 6 (5 cols)\nSecondary fuel codes; primary fuel captures baseline technology"]
        FL2["Startup Source 1 through 4 (4 cols)\nBoiler ignition fuels; energy accounted in total MMBtu"]
        FL3["Multiple Fuels?, Cofire Fuels?, Switch Oil/Gas? (3 cols)\nCapability flags; actual fuel burn captured in EIA-923"]
    end

    SRC --> KEEP
    SRC --> RED
    SRC --> ADM
    SRC --> FUTPL
    SRC --> CAPAC
    SRC --> TECH
    SRC --> FUELS
```

---

### Source 3 — EIA-860 Schedule 6_1 (Environmental Associations)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia860_enviro_assoc`
* **Destination Entity:** `silver_conformed.boiler_generator_bridge` (Silver-layer bridge only; **not** stored in Gold)
* **Column Breakdown:** 7 Total $\longrightarrow$ **3 Kept in Silver Bridge**, **4 Removed** (57.1% Pruning)

```mermaid
flowchart LR
    SRC["📄 EIA-860 Sched 6_1\nEnviroAssoc (7 cols)"]

    subgraph KEEP["✅ KEPT — Silver Bridge Keys (3 cols)"]
        K1["Plant Code — facility join key"]
        K2["Boiler ID — combustion boiler key"]
        K3["Generator ID — electrical rotor key"]
    end

    subgraph RED["🟥 Redundant — Already in dim_plant (3 cols)"]
        R1["Utility ID\nStored in dim_plant.utility_id"]
        R2["Utility Name\nStored in dim_plant.utility_name"]
        R3["Plant Name\nStored in dim_plant.plant_name"]
    end

    subgraph OOS["🟧 Outside Gold Scope (1 col)"]
        O1["Steam Plant Type\nBoiler-turbine piping loop code\nOnce the Silver bridge resolves pairings,\nthis classification is unused"]
    end

    SRC --> KEEP
    SRC --> RED
    SRC --> OOS
```

---

### Source 4 — EIA-860M (Monthly Electric Generator Report)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia860m_monthly_updates`
* **Destination Entity:** Triggers SCD Type 2 events on `gold_warehouse.dim_generator`
* **Column Breakdown:** 6 Total $\longrightarrow$ **4 Kept**, **2 Removed** (33.3% Pruning)

```mermaid
flowchart LR
    SRC["📄 EIA-860M\nMonthly Updates (6 cols)"]

    subgraph KEEP["✅ KEPT — SCD Type 2 Engine (4 cols)"]
        K1["Plant Code — natural key link"]
        K2["Generator ID — natural key link"]
        K3["Operating Status Code — triggers SCD-2 row transition"]
        K4["Effective Date — assigns valid_from and valid_to"]
    end

    subgraph NOMAP["🟧 No Gold DDL Mapping (2 cols)"]
        N1["Net Summer Capacity MW\nNameplate capacity is established from annual EIA-860;\nmonthly seasonal ratings are not versioned"]
        N2["Energy Source 1\nFuel corrections are handled via Type 1 overwrite;\nnot tracked via SCD Type 2 lifecycle"]
    end

    SRC --> KEEP
    SRC --> NOMAP
```

---

### Source 5 — EIA-923 Schedule Page 1 (Generation & Fuel Data)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia923_monthly_generation`
* **Destination Entity:** `gold_warehouse.fact_monthly_plant_operations`
* **Column Breakdown:** 97 Total $\longrightarrow$ **40 Processed & Unpivoted**, **57 Removed** (58.8% Pruning)
  * *Note:* Unpivoting 36 monthly columns collapses the 12-month series into standard monthly rows in Gold.

```mermaid
flowchart TD
    SRC["📄 EIA-923 Page 1\nGeneration & Fuel (97 cols)"]

    subgraph KEEP["✅ KEPT — Unpivoted into fact_monthly (40 physical cols)"]
        K1["Plant Id → plant_key lookup"]
        K2["Reported Prime Mover → prime_mover_code"]
        K3["Reported Fuel Type Code → energy_source_code"]
        K4["YEAR → month_start_date_key join"]
        K5["Elec_Quantity Jan–Dec (12 cols) → fuel_consumed_physical"]
        K6["Elec_MMBtu Jan–Dec (12 cols) → fuel_consumed_mmbtu"]
        K7["Netgen Jan–Dec (12 cols) → net_generation_mwh"]
    end

    subgraph RED["🟥 Redundant — Already in dim_plant (6 cols)"]
        R1["Plant Name, Plant State\nStored in dim_plant"]
        R2["Operator Name, Operator Id\nStored in dim_plant.utility_name / utility_id"]
        R3["Census Region & NERC Region\nDerived from plant state and dim_balancing_authority"]
    end

    subgraph ADM["🟨 Administrative / Categorical (10 cols)"]
        A1["Combined Heat And Power Plant\nStored once at facility level in dim_plant.is_combined_heat_power"]
        A2["Nuclear Unit Id\nHolds sentinel dots for 99% of plants; nuclear identified by prime mover"]
        A3["Reserved\nFederal administrative placeholder column; completely empty"]
        A4["NAICS Code, Sector Number, Sector Name (3 cols)\nConstant industry classifications"]
        A5["MER Fuel Type Code\nAggregated fuel category; fact uses precise Reported Fuel Type Code"]
        A6["Balancing Authority Code\nPlant is mapped to BA through dim_plant.ba_code"]
        A7["Respondent Frequency (M/A)\nSurvey administrative metadata"]
        A8["Physical Unit Label (tons/mcf/bbls)\nImplicit from conformed fuel code; redundant in every row"]
    end

    subgraph INTERMED["🟩 Intermediate / Duplicate Energy Metrics (41 physical cols)"]
        I1["Quantity Jan–Dec (12 cols)\nTotal physical fuel including non-electric thermal; project uses Elec_Quantity"]
        I2["MMBtuPer_Unit Jan–Dec (12 cols)\nHigher heating value factor; mathematically redundant with Quantity * Heat"]
        I3["Tot_MMBtu Jan–Dec (12 cols)\nTotal heat content including CHP steam; project uses Elec_MMBtu"]
        I4["Annual Summary Totals (5 cols)\nTotal Fuel Qty, Elec Fuel Qty, Total MMBtu, Elec MMBtu, Netgen MWh;\nSumming pre-aggregated annual totals with monthly rows causes double-counting"]
    end

    SRC --> KEEP
    SRC --> RED
    SRC --> ADM
    SRC --> INTERMED
```

---

### Source 6 — EIA-930 (Hourly Electric Grid Telemetry)
* **Ingestion Target:** Bronze table `bronze_staging.raw_eia930_hourly_balance`
* **Destination Entities:** `gold_warehouse.dim_balancing_authority` & `gold_warehouse.fact_regional_grid_demand`
* **Column Breakdown:** 15 Total $\longrightarrow$ **14 Kept**, **1 Removed** (6.7% Pruning)

```mermaid
flowchart LR
    SRC["📄 EIA-930\nGrid Telemetry (15 cols)"]

    subgraph KEEP["✅ KEPT — Maps to BA Dim & Grid Fact (14 cols)"]
        K1["ba_code → dim_balancing_authority.ba_code (PK)"]
        K2["ba_name → ba_name"]
        K3["interconnect → region (Eastern, Western, Texas)"]
        K4["timestamp_utc → date_key + hour_of_day (0-23)"]
        K5["demand_mw → demand_mw"]
        K6["demand_forecast_mw → demand_forecast_mw"]
        K7["net_interchange_mw → net_interchange_mw (Import/Export)"]
        K8["6 Fuel Dispatches (6 cols)\ngen_coal, gen_natgas, gen_nuclear, gen_hydro, gen_solar, gen_wind"]
        K9["net_generation_mw → total generation audit check"]
    end

    subgraph REM["🟥 Redundant (1 col)"]
        R1["local_time\nLocal clock string with seasonal Daylight Saving Time shifts\nLakehouse conforms strictly to UTC timestamps to prevent\nmissing/duplicate hour anomalies during clock changes"]
    end

    SRC --> KEEP
    SRC --> REM
```

---

### Source 7 — EPA CAMPD (Continuous Emission Monitoring System)
* **Ingestion Target:** Bronze table `bronze_staging.raw_epa_hourly_emissions`
* **Destination Entity:** `gold_warehouse.fact_hourly_emissions_weather`
* **Column Breakdown:** 33 Total $\longrightarrow$ **9 Kept in Gold Fact**, **1 Kept in Silver DQ**, **23 Removed** (72.7% Pruning)

```mermaid
flowchart TD
    SRC["📄 EPA CAMPD\nHourly Emissions (33 cols)"]

    subgraph KEEP["✅ KEPT — Map to fact_hourly (9 cols)"]
        K1["facilityId → plant_key lookup (ORISPL)"]
        K2["unitId → unit_id (Degenerate Dimension)"]
        K3["date → date_key (YYYYMMDD)"]
        K4["hour → hour_of_day (0-23)"]
        K5["grossLoad → gross_load_mw"]
        K6["heatInput → heat_input_mmbtu"]
        K7["so2Mass → so2_mass_lbs"]
        K8["noxMass → nox_mass_lbs"]
        K9["co2Mass → co2_mass_tons"]
    end

    subgraph SILV["🟩 Silver-Only Data Quality (1 col)"]
        S1["opTime (Operational fraction 0.00-1.00)\nUsed during Silver DQ validation to evaluate unit uptime;\nnot stored in Gold fact table"]
    end

    subgraph RED["🟥 Redundant — Already in dim_plant (3 cols)"]
        R1["stateCode & facilityName (2 cols)\nStored in dim_plant; normalizing out saves gigabytes"]
        R2["unit_id alias\nDuplicate field alias returned by EPA API"]
    end

    subgraph FLAGS["🟩 CEMS Sensor Assurance Flags (7 cols)"]
        F1["so2MassMeasureFlg, co2MassMeasureFlg, noxMassMeasureFlg (3 cols)\nSensor flags (Measured/Substitute); QA executed at Silver"]
        F2["so2RateMeasureFlg, co2RateMeasureFlg, noxRateMeasureFlg (3 cols)\nRate calculation quality flags"]
        F3["heatInputMeasureFlg\nHeat input measurement assurance flag"]
    end

    subgraph RATES["🟩 Pre-Calculated Emission Rates (3 cols)"]
        RT1["so2Rate, co2Rate, noxRate (3 cols)\nCalculated intensity (lbs/MMBtu or tons/MMBtu);\nKimball facts store base additive mass; rates are\nderived dynamically in reporting views (vw_emissions_intensity)"]
    end

    subgraph OOS["🟧 Outside Gold Scope (10 cols)"]
        O1["steamLoad (1,000 lbs/hr)\nIndustrial export steam; bulk power model tracks electricity only"]
        O2["associatedStacks\nCommon flue gas manifold duct ID; Silver bridge maps to unitId"]
        O3["primaryFuelInfo & secondaryFuelInfo (2 cols)\nFuel descriptions; conformed in dim_generator"]
        O4["unitType\nCombustion architecture text; conformed in prime_mover_code"]
        O5["so2ControlInfo, noxControlInfo, pmControlInfo, hgControlInfo (4 cols)\nAbatement equipment names (Scrubbers, SCR, Baghouse);\nactual mass emissions are measured directly"]
        O6["programCodeInfo\nFederal regulatory programs (ARP, CSNOX); administrative audit tags"]
    end

    SRC --> KEEP
    SRC --> SILV
    SRC --> RED
    SRC --> FLAGS
    SRC --> RATES
    SRC --> OOS
```

---

### Source 8 — EPA–EIA Crosswalk
* **Ingestion Target:** Bronze table `bronze_staging.raw_epa_eia_crosswalk`
* **Destination Entity:** `silver_conformed.boiler_generator_bridge` (Silver-layer bridge only; **not** stored in Gold)
* **Column Breakdown:** 33 Total $\longrightarrow$ **5 Core Bridge Keys**, **2 Audit Scores**, **26 Removed** (78.8% Pruning)

```mermaid
flowchart TD
    SRC["📄 EPA-EIA Crosswalk (33 cols)\nSilver Bridge Table"]

    subgraph KEEP["✅ KEPT — Silver Bridge Keys (7 cols)"]
        K1["CAMD_PLANT_ID — EPA plant code"]
        K2["CAMD_UNIT_ID — EPA stack/boiler code"]
        K3["EIA_PLANT_ID — EIA plant code (ORISPL)"]
        K4["EIA_GENERATOR_ID — EIA generator code"]
        K5["EIA_BOILER_ID — EIA boiler code"]
        K6["MATCH_TYPE_GEN & MATCH_TYPE_BOILER (2 cols)\nSilver linkage confidence audit metadata"]
    end

    subgraph SYN["🟨 Synthetic Row Identifier (1 col)"]
        S1["SEQUENCE_NUMBER\nPublisher row index; composite natural keys provide uniqueness"]
    end

    subgraph RED["🟥 Redundant Across Dimensions (13 cols)"]
        R1["CAMD_STATE, CAMD_FACILITY_NAME, EIA_STATE, EIA_PLANT_NAME (4 cols)\nRedundant with dim_plant"]
        R2["CAMD_NAMEPLATE_CAPACITY & EIA_NAMEPLATE_CAPACITY (2 cols)\nConformed in dim_generator.nameplate_capacity_mw"]
        R3["CAMD_FUEL_TYPE & EIA_FUEL_TYPE (2 cols)\nConformed in dim_generator.primary_energy_source"]
        R4["EIA_UNIT_TYPE\nConformed in dim_generator.prime_mover_code"]
        R5["CAMD_LAT/LON & EIA_LAT/LON (4 cols)\nAuthoritative coordinates stored in dim_plant"]
    end

    subgraph STAT["🟨 EPA Operating Lifecycle Status (5 cols)"]
        ST1["CAMD_STATUS, CAMD_STATUS_DATE, CAMD_RETIRE_YEAR (3 cols)\nEPA lifecycle tracking; generator SCD-2 status is driven by EIA-860M"]
        ST2["EIA_RETIRE_YEAR\nCaptured in dim_generator.planned_retirement_year"]
        ST3["PLANT_ID_CHANGE_FLAG\nHistorical agency ID change audit flag"]
    end

    subgraph MOD["🟥 Staging Artifacts (7 cols)"]
        M1["CAMD_GENERATOR_ID & MOD_CAMD_GENERATOR_ID (2 cols)\nEPA-assigned generator IDs; bridge joins on CAMD_UNIT_ID"]
        M2["MOD_CAMD_UNIT_ID, MOD_EIA_PLANT_ID, MOD_EIA_BOILER_ID (3 cols)\nIntermediate normalization artifacts"]
        M3["MOD_EIA_GENERATOR_ID_BOILER & MOD_EIA_GENERATOR_ID_GEN (2 cols)\nIntermediate matching script fields"]
    end

    SRC --> KEEP
    SRC --> SYN
    SRC --> RED
    SRC --> STAT
    SRC --> MOD
```

---

### Source 9 — NOAA ISD Station History (`isd-history.csv`)
* **Ingestion Target:** Bronze table `bronze_staging.raw_noaa_isd_station_history`
* **Destination Entity:** `gold_warehouse.dim_weather_station`
* **Column Breakdown:** 11 Total $\longrightarrow$ **6 Kept in Gold** (projected from 7 raw fields), **1 Kept in Silver**, **3 Removed** (36.4% Excluded from Gold)

```mermaid
flowchart LR
    SRC["📄 NOAA Station History (11 cols)"]

    subgraph KEEP["✅ KEPT — Map to dim_weather_station (6 attributes from 7 raw cols)"]
        K1["USAF + WBAN (2 raw cols) → station_id (Natural Key)"]
        K2["STATION NAME → station_name"]
        K3["STATE → state_code"]
        K4["LAT → latitude (WGS 84)"]
        K5["LON → longitude (WGS 84)"]
        K6["ELEV(M) → elevation_m"]
    end

    subgraph SILV["🟩 Silver-Only Disambiguation (1 col)"]
        S1["ICAO (4-letter airport code e.g. KMOB)\nUsed during Silver spatial matching; not in Gold DDL"]
    end

    subgraph REM["🟨 Removed (3 cols)"]
        R1["CTRY (Country Code)\nDataset filtered to US-only stations during Bronze ingest;\nconstant value ('US') provides zero analytical variance"]
        R2["BEGIN & END (2 cols)\nEarliest and latest observation dates recorded (often 1930s);\nused in Silver to confirm active status during 2021-2024"]
    end

    SRC --> KEEP
    SRC --> SILV
    SRC --> REM
```

---

### Source 10 — NOAA ISD Synoptic Weather Observations
* **Ingestion Target:** Bronze table `bronze_staging.raw_noaa_isd_weather`
* **Destination Entity:** Merged into `gold_warehouse.fact_hourly_emissions_weather`
* **Column Breakdown:** 26 Total $\longrightarrow$ **4 Kept**, **22 Removed** (84.6% Pruning)

```mermaid
flowchart TD
    SRC["📄 NOAA ISD Observations (26 cols)"]

    subgraph KEEP["✅ KEPT — Merged into fact_hourly (4 cols)"]
        K1["stationId → station_key lookup"]
        K2["timestamp → date_key + hour_of_day (UTC Temporal Match)"]
        K3["temperature → ambient_temp_celsius (Missing -9999 coerced to NULL)"]
        K4["windSpeed → wind_speed_mps (Missing -9999 coerced to NULL)"]
    end

    subgraph META["⬛ API & Envelope Metadata (5 cols)"]
        M1["@id & @type (2 cols)\nGeoJSON schema URIs ('wx:ObservationStation')"]
        M2["station & icon (2 cols)\nHTTP URL links to API endpoints and condition PNGs"]
        M3["rawMessage\nUnparsed METAR aeronautical text string; bloats columnar storage"]
    end

    subgraph RED["🟥 Redundant Across Dimensions (2 cols)"]
        R1["elevation\nStored statically in dim_weather_station.elevation_m"]
        R2["stationName\nStored statically in dim_weather_station.station_name"]
    end

    subgraph OOS["🟧 Outside Gold Schema Scope (15 cols)"]
        O1["dewpoint & relativeHumidity (2 cols)\nBorderline thermodynamic metrics; excluded from current Gold DDL"]
        O2["windDirection & windGust (2 cols)\nCompass degrees and gusts; sustained velocity (m/s) modeled"]
        O3["barometricPressure & seaLevelPressure (2 cols)\nAtmospheric pressure in Pa/hPa; temperature is primary efficiency driver"]
        O4["visibility\nAviation safety distance; unrelated to power generation"]
        O5["maxTemperature & minTemperature Last 24 Hours (2 cols)\nPre-aggregated 24-hr extremes; violates hourly transactional grain"]
        O6["precipitationLast3Hours\nLiquid accumulation; not modeled in power generation"]
        O7["windChill & heatIndex (2 cols)\nSubjective human comfort indices; machines respond to dry-bulb temperature"]
        O8["textDescription, presentWeather, cloudLayers (3 cols)\nSky cover narrative strings and sensor array payloads"]
    end

    SRC --> KEEP
    SRC --> META
    SRC --> RED
    SRC --> OOS
```

---

## 5. Implementation Guide: Executing Column Projection

### PySpark Silver-to-Gold Projection Pattern
In PySpark notebooks, apply projection using explicit `.select()` lists rather than writing out raw schemas:

```python
# Example: Silver-to-Gold Projection for dim_plant
dim_plant_df = (
    silver_plants_df
    .select(
        col("Plant Code").cast("int").alias("orispl_code"),
        col("Plant Name").alias("plant_name"),
        col("Utility ID").cast("int").alias("utility_id"),
        col("Utility Name").alias("utility_name"),
        col("Latitude").cast("decimal(9,6)").alias("latitude"),
        col("Longitude").cast("decimal(9,6)").alias("longitude"),
        col("State").alias("state_code"),
        col("County").alias("county_name"),
        col("Balancing Authority Code").alias("balancing_authority_code"),  # matches config.py (or ba_code in early DDL)
        when(col("FERC Cogeneration Status") == "Y", True).otherwise(False).alias("is_combined_heat_power")
    )
    .dropDuplicates(["orispl_code"])
)
```

### Databricks SQL Direct Projection Pattern
When loading fact tables via Databricks SQL, project explicit column lists:

```sql
INSERT INTO dwbi_catalog.gold_warehouse.fact_hourly_emissions_weather
SELECT 
    d.date_key,
    cems.hour AS hour_of_day,
    p.plant_key,
    cems.unitId AS unit_id,
    w.station_key,
    TRY_CAST(cems.grossLoad AS DECIMAL(10,2)) AS gross_load_mw,
    TRY_CAST(cems.heatInput AS DECIMAL(12,3)) AS heat_input_mmbtu,
    TRY_CAST(cems.so2Mass AS DECIMAL(12,3)) AS so2_mass_lbs,
    TRY_CAST(cems.noxMass AS DECIMAL(12,3)) AS nox_mass_lbs,
    TRY_CAST(cems.co2Mass AS DECIMAL(12,3)) AS co2_mass_tons,
    w.ambient_temp_celsius,
    w.wind_speed_mps,
    w.station_distance_km AS weather_distance_km
FROM dwbi_catalog.silver_conformed.silver_cems_emissions cems
JOIN dwbi_catalog.gold_warehouse.dim_plant p ON cems.facilityId = p.orispl_code
JOIN dwbi_catalog.gold_warehouse.dim_date d ON cems.date = d.calendar_date
LEFT JOIN dwbi_catalog.silver_conformed.silver_weather_matched w 
    ON p.orispl_code = w.orispl_code AND cems.date = w.date AND cems.hour = w.hour;
```

---

> [!TIP]
> **Summary Benefit:** Applying these projections eliminates **~80% of raw column volume**, reduces Delta Lake storage by several gigabytes, speeds up Photon vectorization, and prevents aggregation errors in Power BI DirectQuery reporting.
