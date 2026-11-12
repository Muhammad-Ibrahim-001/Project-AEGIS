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
    font-size: 10pt;
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
    font-size: 16pt;
    font-weight: 800;
    color: #0F172A;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 5px;
    margin-top: 25px;
    page-break-after: avoid;
}
h2 {
    font-size: 12.5pt;
    font-weight: 700;
    color: #0369A1;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}
.bq-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    margin-bottom: 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    page-break-inside: avoid;
}
.bq-card-header {
    background: #F8FAFC;
    border-bottom: 1px solid #E2E8F0;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 6px 6px 0 0;
}
.bq-title {
    font-size: 10.5pt;
    font-weight: 700;
    color: #0F172A;
}
.bq-badge {
    padding: 2px 8px;
    font-size: 7.5pt;
    font-weight: 700;
    border-radius: 4px;
    text-transform: uppercase;
}
.badge-blue { background: #E0F2FE; color: #0369A1; }
.badge-green { background: #DCFCE7; color: #15803D; }
.badge-amber { background: #FEF3C7; color: #B45309; }
.badge-purple { background: #F3E8FF; color: #7E22CE; }
.bq-card-body {
    padding: 12px 14px;
}
.bq-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 8.5pt;
}
.bq-grid-item strong {
    color: #334155;
}
.sql-box {
    background: #0F172A;
    color: #F8FAFC;
    font-family: "Consolas", monospace;
    font-size: 7.8pt;
    padding: 8px 12px;
    border-radius: 4px;
    overflow-x: auto;
    margin-top: 8px;
    line-height: 1.4;
}
.sql-keyword { color: #38BDF8; font-weight: bold; }
.sql-func { color: #F472B6; }
.sql-string { color: #FCD34D; }
.sql-comment { color: #94A3B8; font-style: italic; }
.page-break { page-break-after: always; }
table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 8.5pt;
}
th {
    background: #0F172A;
    color: #FFFFFF;
    padding: 6px 8px;
    text-align: left;
}
td {
    padding: 6px 8px;
    border: 1px solid #CBD5E1;
}
tr:nth-child(even) { background: #F8FAFC; }
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)

def generate_business_questions_html():
    body = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Deliverable 3: 10+ Analytical Business Questions Specification</title>
<style>__BASE_CSS__</style>
</head>
<body>

<div class="cover-page">
    <div class="cover-tag">DL3004 Data Warehousing & Business Intelligence • Phase 1 Deliverable</div>
    <div class="cover-title">Analytical Business Questions Specification (Catalog of 12 Questions)</div>
    <div class="cover-subtitle">Strategic Inquiries, Dimensional Bus Matrix Mappings, Mathematical Formulations, Analytical SQL Queries & Decision-Support Visualizations</div>
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

<h1>1. Business Questions Overview & Summary Matrix</h1>
<p>
The course rubric (<code>DWBI Lab Phase 1.pdf</code>) mandates a minimum of 10 analytical business questions designed around business processes rather than operational table mirrors. This catalog specifies <strong>12 comprehensive analytical questions</strong> spanning the entire power generation, air emissions, meteorological, and electric grid domain:
</p>

<table>
    <thead>
        <tr>
            <th>#</th>
            <th>Strategic Analytical Domain</th>
            <th>Primary Business Question Statement</th>
            <th>Underlying Fact Archetype</th>
            <th>Conformed Dimensions</th>
            <th>Target BI Visual</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>BQ1</strong></td>
            <td>Air Emissions & Intensity</td>
            <td>Which generating facilities exhibit the highest CO2, SO2, and NOx emissions intensity per gross MWh?</td>
            <td><code>fact_hourly_emissions_weather</code></td>
            <td><code>dim_plant</code>, <code>dim_date</code></td>
            <td>Ranked Bar Chart & KPI Gauge</td>
        </tr>
        <tr>
            <td><strong>BQ2</strong></td>
            <td>Weather Sensitivity & Heat Rate</td>
            <td>How do extreme ambient temperatures (heatwaves & freezes) impact thermal heat rates?</td>
            <td><code>fact_hourly_emissions_weather</code></td>
            <td><code>dim_plant</code>, <code>dim_weather_station</code>, <code>dim_date</code></td>
            <td>Scatter Plot & Linear Regression</td>
        </tr>
        <tr>
            <td><strong>BQ3</strong></td>
            <td>Grid Clean Energy Penetration</td>
            <td>Which balancing authorities achieve the highest clean renewable penetration and lowest interchange dependency?</td>
            <td><code>fact_regional_grid_demand</code></td>
            <td><code>dim_balancing_authority</code>, <code>dim_date</code></td>
            <td>100% Stacked Area & Choropleth</td>
        </tr>
        <tr>
            <td><strong>BQ4</strong></td>
            <td>Asset Lifecycle & SCD Type 2</td>
            <td>How do generator operational lifecycles evolve over time, and which coal units are retiring?</td>
            <td><code>dim_generator</code> (SCD Type 2)</td>
            <td><code>dim_plant</code>, <code>dim_generator</code></td>
            <td>Waterfall Transition & Matrix</td>
        </tr>
        <tr>
            <td><strong>BQ5</strong></td>
            <td>Grid Dispatch vs. Forecast</td>
            <td>How does real-time generation dispatch respond to day-ahead regional demand peaks?</td>
            <td><code>fact_regional_grid_demand</code></td>
            <td><code>dim_balancing_authority</code>, <code>dim_date</code></td>
            <td>Dual-Axis Line & Bar Chart</td>
        </tr>
        <tr>
            <td><strong>BQ6</strong></td>
            <td>Physical Auxiliary Reconciliation</td>
            <td>Do EPA gross generation and EIA net generation reconcile within physical 3%–14% auxiliary limits?</td>
            <td><code>fact_hourly_emissions_weather</code>, <code>fact_monthly_plant_operations</code></td>
            <td><code>dim_plant</code>, <code>dim_date</code></td>
            <td>Tolerance Band Scatter Chart</td>
        </tr>
        <tr>
            <td><strong>BQ7</strong></td>
            <td>Marginal Peak Emissions Intensity</td>
            <td>What are the marginal emission rates during top 5% peak grid demand hours compared to baseload hours?</td>
            <td><code>fact_regional_grid_demand</code>, <code>fact_hourly_emissions_weather</code></td>
            <td><code>dim_balancing_authority</code>, <code>dim_plant</code>, <code>dim_date</code></td>
            <td>Box & Whisker Distribution Plot</td>
        </tr>
        <tr>
            <td><strong>BQ8</strong></td>
            <td>Thermal Peaker Ramping Dynamics</td>
            <td>Which balancing authorities experience steep renewable drop-offs requiring fast-ramping gas peakers?</td>
            <td><code>fact_regional_grid_demand</code></td>
            <td><code>dim_balancing_authority</code>, <code>dim_date</code></td>
            <td>Hour-over-Hour Ramping Gradient</td>
        </tr>
        <tr>
            <td><strong>BQ9</strong></td>
            <td>Turbine Thermodynamic Degradation</td>
            <td>How does operating thermal efficiency differ between Combined Cycle and Simple Cycle units under high load?</td>
            <td><code>fact_monthly_plant_operations</code></td>
            <td><code>dim_plant</code>, <code>dim_generator</code>, <code>dim_date</code></td>
            <td>Heat Rate Efficiency Heatmap</td>
        </tr>
        <tr>
            <td><strong>BQ10</strong></td>
            <td>Environmental Justice Exposure</td>
            <td>Which high-emitting fossil peakers operate within high-population non-attainment counties?</td>
            <td><code>fact_hourly_emissions_weather</code></td>
            <td><code>dim_plant</code>, <code>dim_date</code></td>
            <td>Geospatial Bubble Map & Table</td>
        </tr>
        <tr>
            <td><strong>BQ11</strong></td>
            <td>Fuel Switching Economics</td>
            <td>How do delivered natural gas prices ($/MMBtu) drive economic fuel switching away from coal generation?</td>
            <td><code>fact_monthly_plant_operations</code></td>
            <td><code>dim_plant</code>, <code>dim_date</code></td>
            <td>Dual-Axis Price vs. Share Trend</td>
        </tr>
        <tr>
            <td><strong>BQ12</strong></td>
            <td>Station Outage & Negative Net Gen</td>
            <td>Which power plants report valid negative net generation during freezing events, and what is the station power draw?</td>
            <td><code>fact_monthly_plant_operations</code></td>
            <td><code>dim_plant</code>, <code>dim_date</code></td>
            <td>Anomalous Load Outage Histogram</td>
        </tr>
    </tbody>
</table>

<div class="page-break"></div>

<h1>2. Detailed Business Question Specifications (BQ1 – BQ12)</h1>

<!-- BQ1 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ1: Facility Carbon & Toxic Air Emissions Intensity</span>
        <span class="bq-badge badge-blue">Environmental Compliance</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Environmental Compliance Officer</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_hourly_emissions_weather</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Ranked Bar Chart & Carbon Intensity KPI Gauge</div>
        </div>
        <p><strong>Business Formulation:</strong> Identify the generating facilities that produce the highest mass of CO2, SO2, and NOx per gross megawatt-hour (MWh) generated, and evaluate how their emission intensity fluctuates across calendar months.</p>
        <p><strong>Mathematical Metric:</strong> Carbon Intensity = (SUM(co2_mass_tons) * 2000) / SUM(gross_load_mw) (lbs CO2/MWh)</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.plant_name, p.state_code, d.calendar_year, d.month_name,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.co2_mass_tons * 2000) / <span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.gross_load_mw), 0), 2) <span class="sql-keyword">AS</span> lbs_co2_per_mwh,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.so2_mass_lbs) / <span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.gross_load_mw), 0), 4) <span class="sql-keyword">AS</span> lbs_so2_per_mwh,
       <span class="sql-func">DENSE_RANK</span>() <span class="sql-keyword">OVER</span> (<span class="sql-keyword">PARTITION BY</span> d.calendar_year, d.calendar_month <span class="sql-keyword">ORDER BY</span> <span class="sql-func">SUM</span>(f.co2_mass_tons)/<span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.gross_load_mw),0) <span class="sql-keyword">DESC</span>) <span class="sql-keyword">AS</span> fleet_rank
