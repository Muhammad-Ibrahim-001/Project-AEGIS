# Phase 1 Data Dictionary

**Project:** U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Warehouse
**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI), Fall 2026
**Institution:** FAST National University of Computer and Emerging Sciences
**Phase:** 1 (Design)
**Companion file:** `Data_Dictionary.xlsx` (the same content in spreadsheet form, one tab per object group)

---

## 1. Purpose and Conventions

This data dictionary documents every table, column, and reporting view designed for the warehouse. It is the reference for the Phase 2 DDL and ETL scripts and for the Phase 3 queries and Power BI model.

| Convention | Rule |
| :--- | :--- |
| Naming | `snake_case`; tables prefixed `raw_` (Bronze), `dim_` (dimensions), `fact_` (facts), `vw_` (reporting views) |
| Surrogate keys | Integer `SERIAL` named `<entity>_key`; the one exception is `dim_date.date_key`, a smart integer in `YYYYMMDD` form |
| Business (natural) keys | Kept alongside every surrogate key and protected by a `UNIQUE` constraint where the dimension is Type 1 |
| Missing values | Sentinels (`.`, `NM`, `*`, empty string, `-9999`) become `NULL` in typed layers; the raw row is kept in `quarantine.rejected_records` when a rule rejects it |
| Units | Conformed in Silver: energy in MWh and MMBtu, mass in lbs (SO2, NOx) and short tons (CO2), temperature in °C, wind in m/s, distance in km |
| Nullability | `NO` means the column is `NOT NULL` in the DDL; `YES` means `NULL` is allowed |

### 1.1 Schemas

| Schema | Layer | Purpose | Objects |
| :--- | :--- | :--- | :--- |
| `project_staging` | Bronze (landing) | Raw, text-typed landing tables with ingestion metadata, plus the ETL audit log | 5 `raw_*` tables, `etl_run_log` |
| `quarantine` | Data quality | Dead-letter store for rejected rows | `rejected_records` |
| `project_dw` | Dimensional warehouse | Kimball star schema | 5 dimensions, 3 fact tables |
| `project_reporting` | Gold | Business-facing views consumed by Power BI | 3 views |

The Silver layer (conformed units, boiler-to-generator crosswalk, spatial weather join, SCD Type 2 processing) is executed by the ETL scripts in `03_ETL` and writes cleaned files to `02_Data/cleaned_data` before the dimension and fact loads. It is a processing stage, not a separate schema.

---

## 2. Bronze Layer: Raw Landing Tables (`project_staging`)

Bronze tables keep every source field as `VARCHAR` so that no row is lost to a type error. Each row carries `batch_id` (UUID of the load run) and `ingested_at` (timestamp). Typing and cleaning happen in Silver.

### 2.1 `project_staging.raw_eia860_generator`

**Source:** EIA-860. **Content:** Generator inventory: plant, utility, prime mover, capacity, status, energy source.

| Column | Type | Note |
| :--- | :--- | :--- |
| `utility_id` | VARCHAR(50) | — |
| `utility_name` | VARCHAR(255) | — |
| `plant_code` | VARCHAR(50) | — |
| `plant_name` | VARCHAR(255) | — |
| `state` | VARCHAR(10) | — |
| `county` | VARCHAR(100) | — |
| `generator_id` | VARCHAR(50) | — |
| `prime_mover` | VARCHAR(20) | — |
| `nameplate_capacity_mw` | VARCHAR(50) | — |
| `status` | VARCHAR(20) | — |
| `operating_year` | VARCHAR(20) | — |
| `retirement_year` | VARCHAR(20) | — |
| `energy_source_1` | VARCHAR(20) | — |
| `balancing_auth_code` | VARCHAR(50) | — |
| `batch_id` | UUID | Load-run identifier (NOT NULL) |
| `ingested_at` | TIMESTAMP WITH TIME ZONE | Default `CURRENT_TIMESTAMP` |

### 2.2 `project_staging.raw_eia860_enviro_assoc`

**Source:** EIA-860 (6_1_EnviroAssoc). **Content:** Boiler-to-generator association records (many-to-many).

