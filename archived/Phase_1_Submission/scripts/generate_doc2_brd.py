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
    font-size: 13.5pt;
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
    font-size: 17pt;
    font-weight: 800;
    color: #0F172A;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 6px;
    margin-top: 30px;
    page-break-after: avoid;
}
h2 {
    font-size: 13pt;
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
.req-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0284C7;
    padding: 10px 14px;
    margin-bottom: 12px;
    border-radius: 0 4px 4px 0;
    page-break-inside: avoid;
}
.req-header {
    display: flex;
    justify-content: space-between;
    font-weight: 700;
    color: #0F172A;
    font-size: 9.5pt;
    margin-bottom: 4px;
}
.req-desc {
    font-size: 9pt;
    color: #334155;
    margin: 0;
}
.page-break {
    page-break-after: always;
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

def generate_brd_html():
    body = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Deliverable 2: Business Requirements Document</title>
<style>__BASE_CSS__</style>
</head>
<body>

<div class="cover-page">
    <div class="cover-tag">DL3004 Data Warehousing & Business Intelligence • Phase 1 Deliverable</div>
    <div class="cover-title">Business Requirements Document (BRD) & System Specification</div>
    <div class="cover-subtitle">Enterprise Functional, Non-Functional, Data Governance, and Quality Requirements for U.S. Bulk Power Generation, Emissions, and Weather Lakehouse</div>
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

<h1>1. Business Context & Strategic Drivers</h1>
<p>
The U.S. commercial electricity sector faces unprecedented operational scrutiny driven by clean energy transition mandates, regional grid reliability risks during extreme meteorological events, and strict smokestack emissions compliance standards. To effectively manage assets and ensure grid balance, stakeholders must synthesize massive volumes of disjointed data across three federal monitoring bodies: EIA, EPA, and NOAA.
</p>
<p>
Currently, organizations suffer from data silos where environmental data resides in EPA CEMS repositories, generation accounting is locked in monthly EIA filings, grid balancing telemetry is managed via REST endpoints, and surface weather is maintained in NOAA flat files. This fragmentation forces analysts to perform ad-hoc, error-prone manual transformations that cannot scale and fail to capture historical asset changes.
</p>

<h3>Core Strategic Objectives:</h3>
<ul>
    <li><strong>Regulatory Environmental Compliance:</strong> Establish automated tracking of hourly mass emissions (CO2, SO2, NOx) and carbon intensity (tons/MWh) by plant, prime mover, and state.</li>
    <li><strong>Grid Reliability & Climate Resilience:</strong> Correlate peak electrical demand and generator heat rates against severe heatwaves and winter freezes to anticipate reserve margin shortages.</li>
    <li><strong>Thermodynamic Efficiency & Fuel Optimization:</strong> Monitor heat rate degradation over time, evaluating fuel-switching economics (coal vs. gas) based on delivered fuel pricing.</li>
    <li><strong>Asset Lifecycle Tracking:</strong> Maintain comprehensive historical audit trails of power plant unit commissions, standby events, and retirements using Kimball Slowly Changing Dimensions (SCD Type 2).</li>
</ul>

<h1>2. Stakeholder Profiles & User Personas</h1>
<table>
    <thead>
        <tr>
            <th>Persona / Role</th>
            <th>Primary Business Responsibility</th>
            <th>Critical Analytical Questions Answered</th>
            <th>Primary Analytical Needs</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Grid Reliability Engineer</strong><br><em>Operations Planning</em></td>
            <td>Maintains regional transmission balance, evaluates day-ahead vs. real-time demand, and oversees peaking capacity dispatch.</td>
            <td>Which balancing authorities experience the highest peak demand stress? How rapidly do thermal peakers ramp up when renewables drop?</td>
            <td>Hourly aggregate grid telemetry, demand vs. forecast delta, net generation mix by fuel, and regional interchange flows.</td>
        </tr>
        <tr>
            <td><strong>Environmental Compliance Officer</strong><br><em>Regulatory Affairs</em></td>
            <td>Ensures fleet adherence to Clean Air Act caps, regional ozone season budgets, and state emissions limits.</td>
            <td>Which facilities produce the highest emissions per gross MW? Which units violate thermodynamic heat rate or emissions thresholds?</td>
            <td>Unit-level hourly CEMS continuous stack monitoring, mass SO2/NOx/CO2, and carbon intensity metrics.</td>
        </tr>
        <tr>
            <td><strong>Plant Operations & Fuel Manager</strong><br><em>Generation Asset Lead</em></td>
            <td>Oversees thermal boiler efficiency, manages coal/gas fuel stockpiles, and analyzes station service power draws.</td>
            <td>What are the operating heat rates across turbine technologies? How often do offline plants experience negative net generation?</td>
            <td>Monthly plant generation accounting, heat rates, delivered fuel cost per MMBtu, and physical stockpile balances.</td>
        </tr>
        <tr>
            <td><strong>Executive Leadership</strong><br><em>Chief Operating Officer / VP Strategy</em></td>
            <td>Drives capital allocation, decarbonization transition roadmaps, and plant retirement timelines.</td>
            <td>What is the fleet-wide renewable penetration percentage? Which aging fossil units should be retired first?</td>
            <td>Executive Power BI KPI summary dashboards, regional choropleth maps, and capacity transition waterfall charts.</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<h1>3. System Scope & Boundaries</h1>
<h3>3.1 In-Scope Capabilities:</h3>
<ul>
    <li>Ingestion of 6 federal data sources across 4 distinct file formats (multi-tab Excel workbooks, bulk CSV, fixed-width text, REST JSON).</li>
    <li>Dynamic header discovery accommodating shifting header rows across federal release years.</li>
    <li>End-to-end Medallion Lakehouse implementation under Unity Catalog (<code>dwbi_catalog</code>) on Databricks Serverless Compute.</li>
    <li>Automated data quality validation engine routing corrupted or sentinel-laden records to <code>quarantine.rejected_records</code>.</li>
    <li>Geospatial Haversine nearest-station matching (&le; 50 km, &plusmn; 60 min) linking surface weather to generation facilities.</li>
    <li>SCD Type 2 dimension tracking generator operating status changes with full validity intervals.</li>
    <li>Surrogate-key dimensional star schema hosting 5 conformed dimensions and 3 multi-grain fact tables (&gt;10,000 fact rows, &gt;100 dimension rows).</li>
    <li>OLAP analytical SQL (<code>ROLLUP</code>, <code>CUBE</code>, window functions) and 3-page Microsoft Power BI Desktop DirectQuery dashboard.</li>
</ul>

<h3>3.2 Out-of-Scope Capabilities:</h3>
<ul>
    <li>Sub-second SCADA real-time grid frequency stabilization (frequency regulation operates at the 4-second grain).</li>
    <li>FERC Form 1 comprehensive financial ledger auditing (evaluated during research phase, deemed non-dimensional).</li>
    <li>Machine learning predictive load forecasting (Phase 1–3 focus strictly on descriptive, diagnostic, and decision-support DWBI).</li>
</ul>

<h1>4. Functional Requirements (FR)</h1>

<div class="req-box">
    <div class="req-header"><span>FR-01: Multi-Source Raw Ingestion</span><span class="badge badge-blue">Mandatory</span></div>
    <div class="req-desc">The ingestion subsystem must extract data from EIA-860, EIA-923, EIA-930, EPA CAMPD, EPA Crosswalk, and NOAA ISD, landing all raw fields as VARCHAR strings in Bronze staging tables with ingestion metadata (<code>batch_id</code>, <code>ingested_at</code>, <code>source_file</code>).</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-02: Programmatic Header Discovery</span><span class="badge badge-blue">Mandatory</span></div>
    <div class="req-desc">The ingestion pipeline must dynamically inspect Excel rows for anchor strings (e.g., <code>"Plant Code"</code> / <code>"Plant Id"</code>) to determine header rows dynamically, preventing ingestion failures caused by federal agency layout modifications.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-03: Type Conformance & Missing Value Coercion</span><span class="badge badge-blue">Mandatory</span></div>
    <div class="req-desc">The transformation pipeline must convert text sentinels (<code>"."</code>, <code>"NM"</code>, <code>"*"</code>, <code>""</code>) and NOAA integer sentinel <code>-9999</code> to SQL <code>NULL</code> using ANSI-compliant <code>TRY_CAST()</code> without query termination.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-04: Automated Dead-Letter Quarantine</span><span class="badge badge-green">Data Quality</span></div>
    <div class="req-desc">Records failing completeness checks, violating thermodynamic heat rate bounds (5,000 to 22,000 Btu/kWh), or exhibiting foreign key referential failures must be routed to <code>quarantine.rejected_records</code> with the raw payload stored as JSON and diagnostic failure codes.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-05: Bipartite Crosswalk Graph Resolution</span><span class="badge badge-green">Conformance</span></div>
    <div class="req-desc">The Silver engine must model the EPA-EIA boiler-to-generator crosswalk as a bipartite adjacency graph to resolve complex M:N mappings without creating duplicate rows or Cartesian products.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-06: Geospatial Meteorological Joining</span><span class="badge badge-green">Enrichment</span></div>
    <div class="req-desc">Power plants must be spatially joined to the nearest NOAA weather station using the Great-Circle Haversine distance formula (&le; 50 km) within a &plusmn; 60 minute temporal window, preserving the calculated match distance in kilometers.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-07: Slowly Changing Dimension (SCD Type 2) Lifecycle</span><span class="badge badge-purple">Kimball DW</span></div>
    <div class="req-desc">The dimensional warehouse must track historical transitions in generator operating status (<code>OP</code>, <code>SB</code>, <code>RE</code>) via <code>dim_generator</code> using <code>row_effective_date</code>, <code>row_expiration_date</code>, and <code>is_current</code> flags.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-08: Surrogate Key Resolution & Unknown Member Handling</span><span class="badge badge-purple">Kimball DW</span></div>
    <div class="req-desc">All fact tables must store surrogate integer/bigint keys resolved from dimension natural keys. All dimensions must maintain a default <code>-1 = Unknown</code> row to prevent drop-outs during fact loading.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-09: Multi-Grain Fact Table Loading</span><span class="badge badge-purple">Kimball DW</span></div>
    <div class="req-desc">The Gold layer must load and maintain three distinct Kimball fact archetypes: Transactional (Hourly Emissions), Periodic Snapshot (Monthly Plant Operations), and Aggregate (Regional Grid Demand).</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-10: Cross-Source Physical Auxiliary Reconciliation</span><span class="badge badge-amber">Validation</span></div>
    <div class="req-desc">The audit framework must execute monthly reconciliation comparing gross generation (EPA CEMS) against net generation (EIA-923), validating auxiliary station load ratios within expected engineering ranges (3% to 14%).</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-11: Multi-Dimensional OLAP Aggregations</span><span class="badge badge-amber">Analytics</span></div>
    <div class="req-desc">The warehouse must support advanced analytical queries including multi-level hierarchical <code>ROLLUP</code>, multi-dimensional <code>CUBE</code> cross-tabulations, and window lag functions.</div>
</div>

<div class="req-box">
    <div class="req-header"><span>FR-12: DirectQuery BI Reporting Views</span><span class="badge badge-amber">BI</span></div>
    <div class="req-desc">The Gold layer must expose clean, materialized reporting views (<code>vw_emissions_intensity</code>, <code>vw_plant_performance</code>, <code>vw_monthly_generation</code>) for zero-latency Power BI DirectQuery consumption.</div>
</div>

<div class="page-break"></div>

<h1>5. Non-Functional Requirements (NFR)</h1>
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Requirement Specification</th>
            <th>Target Metric / Verification Method</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>NFR-01</strong></td>
            <td>Query Performance</td>
            <td>Reporting views and OLAP queries executed from Power BI must respond with interactive latency.</td>
            <td>Sub-second execution (&lt; 1.5 seconds) achieved via Delta Lake Liquid Clustering (<code>CLUSTER BY</code>).</td>
        </tr>
        <tr>
            <td><strong>NFR-02</strong></td>
            <td>Data Volume Capacity</td>
            <td>The dimensional warehouse must comfortably exceed all course volume thresholds.</td>
            <td>Minimum &gt;100 dimension rows per table; &gt;10,000 fact rows across multi-year federal datasets.</td>
        </tr>
        <tr>
            <td><strong>NFR-03</strong></td>
            <td>Referential Integrity</td>
            <td>Zero broken foreign key links or orphan records allowed in the Gold warehouse.</td>
            <td>100% of fact records successfully join to conformed dimensions; zero unmapped rows.</td>
        </tr>
        <tr>
            <td><strong>NFR-04</strong></td>
            <td>Pipeline Idempotency</td>
            <td>Re-executing the ETL pipeline for an existing batch must produce identical, duplicate-free tables.</td>
            <td>Enforced via Delta Lake <code>MERGE INTO</code> statements and unique batch UUID tracking.</td>
        </tr>
        <tr>
            <td><strong>NFR-05</strong></td>
            <td>Auditability & Lineage</td>
            <td>Every data transformation and load run must be completely traceable from source to BI visual.</td>
            <td>All pipeline steps logged in <code>bronze_staging.etl_run_log</code> with row counts, duration, and status.</td>
        </tr>
        <tr>
            <td><strong>NFR-06</strong></td>
            <td>Security & Governance</td>
            <td>Strict zero-credential exposure across all repository scripts and source code.</td>
            <td>OAuth U2M and environment-based tokens; zero hardcoded passwords or API keys in Git.</td>
        </tr>
        <tr>
            <td><strong>NFR-07</strong></td>
            <td>ANSI SQL Compliance</td>
            <td>All DDL, DML, and queries must comply with modern ANSI SQL standards.</td>
            <td>Standard timestamp literals <code>TIMESTAMP 'YYYY-MM-DD HH:MM:SS'</code> and safe <code>TRY_CAST()</code>.</td>
        </tr>
        <tr>
            <td><strong>NFR-08</strong></td>
            <td>Reproducibility</td>
            <td>The entire warehouse must be rebuildable from scratch using repository scripts.</td>
            <td>Fully automated Python orchestrator and SQL scripts executable on standard local / cloud environments.</td>
        </tr>
    </tbody>
</table>

<h1>6. Data Governance, Freshness & Retention SLAs</h1>
<ul>
    <li><strong>Data Refresh Frequency:</strong>
        <br>• Form EIA-923: Refreshed monthly upon federal release.
        <br>• Form EIA-860: Refreshed annually upon generator inventory publication.
        <br>• EPA CAMPD & NOAA ISD: Ingested in quarterly/annual historical partitions.
        <br>• Form EIA-930: Ingested as hourly macro grid telemetry.
    </li>
    <li><strong>Data Retention Policy:</strong> Raw Bronze files are archived indefinitely in object storage Volumes (<code>raw_landing</code>). Gold warehouse facts are partitioned and retained for a 5-year rolling operational window.</li>
    <li><strong>Quarantine Governance:</strong> Quarantined records in <code>quarantine.rejected_records</code> are retained for 90 days for forensic root-cause analysis, after which verified fixes are replayed via the Silver staging pipeline.</li>
</ul>

</body>
</html>
"""
    html = body.replace("__BASE_CSS__", BASE_CSS)
    output_html = os.path.join(SCRIPT_DIR, "02_Business_Requirements_Document.html")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {output_html}")

if __name__ == "__main__":
    generate_brd_html()