<span class="sql-keyword">FROM</span> gold_warehouse.fact_hourly_emissions_weather f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> f.plant_key = p.plant_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.date_key = d.date_key
<span class="sql-keyword">GROUP BY</span> p.plant_name, p.state_code, d.calendar_year, d.calendar_month, d.month_name;
        </div>
    </div>
</div>

<!-- BQ2 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ2: Synoptic Weather Extremes & Generator Heat Rate Sensitivity</span>
        <span class="bq-badge badge-green">Thermal Efficiency</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Plant Operations & Fuel Manager</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_hourly_emissions_weather</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_weather_station</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Scatter Plot of Heat Rate vs. Temperature with Regression Trendline</div>
        </div>
        <p><strong>Business Formulation:</strong> Determine how extreme meteorological conditions (summer heatwaves &gt;35°C and winter polar freezes &lt;0°C) impact thermal efficiency (heat rate in Btu/kWh) and available gross generation capacity.</p>
        <p><strong>Mathematical Metric:</strong> Hourly Heat Rate = (heat_input_mmbtu * 1,000,000) / (gross_load_mw * 1,000) (Btu/kWh)</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.plant_name, f.ambient_temp_celsius,
       <span class="sql-func">ROUND</span>((f.heat_input_mmbtu * 1000000.0) / <span class="sql-func">NULLIF</span>(f.gross_load_mw * 1000.0, 0), 2) <span class="sql-keyword">AS</span> hourly_heat_rate_btu_kwh,
       <span class="sql-keyword">CASE WHEN</span> f.ambient_temp_celsius &gt;= 35.0 <span class="sql-keyword">THEN</span> <span class="sql-string">'Extreme Heat'</span>
            <span class="sql-keyword">WHEN</span> f.ambient_temp_celsius &lt;= 0.0 <span class="sql-keyword">THEN</span> <span class="sql-string">'Freezing Event'</span>
            <span class="sql-keyword">ELSE</span> <span class="sql-string">'Nominal Operating Range'</span> <span class="sql-keyword">END AS</span> thermal_stress_tier