| Column | Type | Note |
| :--- | :--- | :--- |
| `utility_id` | VARCHAR(50) | — |
| `utility_name` | VARCHAR(255) | — |
| `plant_code` | VARCHAR(50) | — |
| `plant_name` | VARCHAR(255) | — |
| `boiler_id` | VARCHAR(50) | — |
| `generator_id` | VARCHAR(50) | — |
| `batch_id` | UUID | Load-run identifier (NOT NULL) |
| `ingested_at` | TIMESTAMP WITH TIME ZONE | Default `CURRENT_TIMESTAMP` |

### 2.3 `project_staging.raw_eia923_monthly_generation`

**Source:** EIA-923. **Content:** Monthly net generation and fuel quantity per plant, prime mover, and fuel.

| Column | Type | Note |
| :--- | :--- | :--- |
| `plant_id` | VARCHAR(50) | — |
| `plant_name` | VARCHAR(255) | — |
| `operator_name` | VARCHAR(255) | — |
| `plant_state` | VARCHAR(10) | — |
| `census_region` | VARCHAR(50) | — |
| `reported_prime_mover` | VARCHAR(20) | — |
| `reported_fuel_type` | VARCHAR(20) | — |
| `physical_unit_label` | VARCHAR(50) | — |
| `quantity_january` | VARCHAR(50) | — |
| `quantity_february` | VARCHAR(50) | — |
| `netgen_january` | VARCHAR(50) | — |
| `netgen_february` | VARCHAR(50) | — |
| `batch_id` | UUID | Load-run identifier (NOT NULL) |
| `ingested_at` | TIMESTAMP WITH TIME ZONE | Default `CURRENT_TIMESTAMP` |

### 2.4 `project_staging.raw_epa_hourly_emissions`

**Source:** EPA CAMPD. **Content:** Hourly continuous-emission-monitoring records per unit.

| Column | Type | Note |
| :--- | :--- | :--- |
| `state` | VARCHAR(10) | — |
| `facility_name` | VARCHAR(255) | — |
| `oris_code` | VARCHAR(50) | — |
| `unit_id` | VARCHAR(50) | — |
| `date_observed` | VARCHAR(30) | — |
| `hour_observed` | VARCHAR(10) | — |
| `op_time` | VARCHAR(20) | — |
| `gross_load_mw` | VARCHAR(50) | — |
| `so2_mass_lbs` | VARCHAR(50) | — |
| `nox_mass_lbs` | VARCHAR(50) | — |
| `co2_mass_tons` | VARCHAR(50) | — |
| `heat_input_mmbtu` | VARCHAR(50) | — |
| `batch_id` | UUID | Load-run identifier (NOT NULL) |
| `ingested_at` | TIMESTAMP WITH TIME ZONE | Default `CURRENT_TIMESTAMP` |

### 2.5 `project_staging.raw_noaa_isd_weather`

**Source:** NOAA ISD. **Content:** Hourly surface weather observations per station.

| Column | Type | Note |
| :--- | :--- | :--- |
| `station_id` | VARCHAR(50) | — |
| `timestamp_utc` | VARCHAR(50) | — |
| `air_temperature_c` | VARCHAR(20) | — |
| `dew_point_c` | VARCHAR(20) | — |
| `sea_level_pressure_hpa` | VARCHAR(20) | — |
| `wind_speed_mps` | VARCHAR(20) | — |
| `precipitation_mm` | VARCHAR(20) | — |
| `quality_flags` | VARCHAR(50) | — |
| `batch_id` | UUID | Load-run identifier (NOT NULL) |
| `ingested_at` | TIMESTAMP WITH TIME ZONE | Default `CURRENT_TIMESTAMP` |

> **Design note.** EIA-923 publishes one column per month for each measure. The Bronze table above is defined with the January and February columns as the prototype; the ETL unpivots all twelve monthly columns into one row per plant, prime mover, fuel, and month in Silver. EIA-923 fields that feed `fuel_consumed_mmbtu`, `delivered_fuel_cost_per_mmbtu`, and `ending_fuel_stock_physical`, and the EIA-930 grid telemetry and NOAA station metadata that feed `fact_regional_grid_demand`, `dim_balancing_authority`, and `dim_weather_station`, are landed by additional Bronze columns or tables created during Phase 2 implementation.

---

