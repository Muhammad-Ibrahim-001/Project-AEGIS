import os

BASE_CSS = """
@page {
    size: A4;
    margin: 20mm 16mm 20mm 16mm;
    @bottom-right {
        content: counter(page);
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1E293B;
    line-height: 1.55;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
}
.cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 90vh;
    padding-top: 40px;
}
.cover-tag {
    font-size: 11pt;
    font-weight: 700;
    color: #0284C7;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}
.cover-title {
    font-size: 26pt;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.25;
    margin-bottom: 16px;
}
.cover-subtitle {
    font-size: 14pt;
    color: #475569;
    line-height: 1.4;
    margin-bottom: 35px;
}
.cover-divider {
    width: 80px;
    height: 5px;
    background-color: #0284C7;
    margin-bottom: 35px;
}
.cover-meta {
    font-size: 10.5pt;
    color: #334155;
    margin-top: 15px;
    border-left: 3px solid #CBD5E1;
    padding-left: 15px;
}
.cover-team-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 25px;
}
.cover-team-table th {
    background-color: #0F172A;
    color: #FFFFFF;
    text-align: left;
    padding: 8px 12px;
    font-size: 9.5pt;
}
.cover-team-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #E2E8F0;
    font-size: 9.5pt;
}
h1 {
    font-size: 18pt;
    font-weight: 800;
    color: #0F172A;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 6px;
    margin-top: 30px;
    page-break-after: avoid;
}
h2 {
    font-size: 13.5pt;
    font-weight: 700;
    color: #0369A1;
    margin-top: 22px;
    margin-bottom: 10px;
    page-break-after: avoid;
}
h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #0F172A;
    margin-top: 16px;
    margin-bottom: 8px;
    page-break-after: avoid;
}
p {
    margin-top: 0;
    margin-bottom: 12px;
    text-align: justify;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 9pt;
    page-break-inside: avoid;
}
th {
    background-color: #0F172A;
    color: #FFFFFF;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #0F172A;
}
td {
    padding: 7px 10px;
    border: 1px solid #CBD5E1;
    vertical-align: top;
}
tr:nth-child(even) {
    background-color: #F8FAFC;
}
.callout {
    background-color: #F0FDF4;
    border-left: 4px solid #059669;
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 0 4px 4px 0;
    page-break-inside: avoid;
}
.callout-title {
    font-weight: 700;
    color: #065F46;
    margin-bottom: 6px;
    font-size: 10pt;
}
.callout-amber {
    background-color: #FFFBEB;
    border-left: 4px solid #D97706;
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 0 4px 4px 0;
    page-break-inside: avoid;
}
.callout-amber .callout-title {
    color: #92400E;
}
.badge {
    display: inline-block;
    padding: 2px 7px;
    font-size: 7.5pt;
    font-weight: 700;
    border-radius: 4px;
    text-transform: uppercase;
}
.page-break {
    page-break-after: always;
}
.diagram-container {
    text-align: center;
    margin: 20px 0;
    page-break-inside: avoid;
}
.diagram-container img {
    max-width: 100%;
    height: auto;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.caption {
    font-size: 8.5pt;
    color: #64748B;
    font-style: italic;
    margin-top: 6px;
    text-align: center;
}
code {
    font-family: "Consolas", monospace;
    font-size: 8.5pt;
    background-color: #F1F5F9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0F172A;
}
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)

def generate_proposal_html():
    img_arch = os.path.join(SUBMISSION_DIR, "Architecture_Pipeline_Diagram.png").replace("\\", "/")
    img_schema = os.path.join(SUBMISSION_DIR, "Physical_Model_Diagram.png").replace("\\", "/")

    body = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Deliverable 1: Project Proposal & Design Specification</title>
<style>__BASE_CSS__</style>
</head>
<body>

<div class="cover-page">
    <div class="cover-tag">DL3004 Data Warehousing & Business Intelligence • Phase 1 Deliverable</div>
    <div class="cover-title">Project Proposal & Dimensional Architecture Blueprint</div>
    <div class="cover-subtitle">Integrated Analytics of U.S. Bulk Power Generation, Continuous Smokestack Air Emissions, and Synoptic Meteorology via an Enterprise Cloud Lakehouse</div>
    <div class="cover-divider"></div>
    <div class="cover-meta">
        <strong>Academic Course:</strong> DL3004 Data Warehousing & Business Intelligence (DWBI)<br>
        <strong>Institution:</strong> FAST National University of Computer & Emerging Sciences<br>
        <strong>Faculty / Instructor:</strong> Shahzeb Mubashar<br>
        <strong>Submission Phase:</strong> Phase 1: Business Analysis & Dimensional Design (30% Weight)<br>
        <strong>Submission Date:</strong> November 2026
    </div>
    
    <table class="cover-team-table">
        <thead>
            <tr>
                <th>Teammate Name</th>
                <th>Roll Number</th>
                <th>Work Package Ownership & Course Responsibilities</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Muhammad Ibrahim</strong></td>
                <td>24L-2602</td>
                <td><strong>WP1 Lead:</strong> Ingestion, Multi-Source Raw Landing & Bronze Lakehouse Architecture</td>
            </tr>
            <tr>
                <td><strong>Rai Fahad Sultan</strong></td>
                <td>24L-2509</td>
                <td><strong>WP2 Lead:</strong> Data Quality Rules Engine, Dead-Letter Quarantine & Silver Conformance</td>
            </tr>
            <tr>
                <td><strong>Muhammad Ayyan</strong></td>
                <td>24L-2568</td>
                <td><strong>WP3 Lead:</strong> Kimball Dimensional Modeling, Star Schema Bus Matrix & Gold Layer</td>
            </tr>
            <tr>
                <td><strong>Taha Imran</strong></td>
                <td>24L-2560</td>
                <td><strong>WP4 Lead:</strong> Analytical OLAP Engineering, Power BI DirectQuery Dashboard & Tuning</td>
            </tr>
        </tbody>
    </table>
</div>

<h1>1. Executive Summary & Problem Formulation</h1>
<p>
Modern electric power systems generate vast amounts of public telemetry reflecting generation dispatch, thermal efficiency, smokestack air pollution, and ambient weather. However, in the United States, this information is fragmented across three independent federal agencies:
</p>
<ul>
    <li><strong>U.S. Energy Information Administration (EIA):</strong> Publishes generator asset inventories (Form EIA-860), monthly facility fuel consumption and generation (Form EIA-923), and hourly regional balancing authority demand and fuel dispatch mix (Form EIA-930).</li>
    <li><strong>U.S. Environmental Protection Agency (EPA):</strong> Publishes continuous emission monitoring system (CEMS) hourly observations of gross electrical load, heat input, and emissions (CO2, SO2, NOx) via Clean Air Markets Program Data (CAMPD), alongside boiler-to-generator crosswalk mappings.</li>
    <li><strong>National Oceanic & Atmospheric Administration (NOAA):</strong> Publishes hourly surface meteorology observations (temperature, wind velocity, precipitation, dew point) via the Integrated Surface Database (ISD).</li>
</ul>
<p>
Each agency operates under distinct temporal grains (clock hour, monthly summary, annual inventory), distinct file formats (multi-tab Excel workbooks, nested JSON APIs, fixed-width flat files, bulk CSVs), and divergent missing-value conventions (e.g., text sentinels <code>"."</code>, <code>"NM"</code>, <code>"*"</code>, and integer sentinel <code>-9999</code>). 
</p>
<p>
Without a unified dimensional data warehouse, environmental compliance officers, utility operators, and policy analysts cannot perform cross-domain analytics—such as evaluating how summer heatwaves increase thermal generator heat rates and carbon intensity, or determining whether offline power plants report valid negative net generation during station maintenance. This project designs and implements an enterprise-grade cloud data lakehouse on Databricks Serverless Compute (Photon Engine) and Delta Lake with Power BI DirectQuery reporting to solve these fundamental business problems.
</p>

<div class="callout">
    <div class="callout-title">Domain Mission Statement</div>
    To engineer a unified Kimball dimensional star schema integrating 6 federal open datasets, resolving complex entity crosswalks, standardizing thermodynamic units, enforcing strict data quality quarantine boundaries, and delivering executive decision-support dashboards with sub-second OLAP responsiveness.
</div>

<h1>2. Multi-Source Ingestion Inventory</h1>
<p>
The lakehouse architecture ingests microdata from six authoritative federal sources:
</p>
<table>
    <thead>
        <tr>
            <th>Source System</th>
            <th>Federal Agency</th>
            <th>Extraction Format</th>
            <th>Native Temporal Grain</th>
            <th>Primary Business Content</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>EIA-860</strong></td>
            <td>U.S. EIA</td>
            <td>Multi-Tab Excel (.xlsx)</td>
            <td>Annual per Generator</td>
            <td>Utility name, plant coordinates, prime mover, nameplate capacity MW, operating status (OP, SB, RE).</td>
        </tr>
        <tr>
            <td><strong>EIA-860 (6.1)</strong></td>
            <td>U.S. EIA</td>
            <td>Multi-Tab Excel (.xlsx)</td>
            <td>Annual Association</td>
            <td>Boiler-to-generator environmental associations establishing bipartite facility graph topology.</td>
        </tr>
        <tr>
            <td><strong>EIA-923</strong></td>
            <td>U.S. EIA</td>
            <td>Multi-Tab Excel (.xlsx)</td>
            <td>Monthly per Plant & Fuel</td>
            <td>Monthly net generation (MWh), fuel consumed (MMBtu & physical), delivered fuel costs, and ending stocks.</td>
        </tr>
        <tr>
            <td><strong>EPA CAMPD</strong></td>
            <td>U.S. EPA</td>
            <td>Bulk CSV / REST API</td>
            <td>Hourly per CEMS Unit</td>
            <td>Gross electrical load (MW), heat input (MMBtu), and mass air emissions (SO2, NOx, CO2).</td>
        </tr>
        <tr>
            <td><strong>EPA Crosswalk</strong></td>
            <td>EPA / EIA</td>
            <td>CSV Bridge Table</td>
            <td>Boiler-to-Generator Link</td>
            <td>Cross-agency identifier mapping linking EPA CEMS unit/stack IDs to EIA generator IDs.</td>
        </tr>
        <tr>
            <td><strong>NOAA ISD</strong></td>
            <td>NOAA NCEI</td>
            <td>Fixed-Width / CSV</td>
            <td>Hourly per Weather Station</td>
            <td>Synoptic surface temperature (°C), dew point, wind speed (m/s), and atmospheric pressure.</td>
        </tr>
        <tr>
            <td><strong>EIA-930</strong></td>
            <td>U.S. EIA</td>
            <td>REST JSON API / CSV</td>
            <td>Hourly per Grid Operator</td>
            <td>Real-time regional electric demand (MW), day-ahead forecast, net generation mix by fuel, and interchange.</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<h1>3. Multi-Layer Medallion Lakehouse Architecture</h1>
<p>
The system implements a rigorous Medallion Lakehouse architecture orchestrated using Databricks Serverless Compute (Python 3.12 / Photon engine) and Delta Lake transaction tables under Unity Catalog (<code>dwbi_catalog</code>):
</p>

<div class="diagram-container">
    <img src="file:///__IMG_ARCH__" alt="Medallion Pipeline Architecture">
    <div class="caption">Figure 1: End-to-End Medallion Lakehouse Architecture (Bronze Landing → Quarantine Engine → Silver Conformance → Kimball Gold Warehouse → Gold Marts & Power BI DirectQuery)</div>
</div>

<h3>Architectural Layer Specifications:</h3>
<ul>
    <li><strong>Bronze Staging (<code>dwbi_catalog.bronze_staging</code>):</strong> Append-only landing layer preserving raw data with all columns ingested as string/VARCHAR types to guarantee zero ingestion loss. Each record is stamped with <code>batch_id</code> (UUID), <code>ingested_at</code> (timestamp), and <code>source_file</code>. Programmatic header discovery automatically detects shifted Excel headers (Row 2 in EIA-860 vs. Row 6 in EIA-923).</li>
    <li><strong>Data Quality & Dead-Letter Quarantine (<code>dwbi_catalog.quarantine</code>):</strong> Automated validation engine evaluating completeness, domain accuracy, and referential integrity. Rows with uncoerced sentinels, thermodynamic boundary violations, or orphan keys are diverted to <code>quarantine.rejected_records</code> with raw JSON payloads and diagnostic failure reasons.</li>
    <li><strong>Silver Conformed (<code>dwbi_catalog.silver_conformed</code>):</strong> Cleansed, typed, and conformed layer. Standardizes energy units (MWh, MMBtu, lbs, short tons, °C), performs geospatial Haversine nearest-neighbor joins (&le; 50 km, &plusmn; 60 min) between plants and NOAA stations, and tracks generator asset status transitions via Slowly Changing Dimensions (SCD Type 2).</li>
    <li><strong>Gold Dimensional Warehouse (<code>dwbi_catalog.gold_warehouse</code>):</strong> Enterprise Kimball Star Schema consisting of 5 conformed dimensions and 3 multi-grain fact tables, utilizing Delta Lake Liquid Clustering (<code>CLUSTER BY</code>) for sub-second query performance.</li>
    <li><strong>Gold Marts & Reporting Views (<code>dwbi_catalog.gold_marts</code>):</strong> Business-facing pre-aggregated reporting views optimized for Microsoft Power BI Desktop DirectQuery connectivity.</li>
</ul>

<div class="page-break"></div>

<h1>4. Dimensional Star Schema & Kimball Bus Matrix</h1>
<p>
The Gold dimensional warehouse is architected around Kimball's four-step dimensional design method: selecting the business process, declaring the grain, identifying the dimensions, and identifying the numeric facts.
</p>

<div class="diagram-container">
    <img src="file:///__IMG_SCHEMA__" alt="Physical Kimball Star Schema">
    <div class="caption">Figure 2: Gold Dimensional Warehouse Star Schema (5 Conformed Dimensions & 3 Multi-Grain Fact Archetypes)</div>
</div>

<h3>Dimensional Entity Catalog:</h3>
<ol>
    <li><strong><code>dim_date</code> (Conformed Calendar Dimension):</strong> Generated via script covering 2020–2026. Smart integer primary key <code>date_key</code> in <code>YYYYMMDD</code> format, calendar hierarchies (Year, Quarter, Month, Day), day names, and weekend flags.</li>
    <li><strong><code>dim_plant</code> (Master Facility Dimension):</strong> Surrogate primary key <code>plant_key</code> (BIGINT IDENTITY), natural business key <code>orispl_code</code> (EIA plant code), facility name, utility parent, coordinates (latitude/longitude), state, county, balancing authority code, and cogeneration flag.</li>
    <li><strong><code>dim_generator</code> (Asset Lifecycle Outrigger - SCD Type 2):</strong> Surrogate primary key <code>generator_key</code>, foreign key to <code>orispl_code</code>, generator ID, prime mover code, energy source, rated nameplate capacity MW, operating status (<code>OP</code>=Operating, <code>SB</code>=Standby, <code>RE</code>=Retired), <code>row_effective_date</code>, <code>row_expiration_date</code>, and <code>is_current</code> flag.</li>
    <li><strong><code>dim_balancing_authority</code> (Regional Grid Operator Dimension):</strong> Surrogate primary key <code>ba_key</code>, natural key <code>ba_code</code> (e.g., PJM, CISO, MISO, ERCOT), operator name, interconnection territory, and active flag.</li>
    <li><strong><code>dim_weather_station</code> (Synoptic Meteorological Station Dimension):</strong> Surrogate primary key <code>station_key</code>, natural key <code>station_id</code> (composite USAF-WBAN), station name, state, latitude, longitude, and elevation meters.</li>
</ol>

<h3>Three Multi-Grain Fact Tables (Kimball Archetypes):</h3>
<ol>
    <li><strong><code>fact_hourly_emissions_weather</code> (Transactional Fact):</strong>
        <br><em>Grain:</em> One row per generating unit per clock hour.
        <br><em>Optimization:</em> Liquid clustered via <code>CLUSTER BY (date_key, plant_key)</code>.
        <br><em>Measures:</em> <code>gross_load_mw</code>, <code>heat_input_mmbtu</code>, <code>so2_mass_lbs</code>, <code>nox_mass_lbs</code>, <code>co2_mass_tons</code>, <code>ambient_temp_celsius</code>, <code>wind_speed_mps</code>, <code>weather_distance_km</code>.
    </li>
    <li><strong><code>fact_monthly_plant_operations</code> (Periodic Snapshot Fact):</strong>
        <br><em>Grain:</em> One row per plant, prime mover, and energy source category per calendar month.
        <br><em>Measures:</em> <code>net_generation_mwh</code> (supports valid negative net generation during station maintenance outages), <code>fuel_consumed_mmbtu</code>, <code>fuel_consumed_physical</code>, <code>avg_heat_rate_btu_kwh</code>, <code>delivered_fuel_cost_per_mmbtu</code>, <code>ending_fuel_stock_physical</code>.
    </li>
    <li><strong><code>fact_regional_grid_demand</code> (Aggregate Grid Fact):</strong>
        <br><em>Grain:</em> One row per balancing authority per clock hour.
        <br><em>Measures:</em> <code>demand_mw</code>, <code>demand_forecast_mw</code>, <code>net_gen_coal_mw</code>, <code>net_gen_gas_mw</code>, <code>net_gen_nuclear_mw</code>, <code>net_gen_hydro_mw</code>, <code>net_gen_wind_mw</code>, <code>net_gen_solar_mw</code>, <code>net_interchange_mw</code>.
    </li>
</ol>

<div class="page-break"></div>

<h1>5. Data Quality, Governance & Defensive Engineering</h1>
<p>
To ensure production-grade data warehouse trustworthiness, the design incorporates six critical defensive engineering rules:
</p>
<div class="callout-amber">
    <div class="callout-title">Critical Data Engineering & Validation Rules</div>
    <ol style="margin-top: 6px; padding-left: 20px;">
        <li><strong>Programmatic Shifting Header Detection:</strong> Automatically scans for anchor strings (<code>"Plant Code"</code> / <code>"Plant Id"</code>) to bypass shifting header rows across federal Excel releases.</li>
        <li><strong>Missing Value Sentinel Coercion & ANSI Mode Compliance:</strong> Federal sentinels (<code>"."</code>, <code>"NM"</code>, <code>"*"</code>, <code>""</code>) and NOAA integer <code>-9999</code> are converted to <code>NULL</code> using <code>TRY_CAST()</code> to avoid runtime aborts under Databricks SQL ANSI mode.</li>
        <li><strong>Preservation of Negative Net Generation:</strong> Offline power plants drawing station auxiliary power during maintenance legitimately report negative net generation in EIA-923. These records are preserved and flagged, never discarded.</li>
        <li><strong>Thermodynamic Heat Rate Validation:</strong> Heat rates (Heat Rate = (Fuel Input MMBtu * 1,000,000) / (Net Generation MWh * 1,000)) are evaluated against strict physical bounds:
            <br>• Combined Cycle: 5,000 to 14,000 Btu/kWh
            <br>• Coal Steam Turbines: 8,500 to 18,000 Btu/kWh
            <br>• Gas Turbines (Peakers): 9,000 to 22,000 Btu/kWh
            <br>Anomalies violating thermodynamic physics are routed to <code>quarantine.rejected_records</code>.</li>
        <li><strong>Physical Auxiliary Load Reconciliation:</strong> Enforces physical conservation: Net Generation (EIA-923) &le; Gross Generation (EPA CAMPD), validating auxiliary station loads within the expected 3% to 14% band.</li>
        <li><strong>Delta Lake Identity Column Merge Safeguards:</strong> SCD Type 2 merges explicitly use <code>UPDATE SET * EXCEPT (generator_key)</code> to avoid modifying Delta identity surrogate keys.</li>
    </ol>
</div>

<h1>6. Analytics, OLAP & Power BI Roadmap</h1>
<p>
The warehouse directly enables high-performance OLAP analytics and executive business intelligence:
</p>
<ul>
    <li><strong>Advanced SQL Analytics:</strong> Multi-dimensional aggregations utilizing <code>ROLLUP</code> (e.g., regional demand subtotals across Year, Quarter, Month, and Balancing Authority), <code>CUBE</code> (cross-tabulated net generation and heat rates across State, Prime Mover, and Fuel Source), and window ranking functions (<code>DENSE_RANK()</code>, <code>LAG()</code> for month-over-month ramping).</li>
    <li><strong>Gold Reporting Views:</strong>
        <br>• <code>vw_emissions_intensity</code>: Evaluates hourly carbon intensity (CO2 Tons/MWh) and toxic emissions vs. ambient temperature.
        <br>• <code>vw_plant_performance</code>: Tracks monthly fuel consumption, delivered fuel cost per MMBtu, and heat rate efficiency.
        <br>• <code>vw_monthly_generation</code>: Analyzes regional renewable energy penetration (wind + solar share) and net interchange dependency.
    </li>
    <li><strong>Microsoft Power BI Desktop DirectQuery Dashboard:</strong>
        <br>• <strong>Page 1: Executive Overview:</strong> High-level KPIs (Total Generation MWh, Total CO2 Tons, Fleet Carbon Intensity, Renewable Share %) and regional generation mix trends.
        <br>• <strong>Page 2: Detailed Operational & Weather Analysis:</strong> Interactive scatter plots of Heat Rate vs. Surface Air Temperature, facility emissions rankings, and fuel price volatility.
        <br>• <strong>Page 3: Grid Reliability & Strategic Decision Page:</strong> Real-time grid stress indicators, thermal peaker ramp-up requirements during renewable drop-offs, and an actionable executive recommendation.
    </li>
</ul>

<div class="page-break"></div>

<h1>7. Project Execution Plan & Risk Management</h1>
<p>
The project adheres to an 8-week collaborative execution model mapped against the DL3004 course milestones:
</p>
<table>
    <thead>
        <tr>
            <th>Phase & Timeline</th>
            <th>Weight</th>
            <th>Primary Deliverables & Milestones</th>
            <th>Responsible Leads</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Phase 1: Design</strong><br>(Weeks 1–3)</td>
            <td><strong>30%</strong></td>
            <td>Business questions, multi-source inventory, medallion architecture blueprint, conceptual/logical/physical models, data dictionary, execution roadmap.</td>
            <td>All 4 Team Members<br>(WP1, WP2, WP3, WP4)</td>
        </tr>
        <tr>
            <td><strong>Phase 2: Implementation</strong><br>(Weeks 4–6)</td>
            <td><strong>40%</strong></td>
            <td>Unity Catalog schemas, Bronze ingestion pipelines, data quality quarantine rules, Silver conformed transforms, SCD Type 2 merge logic, surrogate-key Gold fact loading (&gt;10,000 fact rows, &gt;100 dim rows).</td>
            <td>Muhammad Ibrahim (WP1)<br>Rai Fahad Sultan (WP2)<br>Muhammad Ayyan (WP3)</td>
        </tr>
        <tr>
            <td><strong>Phase 3: Analytics & BI</strong><br>(Weeks 7–8)</td>
            <td><strong>30%</strong></td>
            <td>OLAP SQL queries (<code>ROLLUP</code>, <code>CUBE</code>), query performance optimization (Liquid Clustering & <code>EXPLAIN</code> plans), 3-page Power BI DirectQuery dashboard, decision report.</td>
            <td>Taha Imran (WP4)<br>All Team Members</td>
        </tr>
    </tbody>
</table>

<h3>Risk Mitigation Matrix:</h3>
<table>
    <thead>
        <tr>
            <th>Identified Technical Risk</th>
            <th>Potential Impact</th>
            <th>Architectural Mitigation Strategy</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Shifting Excel Header Positions</td>
            <td>Pipeline parse aborts on raw ingestion</td>
            <td>Dynamic header detection scanning for anchor strings (<code>"Plant Code"</code> / <code>"Plant Id"</code>).</td>
        </tr>
        <tr>
            <td>String Sentinels in Numeric Fields</td>
            <td>ANSI SQL cast exceptions aborting loads</td>
            <td>Safe coercion via <code>TRY_CAST()</code> in Silver transformations; unparsable rows routed to quarantine.</td>
        </tr>
        <tr>
            <td>Complex Boiler-to-Generator Topology</td>
            <td>Cartesian product row explosion</td>
            <td>Bipartite graph modeling in Silver crosswalk mapping; row count validation before and after joins.</td>
        </tr>
        <tr>
            <td>Large Data Volume Local Bottlenecks</td>
            <td>Local out-of-memory crashes</td>
            <td>Databricks Serverless Cloud Lakehouse execution; Photon engine vectorized execution; bounded date filters for local tests.</td>
        </tr>
        <tr>
            <td>Repository Security Breaches</td>
            <td>Compromised credentials in Git</td>
            <td>Strict zero-credential policy; OAuth U2M and environment-variable token management; <code>.databrickscfg</code> exclusion.</td>
        </tr>
    </tbody>
</table>

<h1>8. Academic References</h1>
<ul>
    <li>Kimball, R., & Ross, M. (2013). <em>The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling</em> (3rd ed.). John Wiley & Sons.</li>
    <li>National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Information (NCEI). (2024). <em>Integrated Surface Database (ISD)</em>. NOAA. https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database</li>
    <li>U.S. Energy Information Administration (EIA). (2024). <em>Form EIA-860: Annual Electric Generator Report</em>. U.S. Department of Energy. https://www.eia.gov/electricity/data/eia860/</li>
    <li>U.S. Energy Information Administration (EIA). (2024). <em>Form EIA-923: Power Plant Operations Report</em>. U.S. Department of Energy. https://www.eia.gov/electricity/data/eia923/</li>
    <li>U.S. Energy Information Administration (EIA). (2024). <em>Form EIA-930: Hourly Electric Grid Monitor</em>. U.S. Department of Energy. https://www.eia.gov/electricity/gridmonitor/</li>
    <li>U.S. Environmental Protection Agency (EPA). (2024). <em>Clean Air Markets Program Data (CAMPD)</em>. U.S. EPA. https://campd.epa.gov/</li>
    <li>U.S. Environmental Protection Agency (EPA). (2024). <em>Power Sector Data Crosswalk</em>. U.S. EPA. https://www.epa.gov/power-sector/power-sector-data-crosswalk</li>
</ul>

</body>
</html>
"""
    html = body.replace("__BASE_CSS__", BASE_CSS).replace("__IMG_ARCH__", img_arch).replace("__IMG_SCHEMA__", img_schema)
    output_html = os.path.join(SCRIPT_DIR, "01_Project_Proposal.html")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {output_html}")

if __name__ == "__main__":
    generate_proposal_html()