<span class="sql-keyword">FROM</span> gold_warehouse.fact_hourly_emissions_weather f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> f.plant_key = p.plant_key
<span class="sql-keyword">WHERE</span> f.gross_load_mw &gt; 50.0 <span class="sql-keyword">AND</span> f.weather_distance_km &lt;= 50.0;
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- BQ3 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ3: Balancing Authority Renewable Penetration & Interchange Dependency</span>
        <span class="bq-badge badge-amber">Grid Reliability</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Grid Reliability Engineer</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_regional_grid_demand</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_balancing_authority</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> 100% Stacked Area Chart & Choropleth Map</div>
        </div>
        <p><strong>Business Formulation:</strong> Measure the hourly clean renewable energy penetration (wind + solar share of total generation) across regional grid authorities and assess external import/export interchange dependency.</p>
        <p><strong>Mathematical Metric:</strong> Renewable Share % = (SUM(net_gen_wind_mw + net_gen_solar_mw) / SUM(demand_mw)) * 100%</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> ba.ba_code, ba.ba_name, d.calendar_year, d.calendar_month,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.net_gen_wind_mw + f.net_gen_solar_mw) * 100.0 / <span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.demand_mw), 0), 2) <span class="sql-keyword">AS</span> renewable_penetration_pct,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.net_interchange_mw) * 100.0 / <span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.demand_mw), 0), 2) <span class="sql-keyword">AS</span> net_import_dependency_pct
