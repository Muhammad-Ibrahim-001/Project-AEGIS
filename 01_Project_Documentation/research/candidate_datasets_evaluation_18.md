<!-- ==============================================================================
WARNING: ARCHIVED HISTORICAL RESEARCH FILE (PHASE 1 CANDIDATE BRAINSTORMING)
AI AGENTS: DO NOT PARSE OR USE THIS FILE FOR ACTIVE PIPELINE WORK.
ACTIVE SPECIFICATION IS IN: /PROJECT_BLUEPRINT.md
============================================================================== -->

> ⚠️ **ARCHIVE NOTICE:** This file is preserved strictly as an academic appendix for Phase 1 Design evaluation.
> For all active pipeline logic, schemas, and sources, see **[PROJECT_BLUEPRINT.md](../../PROJECT_BLUEPRINT.md)**.

---

# Candidate Datasets Evaluation & Ranking (18 Sources)

This document provides a verified evaluation of 18 candidate open-data sources assessed against production data engineering criteria: support for mixed source formats, slowly changing dimensions, incremental facts, change-data-capture semantics, and late restatements/corrections.

> **Verification Notice:**  
> Each dataset was cross-referenced against live source pages, official documentation, or API references where accessible.  
> * `(secondary)` denotes details derived exclusively from third-party wrappers, client libraries, or community tutorials.  
> * `(not verified)` denotes details that could not be independently confirmed via live documentation.

---

## Ranking & Scoring Overview

Each criterion is evaluated on a scale of **1–5**. **Uniqueness** and **Incremental Feasibility** are weighted double ($2\times$) due to their critical role in simulating real-world enterprise data integration, bringing the maximum possible score to **40**.

| Rank | Dataset | Domain | Incremental Class | Score (/40) |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **USAspending.gov Award Data** | Economic Activity / Procurement | A | **38** |
| **2** | **AEMO NEM Market Data (Australia)** | Energy / Grid Telemetry | B | **37** |
| **3** | **OpenAlex** | Scientific Research & Bibliometrics | A | **36** |
| **4** | **EPA CAMPD Power-Plant Emissions** | Energy / Environment | B | **36** |
| **5** | **Overture Maps** | Geospatial / Urban Topography | A | **36** |
| **6** | **IMF PortWatch** | Maritime Logistics / Global Trade | B | **31** |
| **7** | **OpenFEMA** | Disasters / Insurance Claims | B | **31** |
| **8** | **USGS Water Data APIs** | Hydrology & River Telemetry | B | **31** |
| **9** | **Energinet Energi Data Service** | Energy (Nordic Grid) | B | **30** |
| **10** | **CMS Open Payments** | Healthcare / Pharma Compliance | A *(annual)* | **29** |
| **11** | **ClinicalTrials.gov** | Healthcare / Clinical Trials | B | **29** |
| **12** | **England Environment Agency Flood Monitoring** | Water / Flood Risk Telemetry | B | **29** |
| **13** | **Global Fishing Watch** | Maritime / Ecology Telemetry | B | **29** |
| **14** | **openFDA** | Healthcare / Regulatory Pharmacovigilance | B | **28** |
| **15** | **NASA FIRMS Active Fires** | Satellite Remote Sensing | B | **27** |
| **16** | **USDA FAS PSD / Export Sales** | Agricultural Commodities | C *(PSD)*, B *(Sales)* | **27** |
| **17** | **MBTA Rapid-Transit Performance** | Public Transit Telemetry | B | **26** |
| **18** | **NOAA Storm Events** | Severe Weather Impacts | C | **21** |

---

## Candidate Deep Dives