## 3. Conformed Dimensions (`project_dw`)

### 3.1 `project_dw.dim_date`

Calendar dimension, one row per day. Generated by script, not loaded from a source.

| Column | Type | Constraint | Nullable | Description | Example / Valid Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `date_key` | INTEGER | PK | NO | Surrogate Key (YYYYMMDD integer) | 20230115 |
| `calendar_date` | DATE | UNIQUE | NO | Full calendar date | 2023-01-15 |
| `calendar_year` | SMALLINT | — | NO | 4-digit year | 2023 |
| `calendar_quarter` | SMALLINT | — | NO | Quarter number (1-4) | 1 |
| `calendar_month` | SMALLINT | — | NO | Month number (1-12) | 1 |
| `month_name` | VARCHAR(15) | — | NO | Full name of the month | January |
| `day_of_month` | SMALLINT | — | NO | Day of the month (1-31) | 15 |
| `day_of_week` | SMALLINT | — | NO | Day of week (1=Sunday, 7=Saturday) | 1 |
| `day_name` | VARCHAR(15) | — | NO | Full name of the day | Sunday |
| `is_weekend` | BOOLEAN | — | NO | True if Saturday or Sunday | TRUE |

### 3.2 `project_dw.dim_plant`

Power plant facility. Natural key `orispl_code`. Type 1: corrections overwrite.

| Column | Type | Constraint | Nullable | Description | Example / Valid Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `plant_key` | SERIAL | PK | NO | Surrogate primary key | 101 |
| `orispl_code` | INTEGER | UNIQUE | NO | Master federal energy facility ID | 3 (Barry) |
| `plant_name` | VARCHAR(150) | — | NO | Official plant facility name | Barry |
| `utility_id` | INTEGER | — | YES | EIA utility owner identifier | 195 |
| `utility_name` | VARCHAR(150) | — | YES | Operating utility name | Alabama Power Co |
| `latitude` | NUMERIC(9,6) | — | YES | Geodetic latitude (WGS 84) | 31.006900 |
| `longitude` | NUMERIC(9,6) | — | YES | Geodetic longitude (WGS 84) | -88.010300 |
| `state_code` | CHAR(2) | — | NO | Two-letter US state code | AL |
| `county_name` | VARCHAR(100) | — | YES | County location | Mobile |
| `ba_code` | VARCHAR(20) | — | YES | Balancing Authority identifier | SOCO |
| `epa_region` | SMALLINT | — | YES | EPA regional office jurisdiction (1-10) | 4 |
| `is_combined_heat_power` | BOOLEAN | — | NO | Flag if cogeneration plant | FALSE |

### 3.3 `project_dw.dim_generator`

Generating unit within a plant. **SCD Type 2**: a new row is written when a tracked attribute (operating status, nameplate capacity) changes. Child (outrigger) of `dim_plant` through `orispl_code`.

| Column | Type | Constraint | Nullable | Description | Example / Valid Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `generator_key` | SERIAL | PK | NO | Surrogate primary key | 501 |
| `orispl_code` | INTEGER | FK | NO | Plant foreign key reference | 3 |
| `generator_id` | VARCHAR(20) | — | NO | Generating unit identifier | 1, CT1, ST2 |
| `prime_mover_code` | VARCHAR(10) | — | NO | Thermodynamic engine code | GT, ST, CC, PV, WT |
| `primary_energy_source` | VARCHAR(10) | — | NO | Primary fuel code | NG, BIT, SUB, SUN, WND |
| `nameplate_capacity_mw` | NUMERIC(10,2) | — | YES | Max design electrical capacity (MW) | 150.00 |
| `operating_status` | VARCHAR(30) | — | NO | SCD 2 Monitored status code | OP, SB, RE, OA |
| `row_effective_date` | DATE | — | NO | Start date of this record version | 2020-01-01 |
| `row_expiration_date` | DATE | — | NO | End date of this record version | 9999-12-31 |
| `is_current` | BOOLEAN | — | NO | True if current active record | TRUE |

### 3.4 `project_dw.dim_balancing_authority`

Regional grid operator (balancing authority). Natural key `ba_code`.