<span class="sql-keyword">FROM</span> gold_warehouse.fact_regional_grid_demand f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_balancing_authority ba <span class="sql-keyword">ON</span> f.ba_key = ba.ba_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.date_key = d.date_key
<span class="sql-keyword">GROUP BY</span> ba.ba_code, ba.ba_name, d.calendar_year, d.calendar_month;
        </div>
    </div>
</div>

<!-- BQ4 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ4: Generator Asset Lifecycle & SCD Type 2 Retirement Trajectory</span>
        <span class="bq-badge badge-purple">Asset Strategy</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Executive Leadership / Strategy Director</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>dim_generator</code> (SCD Type 2)</div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_generator</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Timeline Waterfall Visual & Historical Capacity Transition Matrix</div>
        </div>
        <p><strong>Business Formulation:</strong> Track how generating asset capacities and operating statuses transition across lifecycle stages (Operating OP &rarr; Standby SB &rarr; Retired RE), quantifying fossil capacity retired vs. renewable capacity added.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.state_code, g.primary_energy_source, g.operating_status,
       <span class="sql-func">COUNT</span>(g.generator_key) <span class="sql-keyword">AS</span> total_units,
       <span class="sql-func">SUM</span>(g.nameplate_capacity_mw) <span class="sql-keyword">AS</span> total_capacity_mw,
       <span class="sql-func">MIN</span>(g.row_effective_date) <span class="sql-keyword">AS</span> earliest_transition_date,
       <span class="sql-func">MAX</span>(g.row_effective_date) <span class="sql-keyword">AS</span> latest_transition_date
<span class="sql-keyword">FROM</span> gold_warehouse.dim_generator g
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> g.orispl_code = p.orispl_code
<span class="sql-keyword">WHERE</span> g.operating_status = <span class="sql-string">'RE'</span>
<span class="sql-keyword">GROUP BY</span> p.state_code, g.primary_energy_source, g.operating_status;
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- BQ5 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ5: Real-Time Grid Dispatch Response vs. Day-Ahead Forecast Peaks</span>
        <span class="bq-badge badge-amber">Grid Operations</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Grid Reliability Engineer</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_regional_grid_demand</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_balancing_authority</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Dual-Axis Line & Bar Chart Comparing Dispatch vs. Forecast</div>
        </div>
        <p><strong>Business Formulation:</strong> Quantify the hourly forecast variance (Demand - Forecast) during daily peak demand hours (hours 16–21) to assess reserve margin stress.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> ba.ba_code, d.calendar_date, f.hour_of_day, f.demand_mw, f.demand_forecast_mw,
       (f.demand_mw - f.demand_forecast_mw) <span class="sql-keyword">AS</span> forecast_error_mw,
       <span class="sql-func">ROUND</span>((f.demand_mw - f.demand_forecast_mw) * 100.0 / <span class="sql-func">NULLIF</span>(f.demand_forecast_mw, 0), 2) <span class="sql-keyword">AS</span> forecast_error_pct
<span class="sql-keyword">FROM</span> gold_warehouse.fact_regional_grid_demand f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_balancing_authority ba <span class="sql-keyword">ON</span> f.ba_key = ba.ba_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.date_key = d.date_key
<span class="sql-keyword">WHERE</span> f.hour_of_day <span class="sql-keyword">BETWEEN</span> 16 <span class="sql-keyword">AND</span> 21;
        </div>
    </div>