### 1. USAspending.gov: Federal Contracts, Grants and Loans
* **Domain:** Economic Activity / Procurement
* **Source and Access:** U.S. Department of the Treasury (DATA Act compliance).
  * Bulk Archive: [usaspending.gov/download_center/award_data_archive](https://www.usaspending.gov/download_center/award_data_archive)
  * API Listing Endpoint: `/api/v2/bulk_download/list_monthly_files/`
  * Scope Documentation: [about-the-data-download.pdf](https://www.usaspending.gov/data/about-the-data-download.pdf)
* **Content:** Prime-award transactions for federal contracts and financial assistance, including award IDs, modification numbers, agency identifiers, and CFDA catalog numbers. The upstream delta-file generation pipeline emits an explicit `correction_delete_ind` flag alongside dedicated delete-records files. Budget-account balance tables (File C) attach to previously published award records.
* **Coverage and Volume:** Contract archives date back to FY2001 *(secondary)*; public landing pages cite display data originating from October 2008. Secondary reports document full historical PostgreSQL dumps exceeding 1.5 TB. Total row count: *(not verified)*.
* **Updates:** Full and Delta files regenerate monthly. Procurement awards are submitted daily by federal agencies and pulled into the warehouse nightly.
* **Full Load Feasibility:** Yes, via pre-packaged Full archive files by award type, fiscal year, and agency, or via custom API download jobs.
* **Incremental Ingestion (Class A):** Monthly Delta files carry exclusively new or modified transactions plus an explicit correction/delete flag (`correction_delete_ind`), providing true change-data-capture (CDC) semantics.
* **Related Data and Analytics:** Contracts, grants, loans, direct payments, sub-awards, account allocations, recipient hierarchies, and agency trees. Analytical use cases include federal expenditure concentration by agency/industry, award modification lifecycles, and de-obligation/correction rates. Evolving recipient and agency metadata provides textbook Slowly Changing Dimension (SCD Type 2) material.
* **Why Overlooked:** The scale (>1.5 TB raw) and complex award-modification lineage rules deter developers accustomed to simple flat datasets.
* **Challenges & Caveats:** Requires scoping by fiscal year or agency. Agencies frequently submit late retrofits to correct transaction amounts, and de-obligations/deletions are flagged with `D`.

---

### 2. AEMO National Electricity Market (Australia)
* **Domain:** Energy / Power Grid Operations
* **Source and Access:** Australian Energy Market Operator (AEMO).
  * Rolling Window Data: [nemweb.com.au/Reports/Current/](https://nemweb.com.au/Reports/Current/)
  * Daily Archival Data: [nemweb.com.au/Reports/Archive/](https://nemweb.com.au/Reports/Archive/)
  * MMS Dispatch Documentation: [AEMO Dispatch Data](https://www.aemo.com.au/Energy-systems/Electricity/National-Electricity-Market-NEM/Data-NEM/Market-Management-System-MMS-data/Dispatch)
* **Content:** `DISPATCHPRICE` tables contain 5-minute energy and ancillary-service prices. When a price undergoes ex-post administrative correction, the updated figure is written to `RRP` while preserving the original price in `ROP` as an immutable audit trail. Feeds also track regional electricity demand, generator output, interconnector flows, transmission constraints, 30-minute trading prices, and pre-dispatch forecast horizons.
* **Coverage and Volume:** Archival series date back to approximately July 2009 *(secondary)*. The market transitioned to 5-minute financial settlement on October 1, 2021 *(secondary)*. Row counts: *(not verified)*; logging 288 daily dispatch intervals across hundreds of generators and regional nodes yields high-volume telemetry.
* **Updates:** 5-minute dispatch files maintain a 2-day rolling window; trading files maintain a 14-day rolling window. Permanent daily aggregate archives are published shortly after 04:00 daily.
* **Full Load Feasibility:** High, via daily archive files. A monthly historical MMSDM archive also exists *(secondary; confirm specific path)*.
* **Incremental Ingestion (Class B):** New partitioned files land every interval; `settlementdate` acts as the incremental watermark. There is no `updated_at` filter, no REST query interface, and no delete feed. Price restatements are tracked via the `RRP`/`ROP` audit columns.
* **Related Data and Analytics:** Full MMS Data Model documentation defines explicit relational schemas, indexes, and primary keys. Analysis topics include price spike sessionization, interconnector congestion rents, demand forecast variance, and renewable penetration.
* **Why Overlooked:** Specifically targeted at industrial power market participants; complex nomenclature, domain jargon, and raw flat-file delivery deter generalists.
* **Challenges & Caveats:** Multi-table flat files delivered via HTTP file server directories without a REST API. Ingestors missing the rolling window must backfill from daily archives. Timestamps are period-ending, and the October 2021 settlement reform altered the fundamental time grain.

---

### 3. OpenAlex: Scholarly Works, Authors, Institutions
* **Domain:** Scientific Research & Bibliometrics
* **Source and Access:** OurResearch (OpenAlex).
  * S3 Browser: [openalex.s3.amazonaws.com/browse.html](https://openalex.s3.amazonaws.com/browse.html)
  * Data Snapshot Documentation: [developers.openalex.org/download-all-data/openalex-snapshot](https://developers.openalex.org/download-all-data/openalex-snapshot)
  * Access via AWS CLI: `aws s3 sync s3://openalex <local_dir> --no-sign-request`
* **Content:** Academic works, authors, host sources/venues, institutions, publishers, research funders, and concept topics delivered as deeply nested JSON Lines and Apache Parquet.
* **Coverage and Volume:** Release manifests cite ~264 million works at ~350 GB compressed; secondary documentation references an expanded corpus containing roughly 510 million works.
* **Updates:** Daily snapshot refreshes and delta feeds require an institutional paid tier. Public snapshot refresh cadence: *(not verified)*.
* **Full Load Feasibility:** High. Complete snapshots are open and freely downloadable from public AWS S3 buckets.
* **Incremental Ingestion (Class A):** Object storage partitions are segmented by `updated_date`, enabling incremental synchronization by pulling partitions newer than the local high watermark. The `works` theme includes a cumulative `deleted_ids.csv` file, while entity merges are recorded in a dedicated `merged_ids` directory.
* **Related Data and Analytics:** Co-authorship graph analytics, institutional research impact, funding agency attribution, and longitudinal topic modeling. Changing institutional affiliations and university name reclassifications form natural SCD Type 2 dimensions.
* **Why Overlooked:** Predominantly analyzed within academic bibliometrics; rarely featured in modern data engineering portfolios.
* **Challenges & Caveats:** Enormous data volume, deep array nesting (requiring complex unnesting and relational flattening), handling entity ID merges/redirects, and confirming free REST API rate limits.

---

### 4. EPA CAMPD: Power-Plant Emissions, Allowances, Compliance
* **Domain:** Energy / Environmental Regulations
* **Source and Access:** U.S. Environmental Protection Agency Clean Air Markets Division.
  * Bulk Data Downloads: [campd.epa.gov/data/bulk-data-files](https://campd.epa.gov/data/bulk-data-files)
  * API Portal: [epa.gov/power-sector/cam-api-portal](https://www.epa.gov/power-sector/cam-api-portal)
  * Code Examples: [github.com/USEPA/cam-api-examples](https://github.com/USEPA/cam-api-examples)
* **Content:** Continuous Emission Monitoring System (CEMS) sensor telemetry collected under 40 CFR Part 75. Contains hourly, daily, monthly, and annual apportioned emissions ($\text{SO}_2$, $\text{NO}_x$, $\text{CO}_2$), gross electrical generation, heat input, facility unit/stack configurations, emissions allowances, and compliance records.
* **Coverage and Volume:** Historical files span multi-decade compliance tracking across thousands of power plant units, running into billions of individual hourly sensor rows *(estimated)*. Start year and exact row counts: *(not verified)*.
* **Updates:** Formally synchronized with quarterly regulatory reporting windows. Exact publication cadence: *(not verified)*.
* **Full Load Feasibility:** High. Pre-packaged bulk ZIP/Parquet files allow mass download without paginating API rate limits.
* **Incremental Ingestion (Class B):** API supports date-range parameters; bulk files arrive as quarterly partitions. Resubmissions occur when utilities recalibrate stack flow monitors, requiring partition-level overwrite or upsert reconciliation. Row-level `updated_at`: *(not verified)*.
* **Related Data and Analytics:** Smokestack emissions intensity ($\text{lbs}/\text{MWh}$), coal-to-gas fuel switching, and clean air allowance trading. Unit lifecycle states and changing corporate parent ownership require dimensional tracking.
* **Why Overlooked:** Regulatory reporting context and mandatory (though free) API key registration.
* **Challenges & Caveats:** Apportioned emissions differ from raw ECMPS engineering data due to complex combined-cycle and common-stack boiler configurations. Ingesting full multi-year hourly data requires distributed storage and out-of-core compute.

---

### 5. Overture Maps: Places, Buildings, Divisions, Transportation
* **Domain:** Geospatial / Urban Infrastructure
* **Source and Access:** Overture Maps Foundation (Linux Foundation, Amazon, Meta, Microsoft, TomTom).
  * Documentation: [docs.overturemaps.org/getting-data/cloud-sources/](https://docs.overturemaps.org/getting-data/cloud-sources/)
  * S3 Bucket: `s3://overturemaps-us-west-2/release/<RELEASE>/` (with direct Azure mirrors; no API key needed).
* **Content:** Monthly cloud-native GeoParquet releases indexed by Global Entity Reference System (GERS) stable IDs. Themes include Addresses (alpha), Base topography, Buildings, Administrative Divisions, Places (POIs), and Transportation networks.
* **Coverage and Volume:** Global multi-gigabyte/terabyte geospatial coverage across hundreds of millions of building footprints and point-of-interest entities.
* **Updates:** Published on a regular monthly cadence.
* **Full Load Feasibility:** High, through direct GeoParquet reads partitioned by theme and release date.
* **Incremental Ingestion (Class A):** Publishes formal changelog tables detailing whether each feature in every theme was added, removed, modified, or retained relative to the prior month's release, accompanied by column-level modification arrays.
* **Related Data and Analytics:** POI churn, business category migration, urban expansion, and building density indexing. GERS provides a global foreign key linking diverse municipal and commercial geometries.
* **Why Overlooked:** Modern foundation released relatively recently; predominantly utilized by specialized GIS and geospatial data scientists.
* **Challenges & Caveats:** Schema evolution is rapid (e.g., deprecation and removal of the `places categories` property in 2026 releases); requires specialized spatial compute engines (DuckDB Spatial, Apache Sedona, GeoPandas).

---

### 6. IMF PortWatch: Daily Port Calls and Trade Estimates
* **Domain:** Maritime Logistics / International Trade
* **Source and Access:** International Monetary Fund & University of Oxford.
  * Portal: [portwatch.imf.org](https://portwatch.imf.org)
  * ArcGIS REST FeatureServer: `services9.arcgis.com/.../Daily_Chokepoints_Data/FeatureServer/0`
  * Secondary Mirrors: Humanitarian Data Exchange ([data.humdata.org/organization/portwatch](https://data.humdata.org/organization/portwatch))
* **Content:** Daily port calls broken down by vessel type (container, tanker, dry bulk) and estimated daily import/export volumes in metric tons across 1,648 commercial ports and 24 strategic maritime chokepoints (e.g., Suez Canal, Bab el-Mandeb, Panama Canal, Strait of Malacca).
* **Coverage and Volume:** Time series runs from 2019 to present. Row count: *(not verified)*, estimated in the millions.
* **Updates:** Daily estimates are compiled and published on a weekly refresh cadence.
* **Full Load Feasibility:** Moderate to High; feasible by paginating ArcGIS FeatureServer endpoints or downloading packaged datasets from HDX.
* **Incremental Ingestion (Class B):** Supports SQL date filtering. Upstream researchers note that estimates undergo continuous upward revision over rolling 21-day windows as delayed AIS transponder signals are processed, creating a real-world restatement problem. Row-level modified timestamp: *(not verified)*.
* **Related Data and Analytics:** Geopolitical conflict rerouting (e.g., Red Sea disruptions), port dwell times, berth congestion, and macro trade nowcasting.
* **Why Overlooked:** Launched recently (late 2023 beta); primarily known within macroeconomic policy circles.
* **Challenges & Caveats:** Trade values represent AIS-derived algorithmic proxies rather than official customs filings. The public ArcGIS endpoint enforces a strict 1,000-records-per-request pagination cap.

---

### 7. OpenFEMA: Disaster Declarations, Flood Insurance Policies & Claims
* **Domain:** Disaster Management / Climate Risk Insurance
* **Source and Access:** Federal Emergency Management Agency (FEMA).
  * API Base: [fema.gov/api/open/v2/FimaNfipClaims](https://www.fema.gov/api/open/v2/FimaNfipClaims)
  * Schema & Fields Reference: [fema.gov/api/open/v1/OpenFemaDataSetFields](https://www.fema.gov/api/open/v1/OpenFemaDataSetFields)
* **Content:** Federal disaster declarations, National Flood Insurance Program (NFIP) policies-in-force, and redacted NFIP claim settlement records (including building/contents damage amounts, flood zone classifications, and elevation ratings).
* **Coverage and Volume:** Tens of millions of historical insurance records spanning decades. An endpoint provides dynamic `recordCount` metadata.
* **Updates:** Varies by dataset (`accrualPeriodicity` field in metadata; some tables update weekly/monthly, others irregularly).
* **Full Load Feasibility:** High, available via bulk CSV/JSON files or paginated API requests.
* **Incremental Ingestion (Class B with Hash Diffing):** Every record includes an upstream MD5 cryptographic hash and a `lastRefresh` timestamp indicating the date it was written into the API data store. The MD5 hash enables row-level change detection during incremental ingestion. Whether a full database re-indexing resets `lastRefresh`: *(not verified)*. Explicit deletion signals: *(not verified)*.
* **Related Data and Analytics:** Flood payout severity, repetitive loss properties, and climate risk exposure. Joins directly to NOAA Storm Events (#18) by county FIPS code and date.
* **Why Overlooked:** While popular in exploratory data science, few data engineering portfolios build automated incremental ETL pipelines on top of it.
* **Challenges & Caveats:** Navigation across v1/v2 schema transitions, paginated query caps, and deprecated field definitions.

---

### 8. USGS Water Data APIs
* **Domain:** Hydrology & Environmental Monitoring
* **Source and Access:** U.S. Geological Survey.
  * OGC API Endpoints: `api.waterdata.usgs.gov/ogcapi/v0/collections/`
  * API Migration Documentation: [api.waterdata.usgs.gov/docs/ogcapi/migration](https://api.waterdata.usgs.gov/docs/ogcapi/migration)
* **Content:** Modernized OGC-compliant endpoints providing 15-minute continuous telemetry, daily values, monitoring locations, field measurements, flood peaks, rating curve calibrations, and data revisions across thousands of river streamgages.
* **Coverage and Volume:** Multi-decade historical time series across 10,000+ continuous monitoring stations. Row count: *(not verified)*; total measurements exceed hundreds of millions of sensor readings.
* **Updates:** Real-time satellite downlinks updated every 15–60 minutes. Raw data carries explicit provisional notices subject to long-tail hydrologist revision.
* **Full Load Feasibility:** Achieved by partitioning downloads by state or river basin; no single-click monolithic archive dump.
* **Incremental Ingestion (Class B):** API accepts ISO-8601 time window filters (e.g., `P1D`). A dedicated `/revisions` endpoint enables pipelines to detect historical stage-discharge rating recalculations and retroactively update provisional data to approved status.
* **Related Data and Analytics:** Streamflow forecasting, drought modeling, flood threshold exceedance, and monitoring station metadata tracking (SCD Type 2).
* **Why Overlooked:** Most public tutorials still reference the legacy NWIS interface.
* **Challenges & Caveats:** Ongoing deprecation of legacy USGS APIs (phased out in early 2027); high request volume requires acquiring a free developer API key to avoid throttling.

---

### 9. Energinet Energi Data Service (Denmark)
* **Domain:** Power Grid Telemetry & Nordic Energy Markets
* **Source and Access:** Energinet (Danish Transmission System Operator).
  * API Endpoint: `api.energidataservice.dk/dataset/<DatasetName>`
* **Content:** ~100 distinct energy datasets covering spot market electricity prices, real-time renewable production (wind, solar), transmission exchange capacities, grid frequency balancing, and natural gas flows. Accessible without an API key.
* **Coverage and Volume:** Granular time series; e.g., the `Elspotprices` table contains ~1.8 million records and `DayAheadPrices` contains ~128,000 records *(secondary)*.
* **Updates:** Varies by dataset from 5-minute intervals to hourly updates.
* **Full Load Feasibility:** High, executable by iterating through historical date windows.
* **Incremental Ingestion (Class B):** Query parameters support `start`, `end`, sorting, and offset pagination.
* **Related Data and Analytics:** Modeling wholesale price volatility against wind generation output, forecasting demand ramps, and interconnector flow analysis.
* **Why Overlooked:** Domain geographic focus restricted to Denmark and neighboring European bidding zones.
* **Challenges & Caveats:** Dataset deprecations and schema migrations (e.g., secondary reports indicate 22 datasets are retired yet still return HTTP 200, and `Elspotprices` halted updates in late 2025, being superseded by new bidding zone tables).

---

### 10. CMS Open Payments
* **Domain:** Healthcare Operations & Regulatory Transparency
* **Source and Access:** Centers for Medicare & Medicaid Services (CMS).
  * Datastore API: `openpaymentsdata.cms.gov/api/1/datastore/query/<id>/0`
  * Program Documentation: [cms.gov/OpenPayments/Data](https://www.cms.gov/OpenPayments/Data)
  * Data Dictionary: [open-payments-methodology-data-dictionary.pdf](https://www.cms.gov/files/document/open-payments-methodology-data-dictionary-document-january-2026.pdf)
* **Content:** Financial transfers of value from pharmaceutical and medical device manufacturers to covered physicians and teaching hospitals, covering general payments (consulting, speaking, gifts, travel), research grants, and physician ownership stakes.
* **Coverage and Volume:** Individual annual releases contain >15 million general payment transactions across 90+ attribute columns *(secondary)*, totaling over 80 million historical rows.
* **Updates:** Annual public data release every June, followed by restatement refreshes of the prior six program years.
* **Full Load Feasibility:** High, via direct annual CSV/ZIP archive downloads.
* **Incremental Ingestion (Class A Change Tracking, Coarse Cadence):** Every record in the refreshed publication is explicitly categorized with a Change Type value: `NEW`, `ADD`, `CHANGED`, or `UNCHANGED` relative to the previous publication vintage. A dedicated deleted-records table tracks transactions removed from earlier years.
* **Related Data and Analytics:** Industry payment concentration, physician prescribing correlations (when joined with Medicare Part D), and specialty consulting trends.
* **Why Overlooked:** Commonly studied in academic health policy; rarely utilized in data engineering portfolios due to wide, denormalized schemas.
* **Challenges & Caveats:** Coarse annual release cadence requires simulating intra-year ingestion for real-time demos; wide 90+ column schema demands careful Silver-layer normalization.

---

### 11. ClinicalTrials.gov
* **Domain:** Biomedical Research & Clinical Trial Registries
* **Source and Access:** U.S. National Library of Medicine.
  * API Base: [clinicaltrials.gov/api/v2/studies](https://clinicaltrials.gov/api/v2/studies)
  * Relational Mirror: CTTI AACT Database ([aact.ctti-clinicaltrials.org](https://aact.ctti-clinicaltrials.org))
* **Content:** Deeply nested JSON study records covering clinical protocols, trial eligibility criteria, participant demographics, study arms, drug/device interventions, adverse event outcomes, and sponsor metadata.
* **Coverage and Volume:** 570,000+ registered clinical trials averaging ~17 KB per study payload. Total volume is ~10–20 GB of dense hierarchical JSON.
* **Updates:** Continuous real-time updates as trial investigators modify study parameters.
* **Full Load Feasibility:** High, downloadable via monolithic XML/JSON bulk files or paginated API calls (up to 1,000 records per page).
* **Incremental Ingestion (Class B):** API provides high-watermark filtering via `LastUpdatePostDate`. Explicit delete feed: *(not verified)*. Upstream updates may experience a brief operational lag relative to sponsor actions.
* **Related Data and Analytics:** Trial phase progression tracking, drug repurposing pipelines, and trial attrition analytics. Study lifecycle status transitions (e.g., `Not yet recruiting` $\to$ `Recruiting` $\to$ `Active, not recruiting` $\to$ `Completed` / `Terminated`) form canonical SCD Type 2 dimensions.
* **Why Overlooked:** Heavily utilized in clinical bioinformatics; rarely leveraged in data platform portfolios.
* **Challenges & Caveats:** Deep JSON nesting (up to 6 levels of nested arrays/objects) requiring extensive relational flattening in Silver.

---

### 12. England Environment Agency Flood Monitoring
* **Domain:** Hydrology & Public Safety
* **Source and Access:** UK Environment Agency.
  * API Reference: [environment.data.gov.uk/flood-monitoring/doc/reference](https://environment.data.gov.uk/flood-monitoring/doc/reference)
  * Daily Archive: [environment.data.gov.uk/flood-monitoring/archive](https://environment.data.gov.uk/flood-monitoring/archive)
* **Content:** Real-time river stage levels, rainfall rates, groundwater telemetry, active flood warnings, and monitoring station metadata across ~5,500 observation sites in England.
* **Coverage and Volume:** Daily archive files span multiple years *(start date not verified)*; operational readings are logged at high frequency.
* **Updates:** New measurements publish every 15 minutes.
* **Full Load Feasibility:** High, via daily CSV archive bundles. The REST API is restricted to rolling 28-day historical windows.
* **Incremental Ingestion (Class B):** Due to upstream batching delays, official documentation recommends polling via the `since` parameter to capture all late-arriving measurements, alongside `startdate` and `enddate` parameters.
* **Related Data and Analytics:** Rainfall-to-river level response lag modeling, flood warning lead times, and station operational uptime analytics.
* **Why Overlooked:** Geographically limited to England; API retains an official "Beta" classification.
* **Challenges & Caveats:** Manages thousands of fragmented time series; station metadata occasionally drifts without notification.

---

### 13. Global Fishing Watch
* **Domain:** Maritime Ecology & Commercial Fishing Surveillance
* **Source and Access:** Global Fishing Watch.
  * API Portal: [globalfishingwatch.org/our-apis](https://globalfishingwatch.org/our-apis)
  * API Base: `gateway.api.globalfishingwatch.org/v3/` (Requires non-commercial Bearer token).
* **Content:** Apparent fishing effort telemetry derived from AIS tracking across ~70,000 commercial vessels, alongside vessel identity registries, vessel-to-vessel transshipment encounters, loitering events, and port visits.
* **Coverage and Volume:** Global ocean coverage over multiple years. Absolute row count: *(not verified)*.
* **Updates:** Datasets follow versioned releases (e.g., `fishing-effort:v4.0`), with dynamic aliases pointing to current models.
* **Full Load Feasibility:** API-centric; pre-packaged full bulk downloads: *(not verified)*.
* **Incremental Ingestion (Class B):** Supports date-range query filtering on event and effort layers. Row-level `updated_at`: *(not verified)*.
* **Related Data and Analytics:** Marine protected area enforcement, transshipment hotspot detection, and flags of convenience tracking.
* **Why Overlooked:** Requires developer registration, token authentication, and enforces non-commercial licensing constraints.
* **Challenges & Caveats:** Strict API quotas, handling algorithmic model version migrations, and non-commercial usage limitations.

---

### 14. openFDA
* **Domain:** Healthcare Regulation & Pharmacovigilance
* **Source and Access:** U.S. Food and Drug Administration.
  * API Base: [api.fda.gov/drug/event.json](https://api.fda.gov/drug/event.json)
  * Documentation: [open.fda.gov/apis/](https://open.fda.gov/apis/)
* **Content:** 28 distinct public API endpoints covering post-market drug and device adverse events, Structured Product Labels (SPL), National Drug Code (NDC) directories, recall enforcement reports, and medical device approvals.
* **Coverage and Volume:** Millions of adverse event case reports spanning several decades.
* **Updates:** Varies significantly by endpoint; device events are near real-time, while drug adverse events have experienced historical batch lags of 3–4 months.
* **Full Load Feasibility:** The REST API caps `skip` offsets at 25,000 records, requiring use of the `search_after` cursor or extracting bulk S3 downloads hosted on the portal.
* **Incremental Ingestion (Class B):** Queries support date-range bounding on `receiptdate` combined with ascending sort orders.
* **Rate Limits:** 240 requests/minute and 1,000 requests/day unauthenticated; 120,000 requests/day with a free developer API key.
* **Related Data and Analytics:** Drug adverse reaction signals, pharmaceutical recall clusters, and label change tracking.
* **Why Overlooked:** Well-known in regulatory informatics; less frequented by data platform builders due to API paging limits.
* **Challenges & Caveats:** Navigating 25,000-record offset limits, variable endpoint update lags, and semi-structured free-text clinical fields.

---

### 15. NASA FIRMS Active Fires
* **Domain:** Satellite Remote Sensing & Environmental Hazard Detection
* **Source and Access:** NASA Earthdata / LANCE.
  * API Endpoint: [firms.modaps.eosdis.nasa.gov/api/area/csv](https://firms.modaps.eosdis.nasa.gov/api/area/csv) (Requires free `MAP_KEY`).
* **Content:** Thermal anomaly and active fire detections derived from MODIS (Terra and Aqua) and VIIRS (Suomi NPP and NOAA-20) satellite instruments, including brightness temperature, fire radiative power (FRP), and detection confidence.
* **Coverage and Volume:** Multi-decadal archives dating back to 2000 (MODIS) and 2012 (VIIRS).
* **Updates:** Continuous satellite overpasses. Real-Time (URT/RT) detections are subsequently replaced by definitive Near-Real-Time (NRT) and standard science quality products.
* **Full Load Feasibility:** High, via pre-packaged annual global country CSV archives.
* **Incremental Ingestion (Class B):** API permits date and day-range queries (1–10 days per call). As NRT feeds overwrite raw provisional detections, pipelines must reconcile replaced observations lacking stable physical entity IDs.
* **Related Data and Analytics:** Wildfire perimeter tracking, smoke emissions correlation, and spatial joins to weather and land-cover layers.
* **Why Overlooked:** Typically consumed as a direct GIS map layer rather than piped through enterprise ETL infrastructure.
* **Challenges & Caveats:** Point-detection presence data lacking relational depth or foreign keys to business entities.

---

### 16. USDA FAS: PSD, Export Sales and Trade
* **Domain:** Agricultural Economics & Commodity Trade
* **Source and Access:** USDA Foreign Agricultural Service.
  * Open Data Portal: [apps.fas.usda.gov/opendataweb/home](https://apps.fas.usda.gov/opendataweb/home)
  * PSD Online: [apps.fas.usda.gov/psdonline](https://apps.fas.usda.gov/psdonline)
* **Content:** Three primary commodity databases: Production, Supply, and Distribution (PSD), Weekly Export Sales reporting, and Global Agricultural Trade System statistics.
* **Coverage and Volume:** PSD histories extend back to 1960; Export Sales records date back to 1998. Total data volume is relatively compact.
* **Updates:** PSD publishes monthly forecasts by commodity; Export Sales updates weekly on Thursdays.
* **Full Load Feasibility:** High, achievable via API extracts filtered by commodity code and year.
* **Incremental Ingestion (Class C for PSD, Class B for Export Sales):** The API surfaces publication release dates. For PSD, each new monthly release overwrites previous forecasts across entire historical balance sheets without row-level delta flags, necessitating snapshot diffing to track forecast revisions over time.
* **Related Data and Analytics:** Commodity ending stocks, export commitments versus actual shipments, and supply deficit modeling.
* **Why Overlooked:** Highly specialized within agricultural trade circles.
* **Challenges & Caveats:** Compact volume; legacy REST endpoints have experienced intermittent key-validation issues, requiring fallback to SOAP or bulk endpoints.

---

### 17. MBTA Rapid-Transit Performance (Boston)
* **Domain:** Public Transit & Urban Operations
* **Source and Access:** Massachusetts Bay Transportation Authority / MassDOT.
  * Portal: [mbta.com/developers/mbta-performance-data](https://www.mbta.com/developers/mbta-performance-data)
* **Content:** Historical heavy-rail and light-rail vehicle arrival/departure events, scheduled vs. actual travel times, train headways, and dwell times across the MBTA subway network. Includes daily Apache Parquet logs via the LAMP (Lightweight Architecture for Monitoring Performance) pipeline.
* **Coverage and Volume:** Event-level operational data from 2016 to present. Row count: *(not verified)*.
* **Updates:** Daily (LAMP Parquet dumps) and monthly (aggregated CSV releases).
* **Full Load Feasibility:** High, partitioned by day or calendar month.
* **Incremental Ingestion (Class B):** Daily service-date partitions without downstream CDC change indicators.
* **Related Data and Analytics:** Transit schedule adherence, peak-hour congestion bottlenecks, and train dwell-time patterns.
* **Why Overlooked:** Event-level transit data is much harder to clean and model than static GTFS schedules or monthly ridership totals.
* **Challenges & Caveats:** The legacy MBTA-Performance API was deprecated in May 2024; occasional missing dates in historical bus archives *(secondary)*.

---

### 18. NOAA Storm Events
* **Domain:** Severe Weather Impacts & Disaster Economics
* **Source and Access:** NOAA National Centers for Environmental Information (NCEI).
  * Bulk Archive: [ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/)
* **Content:** Annual gzip-compressed CSV files split into three relational entities: Storm Details, Storm Fatalities, and Storm Locations, linked via `EVENT_ID` and `EPISODE_ID`.
* **Coverage and Volume:** Spans 1950 to present. Highly accessible and open without authentication.
* **Updates:** Database refreshes with a 75 to 90 day lag following the conclusion of each observation month.
* **Full Load Feasibility:** High; all annual archives can be scripted directly via HTTP.
* **Incremental Ingestion (Class C):** Upstream files carry a build-date timestamp in the file naming convention (e.g., `c20260918.csv.gz`). When a historical record is updated, the entire annual archive file is rebuilt and re-uploaded, requiring downstream pipelines to download and state-diff the full annual partition.
* **Related Data and Analytics:** Property and crop damage loss estimation; joins directly with OpenFEMA flood claims by county FIPS code.
* **Why Overlooked / Low Ranking:** Extremely ubiquitous in beginner data science courses; lacks native streaming, change flags, or complex API capabilities. Retained here primarily as a secondary enrichment join.
* **Challenges & Caveats:** Text-encoded numeric damage values (e.g., `"2.50K"`, `"15.00M"`), 90-day reporting lag, and absence of row-level delta feeds.

---

## Final Recommendation & Strategic Assessment

### The Five Strongest Candidates

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Top 5 Overall Contenders                        │
├────────────────────┬──────────────────┬───────────────┬────────────────┤
│ Candidate          │ Domain           │ Incr. Class   │ Score (/40)    │
├────────────────────┼──────────────────┼───────────────┼────────────────┤
│ 1. USAspending.gov │ Federal Spending │ Class A       │ 38             │
│ 2. AEMO NEM        │ Energy Grid      │ Class B       │ 37             │
│ 3. OpenAlex        │ Bibliometrics    │ Class A       │ 36             │
│ 4. EPA CAMPD       │ Emissions/Energy │ Class B       │ 36             │
│ 5. Overture Maps   │ Geospatial       │ Class A       │ 36             │
└────────────────────┴──────────────────┴───────────────┴────────────────┘
```

1. **USAspending.gov:** Features native delta files containing an explicit `correction_delete_ind` flag. It is deeply relational across awards, transactions, subawards, recipients, and federal agencies, requiring no API key.
2. **AEMO NEM:** Features a thoroughly documented MMS data model, massive high-frequency time series, and an immutable `RRP`/`ROP` price-adjustment audit trail. It is completely file-based without REST overhead.
3. **OpenAlex:** Delivers first-class incremental synchronization via `updated_date` object storage partitions, paired with explicit merged and deleted ID crosswalks. It is deeply relational, open, and massive.
4. **EPA CAMPD:** Offers unique regulatory telemetry with hourly unit-level physical facts and slowly changing facility/owner dimensions. It provides high volume and requires only a free API key.
5. **Overture Maps:** Provides formal per-release changelogs with column-level modification arrays and globally stable GERS identifiers, representing the pinnacle of cloud-native GeoParquet engineering.

---

### Full and Incremental Loading Compared

| Dataset | Full Load Strategy | Incremental Mechanism | Incremental Class | Native Cadence |
| :--- | :--- | :--- | :---: | :--- |
| **USAspending.gov** | Full archive ZIPs by FY and agency; API custom download jobs | Dedicated monthly delta files with `correction_delete_ind` and delete feeds | **Class A** | Monthly (with daily ingest) |
| **AEMO NEM** | Daily and historical MMSDM archive files | High-frequency interval files; `settlementdate` high-watermark | **Class B** | 5-Minute / Daily |
| **OpenAlex** | Direct S3 bulk download (`--no-sign-request`) | `updated_date` object partitions with cumulative `deleted_ids.csv` | **Class A** | Public snapshot cadence |
| **EPA CAMPD** | Packaged bulk files via API / portal | API date-range filters and quarterly partition reconciliations | **Class B** | Quarterly |
| **Overture Maps** | Direct GeoParquet S3 sync by theme | Formal release changelogs detailing added, deleted, and modified features | **Class A** | Monthly |

---

### Strongest Overall Choice: USAspending.gov

USAspending.gov represents the ideal candidate for an enterprise-grade data engineering project for five decisive reasons:

1. **Comprehensive Format & Source Modality:** Supports every modern ingestion modality—REST APIs, bulk CSV archives, and full relational database dumps. Ingesting mixed formats is a genuine property of the data rather than an artificial simulation.
2. **Native CDC & Change Semantics:** Very few public datasets publish explicit record modifications, retrofits, and deletions. USAspending provides actual change-capture semantics (`correction_delete_ind` and separate deletion feeds), forcing pipelines to handle late-arriving and restated facts organically.
3. **True Slowly Changing Dimensions:** Parent recipient companies, subsidiary holding structures, and awarding agency hierarchies evolve continuously over time, providing realistic material for SCD Type 2 modeling.
4. **Executive Business Relevance:** Tracking federal expenditures across contractors, grants, states, and congressional districts represents a high-value economic activity dataset with immediate analytical significance.
5. **Unrestricted Open Access:** 100% public under the DATA Act—no subscription paywalls, no proprietary terms of service, and no brittle scraping scripts required.

> **Comparison to Conventional Tutorial Datasets:**  
> Standard portfolio datasets (NYC TLC Taxi trips, Kaggle retail transactions, CitiBike feeds) are static, single-grain exports lacking delete feeds, restatements, or upstream CDC metadata. As a result, incremental loading in those projects must be artificially manufactured. USAspending forces you to solve the exact problems encountered in enterprise production.

---

### Recommended Alternative Pairings

* **For High-Frequency Time Series & Power Systems:** Choose **AEMO NEM**.
* **For a Lightweight, Modern Maritime Pipeline:** Choose **IMF PortWatch**.
* **For a Compact, Multi-Source Relational Setup:** Combine **OpenFEMA** with **NOAA Storm Events** joined on county FIPS codes and dates.

---

### Unverified Items Checklist (For Live Pipeline Prototyping)

Prior to finalizing pipeline schemas, verify the following upstream implementation details:
* **USAspending.gov:** Inspect a live monthly Delta file to confirm active header column names and verify current uncompressed row counts.
* **AEMO NEM:** Confirm the earliest archive start date and verify the exact MMSDM monthly archive directory structure.
* **OpenAlex:** Verify the exact public refresh cadence for the free AWS S3 snapshot.
* **EPA CAMPD & CMS Open Payments:** Verify uncompressed row counts and confirm specific quarterly publication calendars.
* **OpenFEMA:** Test whether API server-side re-indexing resets the `lastRefresh` timestamp for unmodified historical rows.