| Column | Type | Constraint | Nullable | Description | Example / Valid Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ba_key` | SERIAL | PK | NO | Surrogate primary key | 1 |
| `ba_code` | VARCHAR(20) | UNIQUE | NO | Official BA abbreviation | PJM, CISO, ERCO, MISO |
| `ba_name` | VARCHAR(150) | — | NO | Full grid operator name | PJM Interconnection |
| `region` | VARCHAR(50) | — | YES | NERC Interconnection Region | Eastern, Western, Texas |
| `is_active` | BOOLEAN | — | NO | Active operational status | TRUE |

### 3.5 `project_dw.dim_weather_station`

NOAA ISD weather station. Natural key `station_id`.

| Column | Type | Constraint | Nullable | Description | Example / Valid Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `station_key` | SERIAL | PK | NO | Surrogate primary key | 12 |
| `station_id` | VARCHAR(25) | UNIQUE | NO | NOAA USAF-WBAN / GHCN identifier | USW00094728 |
| `station_name` | VARCHAR(150) | — | YES | Weather station location name | NEW YORK CNTRL PK TWR |
| `state_code` | CHAR(2) | — | YES | Station state code | NY |
| `latitude` | NUMERIC(9,6) | — | YES | Geodetic station latitude | 40.778900 |
| `longitude` | NUMERIC(9,6) | — | YES | Geodetic station longitude | -73.969200 |
| `elevation_m` | NUMERIC(7,2) | — | YES | Elevation above sea level in meters | 39.60 |

---

## 4. Fact Tables (`project_dw`)

### 4.1 `project_dw.fact_hourly_emissions_weather`

- **Archetype:** Transactional fact, range-partitioned on `date_key`
- **Grain:** One row per generating unit (`unit_id`) at a plant for one clock hour.
- **Primary key:** `(date_key, hour_of_day, plant_key, unit_id)`
- **Notes:** Dimensions: `dim_date`, `dim_plant`, `dim_weather_station`. Emission, load, and heat-input measures are additive. `ambient_temp_celsius`, `wind_speed_mps`, and `weather_distance_km` are non-additive and are averaged.

| Column | Type | Constraint | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | INTEGER | PK, FK | NO | Foreign key to dim_date |
| `hour_of_day` | SMALLINT | PK | NO | Hour interval (0-23) |
| `plant_key` | INTEGER | PK, FK | NO | Foreign key to dim_plant |
| `unit_id` | VARCHAR(20) | PK | NO | Combustion smokestack/boiler unit ID |
| `station_key` | INTEGER | FK | YES | Foreign key to nearest dim_weather_station |
| `gross_load_mw` | NUMERIC(10,2) | — | YES | Gross electrical power produced (MW) |
| `heat_input_mmbtu` | NUMERIC(12,3) | — | YES | Total thermal heat input from fuel (MMBtu) |
| `so2_mass_lbs` | NUMERIC(12,3) | — | YES | Sulfur dioxide emissions mass (lbs) |
| `nox_mass_lbs` | NUMERIC(12,3) | — | YES | Nitrogen oxides emissions mass (lbs) |
| `co2_mass_tons` | NUMERIC(12,3) | — | YES | Carbon dioxide emissions mass (short tons) |
| `ambient_temp_celsius` | NUMERIC(5,2) | — | YES | NOAA ISD surface temperature (°C) |
| `wind_speed_mps` | NUMERIC(5,2) | — | YES | NOAA ISD surface wind speed (m/s) |
| `weather_distance_km` | NUMERIC(6,2) | — | YES | Spatial Haversine distance to station (km) |

### 4.2 `project_dw.fact_monthly_plant_operations`

- **Archetype:** Periodic snapshot fact
- **Grain:** One row per plant, prime mover, and energy source for one calendar month.
- **Primary key:** `snapshot_key` (surrogate)
- **Notes:** Dimensions: `dim_date` (month start), `dim_plant`. `net_generation_mwh` and `fuel_consumed_mmbtu` are additive. `fuel_consumed_physical` is additive only within one unit of measure. `avg_heat_rate_btu_kwh` and `delivered_fuel_cost_per_mmbtu` are non-additive ratios and are recomputed from sums. `ending_fuel_stock_physical` is semi-additive (not summed across months).

| Column | Type | Constraint | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `snapshot_key` | SERIAL | PK | NO | Surrogate primary key |
| `month_start_date_key` | INTEGER | FK | NO | First day of reporting month in dim_date |
| `plant_key` | INTEGER | FK | NO | Foreign key to dim_plant |
| `prime_mover_code` | VARCHAR(10) | — | NO | Prime mover code (ST, GT, CC, etc.) |
| `energy_source_code` | VARCHAR(10) | — | NO | Fuel type code (NG, BIT, SUB, etc.) |
| `net_generation_mwh` | NUMERIC(14,3) | — | NO | Net power exported (MWh; negative if outage) |
| `fuel_consumed_physical` | NUMERIC(14,3) | — | YES | Physical fuel units (tons/barrels/Mcf) |
| `fuel_consumed_mmbtu` | NUMERIC(14,3) | — | YES | Total thermal heat content consumed (MMBtu) |
| `avg_heat_rate_btu_kwh` | NUMERIC(10,2) | — | YES | Calculated thermal heat rate efficiency |
| `delivered_fuel_cost_per_mmbtu` | NUMERIC(8,2) | — | YES | Average delivered fuel cost ($/MMBtu) |
| `ending_fuel_stock_physical` | NUMERIC(14,3) | — | YES | Fuel inventory stored on-site at month end |

### 4.3 `project_dw.fact_regional_grid_demand`

- **Archetype:** Aggregate grid fact (hourly, balancing-authority grain)
- **Grain:** One row per balancing authority for one clock hour.
- **Primary key:** `(date_key, hour_of_day, ba_key)`
- **Notes:** Dimensions: `dim_date`, `dim_balancing_authority`. All MW measures are additive across balancing authorities for the same hour; over time they are averaged, or summed to MWh at the hourly grain.

| Column | Type | Constraint | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | INTEGER | PK, FK | NO | Foreign key to dim_date |
| `hour_of_day` | SMALLINT | PK | NO | Hour of observation (0-23) |
| `ba_key` | INTEGER | PK, FK | NO | Foreign key to dim_balancing_authority |
| `demand_mw` | NUMERIC(12,2) | — | YES | Total grid demand / load (MW) |
| `demand_forecast_mw` | NUMERIC(12,2) | — | YES | Day-ahead demand forecast (MW) |
| `net_gen_coal_mw` | NUMERIC(12,2) | — | YES | Real-time coal power dispatch (MW) |
| `net_gen_gas_mw` | NUMERIC(12,2) | — | YES | Real-time natural gas power dispatch (MW) |
| `net_gen_nuclear_mw` | NUMERIC(12,2) | — | YES | Real-time nuclear power dispatch (MW) |
| `net_gen_hydro_mw` | NUMERIC(12,2) | — | YES | Real-time hydro power dispatch (MW) |
| `net_gen_wind_mw` | NUMERIC(12,2) | — | YES | Real-time wind renewable dispatch (MW) |
| `net_gen_solar_mw` | NUMERIC(12,2) | — | YES | Real-time solar renewable dispatch (MW) |
| `net_interchange_mw` | NUMERIC(12,2) | — | YES | Net power imported/exported across ties (MW) |

---

## 5. Quarantine and Audit Tables

### 5.1 `quarantine.rejected_records`

Dead-letter table. Each row keeps the complete unaltered source row as JSON plus the reason it was rejected.

| Column | Type | Constraint | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `rejection_id` | BIGSERIAL | PK | NO | Surrogate error identifier |
| `batch_id` | UUID | — | NO | Pipeline ingestion batch execution ID |
| `source_system` | VARCHAR(50) | — | NO | Source system name (EIA, EPA, NOAA) |
| `source_table` | VARCHAR(100) | — | NO | Originating staging table |
| `source_row_identifier` | VARCHAR(100) | — | YES | Natural identifier of corrupt row |
| `rejection_reason` | VARCHAR(255) | — | NO | Specific data contract violation code |
| `raw_payload_json` | JSONB | — | NO | Complete unaltered raw row stored as JSON |
| `rejected_at` | TIMESTAMPTZ | — | NO | Rejection timestamp |

### 5.2 `project_staging.etl_run_log`

One row per pipeline step per batch. Counts rows read, inserted, updated, and rejected, and records the run status.

| Column | Type | Constraint | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_id` | BIGSERIAL | PK | NO | Surrogate execution identifier |
| `batch_id` | UUID | — | NO | Batch execution UUID |
| `pipeline_step` | VARCHAR(100) | — | NO | Pipeline stage name |
| `source_system` | VARCHAR(50) | — | NO | Upstream agency code |
| `records_read` | INTEGER | — | NO | Count of input rows extracted |
| `records_inserted` | INTEGER | — | NO | Count of rows successfully loaded |
| `records_updated` | INTEGER | — | NO | Count of SCD updates performed |
| `records_rejected` | INTEGER | — | NO | Count of records sent to quarantine |
| `execution_status` | VARCHAR(30) | — | NO | RUNNING, COMPLETED, FAILED |
| `start_time` | TIMESTAMPTZ | — | NO | Step start timestamp |
| `end_time` | TIMESTAMPTZ | — | YES | Step completion timestamp |
| `error_message` | TEXT | — | YES | Error traceback if failed |