</div>

<!-- BQ6 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ6: Cross-Agency Physical Auxiliary Power Reconciliation</span>
        <span class="bq-badge badge-blue">Data Quality & Audit</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Compliance Lead & Data Auditor</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_hourly_emissions_weather</code>, <code>fact_monthly_plant_operations</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Auxiliary Ratio Tolerance Band Scatter Chart</div>
        </div>
        <p><strong>Business Formulation:</strong> Cross-validate monthly gross generation aggregated from EPA CAMPD hourly CEMS against net generation reported in EIA-923 to ensure station auxiliary consumption adheres to thermodynamic physics (3% &le; Aux Ratio &le; 14%).</p>
        <p><strong>Mathematical Metric:</strong> Auxiliary Load % = ((Gross Gen EPA - Net Gen EIA) / Gross Gen EPA) * 100%</p>
        <div class="sql-box">
<span class="sql-keyword">WITH</span> epa_monthly <span class="sql-keyword">AS</span> (
    <span class="sql-keyword">SELECT</span> plant_key, <span class="sql-func">SUBSTRING</span>(<span class="sql-func">CAST</span>(date_key <span class="sql-keyword">AS</span> VARCHAR), 1, 6) <span class="sql-keyword">AS</span> yyyymm,
           <span class="sql-func">SUM</span>(gross_load_mw) <span class="sql-keyword">AS</span> epa_gross_mwh
    <span class="sql-keyword">FROM</span> gold_warehouse.fact_hourly_emissions_weather
    <span class="sql-keyword">GROUP BY</span> plant_key, <span class="sql-func">SUBSTRING</span>(<span class="sql-func">CAST</span>(date_key <span class="sql-keyword">AS</span> VARCHAR), 1, 6)
)
<span class="sql-keyword">SELECT</span> p.plant_name, e.yyyymm, e.epa_gross_mwh, m.net_generation_mwh <span class="sql-keyword">AS</span> eia_net_mwh,
       <span class="sql-func">ROUND</span>((e.epa_gross_mwh - m.net_generation_mwh) * 100.0 / <span class="sql-func">NULLIF</span>(e.epa_gross_mwh, 0), 2) <span class="sql-keyword">AS</span> aux_load_pct
<span class="sql-keyword">FROM</span> epa_monthly e
<span class="sql-keyword">JOIN</span> gold_warehouse.fact_monthly_plant_operations m <span class="sql-keyword">ON</span> e.plant_key = m.plant_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> e.plant_key = p.plant_key;
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- BQ7 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ7: Marginal Peak Emissions Intensity vs. Baseload Hours</span>
        <span class="bq-badge badge-blue">Decarbonization</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Environmental Policy Analyst</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_regional_grid_demand</code>, <code>fact_hourly_emissions_weather</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_balancing_authority</code>, <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Box & Whisker Emissions Distribution Plot</div>
        </div>
        <p><strong>Business Formulation:</strong> Calculate the marginal carbon emissions rate during top 5% peak demand hours compared to off-peak hours to identify inefficient peaker activation.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.ba_code,
       <span class="sql-keyword">CASE WHEN</span> f.hour_of_day <span class="sql-keyword">BETWEEN</span> 17 <span class="sql-keyword">AND</span> 20 <span class="sql-keyword">THEN</span> <span class="sql-string">'Peak Dispatch'</span> <span class="sql-keyword">ELSE</span> <span class="sql-string">'Off-Peak'</span> <span class="sql-keyword">END AS</span> dispatch_period,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.co2_mass_tons * 2000.0) / <span class="sql-func">NULLIF</span>(<span class="sql-func">SUM</span>(f.gross_load_mw), 0), 2) <span class="sql-keyword">AS</span> avg_carbon_intensity_lbs_mwh
<span class="sql-keyword">FROM</span> gold_warehouse.fact_hourly_emissions_weather f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> f.plant_key = p.plant_key
<span class="sql-keyword">GROUP BY</span> p.ba_code, <span class="sql-keyword">CASE WHEN</span> f.hour_of_day <span class="sql-keyword">BETWEEN</span> 17 <span class="sql-keyword">AND</span> 20 <span class="sql-keyword">THEN</span> <span class="sql-string">'Peak Dispatch'</span> <span class="sql-keyword">ELSE</span> <span class="sql-string">'Off-Peak'</span> <span class="sql-keyword">END</span>;
        </div>
    </div>