---

## 6. Reporting Views (`project_reporting`)

The Gold layer. Each view joins facts to dimensions and aggregates to the grain a Power BI visual needs.

### 6.1 `project_reporting.vw_emissions_intensity`

Daily plant-level emissions and carbon intensity with ambient temperature. Source: `fact_hourly_emissions_weather`.

| Column | Type | Derived Expression | Description | Target Power BI Visual |
| :--- | :--- | :--- | :--- | :--- |
| `calendar_date` | DATE | `d.calendar_date` | Observation date | Time series line chart |
| `plant_name` | VARCHAR(150) | `p.plant_name` | Generating facility name | Bar chart / Slicer |
| `total_gross_mw` | NUMERIC | `SUM(f.gross_load_mw)` | Total gross electrical output | KPI card |
| `total_co2_tons` | NUMERIC | `SUM(f.co2_mass_tons)` | Total CO2 emissions in short tons | KPI card |
| `co2_intensity_tons_per_mw` | NUMERIC | `total_co2_tons / total_gross_mw` | Carbon intensity ratio | Gauge / Color indicator |
| `avg_ambient_temp_celsius` | NUMERIC | `AVG(f.ambient_temp_celsius)` | NOAA ISD ambient temperature | Scatter plot (Temp vs Carbon) |