</div>

<!-- BQ8 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ8: Thermal Peaker Ramp-Up Response During Renewable Curtailment</span>
        <span class="bq-badge badge-amber">Grid Reliability</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Transmission System Operator</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_regional_grid_demand</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_balancing_authority</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Hour-over-Hour Ramping Gradient Line Chart</div>
        </div>
        <p><strong>Business Formulation:</strong> Measure the maximum 1-hour positive ramping required from natural gas generation when solar generation drops off at sunset (duck curve analysis).</p>
        <p><strong>Mathematical Metric:</strong> Gas Ramp MW = net_gen_gas_mw(t) - net_gen_gas_mw(t-1)</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> ba.ba_code, d.calendar_date, f.hour_of_day, f.net_gen_gas_mw,
       (f.net_gen_gas_mw - <span class="sql-func">LAG</span>(f.net_gen_gas_mw, 1) <span class="sql-keyword">OVER</span> (<span class="sql-keyword">PARTITION BY</span> f.ba_key, d.calendar_date <span class="sql-keyword">ORDER BY</span> f.hour_of_day)) <span class="sql-keyword">AS</span> gas_ramp_1hr_mw
<span class="sql-keyword">FROM</span> gold_warehouse.fact_regional_grid_demand f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_balancing_authority ba <span class="sql-keyword">ON</span> f.ba_key = ba.ba_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.date_key = d.date_key
<span class="sql-keyword">WHERE</span> f.hour_of_day <span class="sql-keyword">BETWEEN</span> 15 <span class="sql-keyword">AND</span> 22;
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- BQ9 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ9: Turbine Thermodynamic Efficiency: Combined Cycle vs. Simple Cycle</span>
        <span class="bq-badge badge-green">Thermal Efficiency</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Thermal Generation Engineer</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_monthly_plant_operations</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Technology Heat Rate Heatmap Matrix</div>
        </div>
        <p><strong>Business Formulation:</strong> Compare operating heat rates (Btu/kWh) between Combined Cycle (CT/CA) and Simple Cycle Gas Turbines (GT) across capacity factors to detect equipment degradation.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> f.prime_mover_code, d.calendar_year,
       <span class="sql-func">ROUND</span>(<span class="sql-func">AVG</span>(f.avg_heat_rate_btu_kwh), 2) <span class="sql-keyword">AS</span> mean_heat_rate_btu_kwh,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.net_generation_mwh), 0) <span class="sql-keyword">AS</span> total_generation_mwh
<span class="sql-keyword">FROM</span> gold_warehouse.fact_monthly_plant_operations f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.month_start_date_key = d.date_key
<span class="sql-keyword">WHERE</span> f.prime_mover_code <span class="sql-keyword">IN</span> (<span class="sql-string">'CA'</span>, <span class="sql-string">'CT'</span>, <span class="sql-string">'GT'</span>, <span class="sql-string">'ST'</span>) <span class="sql-keyword">AND</span> f.net_generation_mwh &gt; 0
<span class="sql-keyword">GROUP BY</span> f.prime_mover_code, d.calendar_year;
        </div>
    </div>
</div>

<!-- BQ10 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ10: Environmental Justice & Non-Attainment County Emissions</span>
        <span class="bq-badge badge-blue">Social Impact</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Public Health & Policy Director</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_hourly_emissions_weather</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Geospatial Bubble Map with County Overlay</div>
        </div>
        <p><strong>Business Formulation:</strong> Pinpoint fossil peaker units operating inside urban non-attainment counties that emit disproportionate cumulative SO2 and NOx mass during summer air stagnation periods.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.county_name, p.state_code, p.plant_name,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.nox_mass_lbs) / 2000.0, 2) <span class="sql-keyword">AS</span> total_nox_tons,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.so2_mass_lbs) / 2000.0, 2) <span class="sql-keyword">AS</span> total_so2_tons
<span class="sql-keyword">FROM</span> gold_warehouse.fact_hourly_emissions_weather f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> f.plant_key = p.plant_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.date_key = d.date_key
<span class="sql-keyword">WHERE</span> d.calendar_month <span class="sql-keyword">BETWEEN</span> 6 <span class="sql-keyword">AND</span> 8
<span class="sql-keyword">GROUP BY</span> p.county_name, p.state_code, p.plant_name
<span class="sql-keyword">ORDER BY</span> total_nox_tons <span class="sql-keyword">DESC LIMIT</span> 20;
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- BQ11 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ11: Multi-Year Fuel Switching Dynamics Driven by Fuel Price</span>
        <span class="bq-badge badge-green">Fuel Economics</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Energy Trading & Fuel Procurement Lead</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_monthly_plant_operations</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Dual-Axis Delivered Fuel Price vs. Generation Share Trend</div>
        </div>
        <p><strong>Business Formulation:</strong> Analyze how variations in delivered natural gas cost ($/MMBtu) cause utilities to displace coal generation with natural gas, and determine the tipping-point price.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> d.calendar_year, d.calendar_month, f.energy_source_code,
       <span class="sql-func">ROUND</span>(<span class="sql-func">AVG</span>(f.delivered_fuel_cost_per_mmbtu), 2) <span class="sql-keyword">AS</span> avg_fuel_cost_per_mmbtu,
       <span class="sql-func">ROUND</span>(<span class="sql-func">SUM</span>(f.net_generation_mwh), 0) <span class="sql-keyword">AS</span> monthly_generation_mwh
<span class="sql-keyword">FROM</span> gold_warehouse.fact_monthly_plant_operations f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.month_start_date_key = d.date_key
<span class="sql-keyword">WHERE</span> f.energy_source_code <span class="sql-keyword">IN</span> (<span class="sql-string">'NG'</span>, <span class="sql-string">'SUB'</span>, <span class="sql-string">'BIT'</span>)
<span class="sql-keyword">GROUP BY</span> d.calendar_year, d.calendar_month, f.energy_source_code;
        </div>
    </div>
</div>

<!-- BQ12 -->
<div class="bq-card">
    <div class="bq-card-header">
        <span class="bq-title">BQ12: Station Service Outage Frequency & Negative Net Generation</span>
        <span class="bq-badge badge-purple">Defensive Data Quality</span>
    </div>
    <div class="bq-card-body">
        <div class="bq-grid">
            <div class="bq-grid-item"><strong>Target Stakeholder:</strong> Plant Maintenance Lead & Data Quality Engineer</div>
            <div class="bq-grid-item"><strong>Fact Integration:</strong> <code>fact_monthly_plant_operations</code></div>
            <div class="bq-grid-item"><strong>Dimensions:</strong> <code>dim_plant</code>, <code>dim_date</code></div>
            <div class="bq-grid-item"><strong>Target Visual:</strong> Anomalous Station Power Draw Outage Histogram</div>
        </div>
        <p><strong>Business Formulation:</strong> Detect the frequency and magnitude of power plants drawing net auxiliary power from the grid during maintenance shutdowns (negative net generation), confirming that these legitimate physical events are never erroneously rejected by ETL quality checks.</p>
        <div class="sql-box">
<span class="sql-keyword">SELECT</span> p.plant_name, p.state_code, d.calendar_year, d.month_name,
       f.net_generation_mwh <span class="sql-keyword">AS</span> auxiliary_station_draw_mwh,
       f.fuel_consumed_mmbtu
<span class="sql-keyword">FROM</span> gold_warehouse.fact_monthly_plant_operations f
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_plant p <span class="sql-keyword">ON</span> f.plant_key = p.plant_key
<span class="sql-keyword">JOIN</span> gold_warehouse.dim_date d <span class="sql-keyword">ON</span> f.month_start_date_key = d.date_key
<span class="sql-keyword">WHERE</span> f.net_generation_mwh &lt; 0.0
<span class="sql-keyword">ORDER BY</span> f.net_generation_mwh <span class="sql-keyword">ASC</span>;
        </div>
    </div>
</div>

</body>
</html>
"""
    html = body.replace("__BASE_CSS__", BASE_CSS)
    output_html = os.path.join(SCRIPT_DIR, "03_10_Business_Questions.html")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {output_html}")

if __name__ == "__main__":
    generate_business_questions_html()