### 6.2 `project_reporting.vw_plant_performance`

Monthly plant fuel use, net generation, heat rate, and an outage indicator. Source: `fact_monthly_plant_operations`.

| Column | Type | Derived Expression | Description | Target Power BI Visual |
| :--- | :--- | :--- | :--- | :--- |
| `calendar_year` | SMALLINT | `d.calendar_year` | Reporting year | Year slicer |
| `month_name` | VARCHAR(15) | `d.month_name` | Month name | X-axis category |
| `orispl_code` | INTEGER | `p.orispl_code` | Plant code | Matrix drilldown |
| `net_generation_mwh` | NUMERIC | `SUM(f.net_generation_mwh)` | Net power exported to grid | Column chart |
| `avg_heat_rate` | NUMERIC | `AVG(f.avg_heat_rate_btu_kwh)` | Calculated thermal efficiency | Heatmap matrix |
| `operational_state` | VARCHAR | `CASE Net < 0 THEN OUTAGE...` | Station service indicator | Alert badge |

### 6.3 `gold_marts.vw_grid_stress`

Hourly balancing-authority demand, day-ahead forecast residuals, renewable share, and grid stress alert levels. Source: `fact_regional_grid_demand`.

| Column | Type | Derived Expression | Description | Target Power BI Visual |
| :--- | :--- | :--- | :--- | :--- |
| `ba_code` | STRING | `ba.ba_code` | Balancing authority code | Geographic map / Slicer |
| `demand_mw` | DOUBLE | `g.demand_mw` | Instantaneous hourly electrical demand (MW) | Line / Area chart |
| `demand_forecast_mw` | DOUBLE | `g.demand_forecast_mw` | Day-ahead forecast demand (MW) | Line chart comparison |
| `demand_forecast_residual_mw` | DOUBLE | `g.demand_mw - g.demand_forecast_mw` | Hourly forecast error residual | Bar chart (Stress monitor) |
| `total_renewable_generation_mw`| DOUBLE | `g.net_gen_wind_mw + g.net_gen_solar_mw`| Wind + solar clean energy total | Stacked area chart |
| `renewable_penetration_pct` | DOUBLE | `(Renewables / Demand) * 100` | Clean energy share (%) | Donut chart / Executive KPI |
| `net_interchange_mw` | DOUBLE | `g.net_interchange_mw` | Net interchange import/export | KPI card |

### 6.4 `gold_marts.vw_monthly_generation_mix`

Monthly prime mover and energy source generation totals, fuel consumption, and weighted heat rates. Source: `fact_monthly_plant_operations`.

| Column | Type | Derived Expression | Description | Target Power BI Visual |
| :--- | :--- | :--- | :--- | :--- |
| `calendar_year` | INT | `d.calendar_year` | Calendar reporting year | Slicer / X-axis |
| `month_name` | STRING | `d.month_name` | Calendar month name | Trend axis |
| `state_code` | STRING | `p.state_code` | State two-letter postal code | Map visual |
| `prime_mover_code` | STRING | `f.prime_mover_code` | Prime mover technology (CC, CT, ST, WT, PV) | Categorical breakdown |
| `energy_source_code` | STRING | `f.energy_source_code` | Energy source fuel (NG, BIT, WND, SUN) | Color legend |
| `total_net_generation_mwh` | DOUBLE | `SUM(f.net_generation_mwh)` | Total monthly net generation (MWh) | Stacked bar chart |
| `weighted_heat_rate_btu_kwh` | DOUBLE | `(SUM(Fuel) * 1000) / SUM(NetGen)`| Weighted thermal heat rate | Scatter / Efficiency matrix |


> The dictionary lists the columns used by the dashboard. The view SQL in `05_Analytics/Views.sql` also exposes supporting columns (for example `state_code`, `total_so2_lbs`, `total_nox_lbs`, `peak_hourly_demand_mw`).

---

## 7. Business Key to Surrogate Key Mapping

| Dimension | Business (natural) key | Surrogate key | Source of the business key |
| :--- | :--- | :--- | :--- |
| `dim_date` | `calendar_date` | `date_key` (`YYYYMMDD`) | Generated calendar |
| `dim_plant` | `orispl_code` | `plant_key` | EIA-860 Plant Code, equal to EPA ORIS code |
| `dim_generator` | `orispl_code` + `generator_id` + `row_effective_date` | `generator_key` | EIA-860 |
| `dim_balancing_authority` | `ba_code` | `ba_key` | EIA-930 |
| `dim_weather_station` | `station_id` | `station_key` | NOAA ISD |

Fact loading replaces each business key with its surrogate key by lookup. Example: EPA record `oris_code = 3` is resolved through `dim_plant.orispl_code` to `plant_key`, and the date and hour are split into `date_key` and `hour_of_day`. Rows whose business key has no match are sent to quarantine, so the loaded fact has zero orphan rows.

---

## 8. Code Lists and Reference Values

**Prime mover (`prime_mover_code`)**

| Code | Meaning |
| :--- | :--- |
| ST | Steam turbine (coal, oil, gas, nuclear, biomass) |
| GT | Combustion (gas) turbine, simple cycle |
| CC | Combined cycle, total unit |
| CA | Combined cycle, steam part |
| CT | Combined cycle, combustion turbine part |
| CS | Combined cycle, single shaft |
| PV | Photovoltaic |
| WT | Wind turbine |

**Energy source (`primary_energy_source`, `energy_source_code`)**

| Code | Meaning |
| :--- | :--- |
| NG | Natural gas |
| BIT | Bituminous coal |
| SUB | Subbituminous coal |
| LIG | Lignite coal |
| SUN | Solar |
| WND | Wind |

**Generator operating status (`operating_status`, tracked by SCD Type 2)**

| Code | Meaning |
| :--- | :--- |
| OP | Operating |
| SB | Standby / backup |
| OA | Out of service, expected to return |
| RE | Retired |

**Missing-value sentinels converted to `NULL`**

| Source | Sentinel values | Column examples |
| :--- | :--- | :--- |
| EIA-923 | `.`, `NM` (not meaningful), `*`, empty string | `quantity_january`, `netgen_january` |
| NOAA ISD | `-9999` | `air_temperature_c`, `wind_speed_mps` |

**Quarantine reason codes (`rejection_reason`)**

| Code | Rule | Status |
| :--- | :--- | :--- |
| `NUMERIC_FIELD_CONTAINS_STRING_SENTINEL` | EIA-923 numeric field holds `.`, `NM`, `*`, or blank | Rule drafted in `quality_checks.sql` |
| `NOAA_SENTINEL_SENSOR_DROPOUT` | NOAA temperature or wind equals `-9999` | Rule drafted |
| `CCGT_HEAT_RATE_OUT_OF_BOUNDS` | Combined-cycle heat rate outside 5,000 to 14,000 Btu/kWh | Rule drafted |
| `COAL_ST_HEAT_RATE_OUT_OF_BOUNDS` | Steam-turbine heat rate outside 8,500 to 18,000 Btu/kWh | Rule drafted |
| `PEAKER_GT_HEAT_RATE_OUT_OF_BOUNDS` | Simple-cycle gas turbine heat rate outside 9,000 to 22,000 Btu/kWh | Rule drafted |
| Referential-integrity and duplicate-key failures | Fact row without a matching dimension row; duplicate business key | Implemented in Phase 2 |

`STATION_SERVICE_EXCEEDS_OUTPUT` is not a rejection. Negative `net_generation_mwh` is valid (a plant that is offline draws station power from the grid), so those rows stay in the fact table and are flagged in `vw_plant_performance.operational_state`.

---

## 9. Source-to-Warehouse Lineage (Key Measures)

| Warehouse column | Bronze source column | Source system | Transformation |
| :--- | :--- | :--- | :--- |
| `fact_hourly_emissions_weather.plant_key` | `raw_epa_hourly_emissions.oris_code` | EPA CAMPD | Lookup to `dim_plant.orispl_code` |
| `fact_hourly_emissions_weather.date_key`, `hour_of_day` | `date_observed`, `hour_observed` | EPA CAMPD | Parse date to `YYYYMMDD`; hour to 0 through 23 |
| `fact_hourly_emissions_weather.gross_load_mw` | `gross_load_mw` | EPA CAMPD | Cast to numeric; sentinels to `NULL` |
| `fact_hourly_emissions_weather.heat_input_mmbtu` | `heat_input_mmbtu` | EPA CAMPD | Cast to numeric |
| `fact_hourly_emissions_weather.so2_mass_lbs`, `nox_mass_lbs`, `co2_mass_tons` | `so2_mass_lbs`, `nox_mass_lbs`, `co2_mass_tons` | EPA CAMPD | Cast to numeric; unit check |
| `fact_hourly_emissions_weather.ambient_temp_celsius` | `raw_noaa_isd_weather.air_temperature_c` | NOAA ISD | `-9999` to `NULL`; nearest-hour join |
| `fact_hourly_emissions_weather.wind_speed_mps` | `raw_noaa_isd_weather.wind_speed_mps` | NOAA ISD | `-9999` to `NULL`; nearest-hour join |
| `fact_hourly_emissions_weather.station_key`, `weather_distance_km` | `raw_noaa_isd_weather.station_id` | NOAA ISD + `dim_plant` coordinates | Nearest station within 50 km by Haversine distance; ±60-minute time match |
| `fact_monthly_plant_operations.net_generation_mwh` | `raw_eia923_monthly_generation.netgen_*` | EIA-923 | Unpivot months; cast; negative values allowed |
| `fact_monthly_plant_operations.fuel_consumed_physical` | `raw_eia923_monthly_generation.quantity_*` | EIA-923 | Unpivot months; cast |
| `fact_monthly_plant_operations.avg_heat_rate_btu_kwh` | Derived | EIA-923 | `fuel_consumed_mmbtu * 1000 / net_generation_mwh` |
| `dim_generator.*` | `raw_eia860_generator.*` | EIA-860 | SCD Type 2 on status and capacity |
| `fact_regional_grid_demand.*` | EIA-930 landing table (Phase 2) | EIA-930 | Hourly per balancing authority; `ba_code` to `ba_key` |

