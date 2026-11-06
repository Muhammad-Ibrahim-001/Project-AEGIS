import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def create_document():
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
    return doc

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header_title(doc, title, subtitle):
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    run_title = p_title.add_run(title)
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(21)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(27, 54, 93) # Deep Navy
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(8)
    run_sub = p_sub.add_run(subtitle)
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(11.5)
    run_sub.italic = True
    run_sub.font.color.rgb = RGBColor(70, 95, 133) # Slate Blue

    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(0)
    p_line.paragraph_format.space_after = Pt(10)
    run_line = p_line.add_run("―" * 60)
    run_line.font.color.rgb = RGBColor(210, 220, 235)

def add_h1(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(13.5)
    r.bold = True
    r.font.color.rgb = RGBColor(27, 54, 93)

def add_h2(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(11.5)
    r.bold = True
    r.font.color.rgb = RGBColor(46, 107, 158)

def add_body(doc, text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(9.5)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(30, 41, 59)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(9.5)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(30, 41, 59)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_callout(doc, text, title="Key Takeaway", accent_color="1B365D"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="single" w:sz="36" w:space="0" w:color="{accent_color}"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
    tcPr.append(tcBorders)
    set_cell_margins(cell, top=80, bottom=80, left=130, right=130)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.15
    
    r_title = p.add_run(f"📌 {title}: ")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(9.5)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(27, 54, 93)
    
    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(9)
    r_text.font.color.rgb = RGBColor(71, 85, 105)
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(3)

def format_table(table, col_widths, headers, rows_data):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = h_text
        set_cell_background(hdr_cells[i], "1B365D")
        set_cell_margins(hdr_cells[i], top=60, bottom=60, left=80, right=80)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(8.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            
    for r_idx, row in enumerate(rows_data):
        row_cells = table.add_row().cells
        bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row):
            row_cells[c_idx].text = str(cell_value)
            set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=45, bottom=45, left=80, right=80)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Calibri'
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(51, 65, 85)
                
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

# ==============================================================================
# 1. BUILD DOCUMENT 1: PROJECT INTRODUCTION & OVERVIEW
# ==============================================================================
def build_doc1(output_path):
    doc = create_document()
    add_header_title(doc, 
                     "Welcome to Our DWBI Project: High-Level Overview", 
                     "Why We're Building an Industrial Power & Climate Warehouse (And Why It Sets Us Apart)")
    
    add_h1(doc, "1. The Big Picture: Why We Aren't Building Another Grocery Store")
    add_body(doc, "When university teams start a Data Warehousing & Business Intelligence (DWBI) project, almost everyone takes the easy route: they download a pre-cleaned retail sales CSV (like Superstore, Amazon reviews, or a mock e-commerce database). Those datasets are trivial, flat, and teachers and recruiters have seen them hundreds of times.")
    add_body(doc, "Instead, our team is building an enterprise-grade, real-world data warehouse centered on critical national infrastructure: the U.S. Bulk Electrical Grid, Smokestack Air Pollution, and Synoptic Weather Telemetry.")
    
    add_callout(doc, 
                "We are solving a genuine, headline-level real-world problem: When extreme weather strikes (like summer heatwaves or winter polar freezes), power demand surges. Which power plants are forced to run? How much toxic pollution comes out of their smokestacks? And which technologies are failing?", 
                "The Core Business Story")

    add_h1(doc, "2. The Problem: Three Federal Agencies, Zero Coordination")
    add_body(doc, "In the United States, three separate federal agencies track different pieces of this energy ecosystem, completely independent of each other:")
    add_bullet(doc, "measures continuous smokestack emissions (SO2, NOx, CO2) and gross megawatts every single hour from physical sensors in power plant exhaust stacks.", "The EPA (Environmental Protection Agency): ")
    add_bullet(doc, "tracks power plant ownership, generator machine types, monthly fuel bills, and real-time regional electrical grid demand.", "The EIA (Energy Information Administration): ")
    add_bullet(doc, "tracks ground weather observations (temperature, wind speed, barometric pressure) at airport weather stations nationwide.", "The NOAA (National Oceanic & Atmospheric Admin): ")
    add_body(doc, "Because these agencies don't talk to each other, an energy analyst or environmental auditor who wants to know why pollution rose during a Texas heatwave has to spend weeks manually stitching together incompatible spreadsheets, APIs, and text files. Our warehouse does this automatically.")

    add_h1(doc, "3. Why This Is a Serious Data Engineering Project")
    add_body(doc, "This project isn't just about writing SQL queries on a clean table. It tackles every classic challenge that professional data engineers encounter in production:")
    add_bullet(doc, "We don't just load one clean CSV. We ingest live REST JSON APIs, multi-tab Excel workbooks, massive bulk CSVs, and fixed-width meteorological feeds.", "1. Multi-Format Ingestion: ")
    add_bullet(doc, "Some data arrives hourly (smokestack sensors, grid demand), some arrives monthly (fuel accounting and net power), and some arrives annually (machine inventory). We design star schemas that gracefully handle all three time grains.", "2. Multi-Grain Harmonization: ")
    add_bullet(doc, "Government data is notoriously dirty. EIA Excel files use '.' and 'NM' (Not Meaningful) instead of nulls. NOAA weather feeds use integer -9999. In addition, 41 power plants report negative electricity generation because offline plants consume power from the grid to keep their safety systems running!", "3. Handling Real-World Upstream Bugs: ")
    add_bullet(doc, "Power plants don't stay static. Over time, generators change their operating status from 'Operating' to 'Retired'. We implement a Kimball Slowly Changing Dimension (SCD Type 2) with timestamp tracking so history is never lost.", "4. Slowly Changing Dimensions (SCD Type 2): ")
    add_bullet(doc, "When a bad record comes in (e.g., impossible fuel heat rates), our pipeline doesn't crash. Bad records are automatically trapped into a dead-letter quarantine table with exact rejection reason codes, while clean data flows through.", "5. Automated Data Quality Quarantine: ")
    add_bullet(doc, "Power plants don't have weather stations on their roofs. We use the mathematical Haversine formula to find the nearest weather station within 50 km and join weather to smokestack emissions within +/- 60 minutes.", "6. Spatial Nearest-Neighbor Joining: ")
    add_bullet(doc, "We enforce physical laws across agencies: A plant's Net Generation (EIA) can never physically exceed its Gross Generation (EPA). Our pipeline audits this automatically.", "7. Cross-Source Conservation Auditing: ")

    add_h1(doc, "4. The End-to-End Pipeline in Simple Terms")
    add_body(doc, "We implement an 8-stage enterprise medallion architecture:")
    add_body(doc, "1. Source Systems (6 public feeds) ➔ 2. Python Master Orchestrator ➔ 3. Bronze Staging (Raw unvalidated tables) ➔ 4. Data Quality & Quarantine ➔ 5. Silver Layer (Cleaned & unit-conformed) ➔ 6. Dimensional Data Warehouse (Kimball Star Schema in PostgreSQL) ➔ 7. Gold Data Marts (Aggregated analytical views) ➔ 8. Interactive 3-Page Power BI Dashboard.")

    add_h1(doc, "5. What This Means for Us as a Team")
    add_bullet(doc, "Our architecture strictly implements every single requirement in the DL3004 syllabus, guaranteeing maximum marks across Phase 1, Phase 2, and Phase 3.", "Academic Excellence: ")
    add_bullet(doc, "The entire pipeline runs locally on free software: PostgreSQL 16+, Python, and Power BI Desktop. No cloud subscriptions or paid software required.", "100% Free & Local: ")
    add_bullet(doc, "When interviewing for internships or data engineering roles, talking about handling CEMS emissions telemetry, SCD Type 2 lifecycles, and partitioned star schemas immediately sets you apart from candidates with basic toy projects.", "Killer Portfolio Piece: ")

    doc.save(output_path)
    print(f"Document 1 generated: {output_path}")

# ==============================================================================
# 2. BUILD DOCUMENT 2: DATA SOURCES & CONNECTIONS GUIDE
# ==============================================================================
def build_doc2(output_path):
    doc = create_document()
    add_header_title(doc, 
                     "The Data Ecosystem: Sources and Connections Guide", 
                     "A Clear, Intuitive Guide to How Six Federal Datasets Interlock")
    
    add_h1(doc, "1. The Ecosystem at a Glance")
    add_body(doc, "Our warehouse integrates six public datasets across three U.S. federal agencies. Here is the high-level lineup:")
    
    headers = ["#", "Source Name", "Agency", "Native Format", "Native Grain", "Role in Warehouse"]
    widths = [Inches(0.4), Inches(1.3), Inches(0.8), Inches(1.1), Inches(1.4), Inches(1.8)]
    rows = [
        ["1", "EPA CAMPD", "U.S. EPA", "Bulk CSV / API", "Hourly per Smokestack", "Main Transactional Fact (Pollution & Gross MW)"],
        ["2", "EIA-860", "U.S. EIA", "Multi-tab Excel", "Annual per Generator", "Dimensions: Dim_Plant & Dim_Generator (SCD 2)"],
        ["3", "EIA-923", "U.S. EIA", "Multi-tab Excel", "Monthly per Plant/Fuel", "Periodic Snapshot Fact (Net MWh & Fuel Ledger)"],
        ["4", "EIA-930", "U.S. EIA", "REST JSON / CSV", "Hourly per Grid Region", "Aggregate Grid Fact (Regional Demand & Fuel Mix)"],
        ["5", "Crosswalk", "EPA & EIA", "CSV / Excel", "Boiler-to-Generator", "Bipartite Bridge linking Stacks to Generators"],
        ["6", "NOAA ISD", "NOAA NCEI", "Fixed-width / CSV", "Hourly per Station", "Dim_Weather_Station & Environmental Enriched Fact"]
    ]
    tbl = doc.add_table(rows=1, cols=6)
    format_table(tbl, widths, headers, rows)
    
    add_h1(doc, "2. The Airline Analogy (Grasping the Ecosystem in 60 Seconds)")
    add_body(doc, "If power grid terminology feels complex, think of the system as a national commercial airline:")
    add_bullet(doc, "is the Airplane Fleet Catalog (lists every plane, engine model, seating capacity, and year manufactured).", "EIA-860: ")
    add_bullet(doc, "is the Black Box Engine Sensor (records actual fuel burned, exhaust heat, and engine thrust every minute of flight).", "EPA CAMPD: ")
    add_bullet(doc, "is the Monthly Fuel & Financial Ledger (how many gallons of jet fuel the airline purchased, ticket revenue, and net passenger miles).", "EIA-923: ")
    add_bullet(doc, "is National Air Traffic Control (tracks total passenger demand in the sky, flight delays, and airspace congestion).", "EIA-930: ")
    add_bullet(doc, "is the Engineering Blueprint (tells mechanics which jet engines are mounted to which aircraft wings).", "EPA-EIA Crosswalk: ")
    add_bullet(doc, "is the Flight Weather Radar (measures outside headwind, turbulence, and air temperature).", "NOAA ISD: ")

    add_h1(doc, "3. Walkthrough of the Six Sources")
    
    add_h2(doc, "Source 1: EPA CAMPD (The Main Operational Anchor)")
    add_body(doc, "Under the Clean Air Act, all large fossil-fuel plants must install Continuous Emission Monitoring Systems (CEMS) directly inside their smokestacks. Every single hour, physical sensors measure SO2 (acid rain), NOx (smog), CO2 (greenhouse gas), gross electricity generated, and fuel heat input. It is our largest, most detailed operational dataset.")

    add_h2(doc, "Source 2: EIA-860 (The Equipment Directory)")
    add_body(doc, "An annual census of every power plant and generator in America. It provides the 'passport' for every facility: utility owner, geographic coordinates, county, engine technology, nameplate megawatt capacity, and lifecycle status (Operating, Standby, or Retired).")

    add_h2(doc, "Source 3: EIA-923 (Monthly Fuel & Operations Ledger)")
    add_body(doc, "While EPA measures hourly gross generation at the stack, EIA-923 measures monthly net generation sent to the grid, fuel consumed, delivered fuel prices ($/MMBtu), and on-site fuel stockpiles. It enables financial and efficiency analysis.")

    add_h2(doc, "Source 4: EIA-930 (Hourly Regional Grid Demand)")
    add_body(doc, "Electricity cannot be easily stored in bulk. EIA-930 monitors balancing authorities (regional grid operators like ERCOT in Texas or PJM in the Mid-Atlantic). Every hour, it tells us total consumer electricity demand, forecasted demand, and real-time generation by fuel mix (coal, gas, nuclear, hydro, wind, solar).")

    add_h2(doc, "Source 5: The EPA-EIA Crosswalk (The Translation Dictionary)")
    add_body(doc, "The EPA monitors boilers and smokestacks (where smoke comes out). The EIA monitors turbines and generators (where electricity is made). Because large power plants often have multiple boilers feeding multiple generators, they don't have a simple 1-to-1 match. This official federal crosswalk acts as the bridge connecting EPA boiler IDs to EIA generator IDs.")

    add_h2(doc, "Source 6: NOAA ISD (Hourly Surface Weather)")
    add_body(doc, "Hourly meteorological readings from airport weather stations. Supplies ambient temperature, wind speed, and atmospheric pressure to help us model how weather influences power generation.")

    add_h1(doc, "4. The Master Connection Blueprint: How They Talk to Each Other")
    add_body(doc, "How do these six independent feeds connect in our PostgreSQL database? They connect through four explicit integration keys:")
    
    add_bullet(doc, "Both EPA and EIA use a shared federal plant identifier called the ORISPL Plant Code (e.g., Plant 3470 is always W.A. Parish in Texas). This connects EPA CAMPD, EIA-860, EIA-923, and the Crosswalk at the facility level.", "Key 1: The Master Plant Code (ORISPL): ")
    add_bullet(doc, "The EPA-EIA Crosswalk maps EPA unit_id (smokestack) to EIA generator_id (machine). This connects our hourly emissions fact table to our generator dimension.", "Key 2: The Equipment Bridge: ")
    add_bullet(doc, "Every power plant belongs to a regional grid operator (Balancing Authority). This links regional grid demand in EIA-930 to local plant operations.", "Key 3: The Balancing Authority Code (ba_code): ")
    add_bullet(doc, "Plants and weather stations are joined mathematically using plant GPS coordinates (within 50 km) and clock hours (+/- 60 min).", "Key 4: Spatial-Temporal Match (Haversine Distance): ")

    add_h1(doc, "5. Our Five Dimensions and Three Fact Tables at a Glance")
    add_body(doc, "To see the complete architecture in one unified table, here is the Kimball dimensional layout:")
    
    dim_sum_hdr = ["Object Type", "Table Name", "Natural / Source Key", "Key Attributes & Measures"]
    dim_sum_w = [Inches(1.2), Inches(1.8), Inches(1.4), Inches(2.4)]
    dim_sum_rows = [
        ["Dimension", "dim_date", "calendar_date", "Date_Key (YYYYMMDD), Year, Quarter, Month, Day, Is_Weekend"],
        ["Dimension", "dim_plant", "orispl_code (ORISPL)", "Plant_Name, Utility, Latitude, Longitude, State, County, BA_Code"],
        ["Dimension (SCD 2)", "dim_generator", "generator_id + orispl", "Technology, Fuel, Nameplate_MW, Operating_Status, Effective/Expiration Dates"],
        ["Dimension", "dim_balancing_authority", "ba_code", "BA_Code (ERCO, PJM, etc.), BA_Name, Regional Interconnect, Active Flag"],
        ["Dimension", "dim_weather_station", "station_id (USAF-WBAN)", "Station_Name, State, Latitude, Longitude, Elevation_m"],
        ["Fact (Transactional)", "fact_hourly_emissions_weather", "Stack Unit + Timestamp", "Gross_MW, Heat_Input_MMBtu, SO2_lbs, NOx_lbs, CO2_tons, Temp_C, Wind_Speed"],
        ["Fact (Snapshot)", "fact_monthly_plant_operations", "Plant + Prime Mover + Month", "Net_Generation_MWh, Fuel_Consumed_MMBtu, Heat_Rate, Fuel_Cost_$/MMBtu, Fuel_Stock"],
        ["Fact (Aggregate)", "fact_regional_grid_demand", "BA + Timestamp", "Demand_MW, Forecast_MW, Coal_MW, Gas_MW, Nuclear_MW, Wind_MW, Solar_MW"]
    ]
    tbl_dsum = doc.add_table(rows=1, cols=4)
    format_table(tbl_dsum, dim_sum_w, dim_sum_hdr, dim_sum_rows)

    add_h1(doc, "6. Cross-Source Engineering Synergies")
    add_body(doc, "Connecting these sources allows us to perform powerful cross-agency analyses that are impossible with isolated datasets:")
    add_bullet(doc, "Physical law dictates that Net Generation (EIA) can never exceed Gross Generation (EPA) because plants consume power internally. Our pipeline automatically audits this relationship.", "1. The Conservation of Energy Audit: ")
    add_bullet(doc, "By dividing EPA pollutant emissions by EIA net electricity generation, we calculate true Emissions Intensity (lbs of CO2 per MWh) for every power plant in the country.", "2. True Emissions Intensity: ")
    add_bullet(doc, "We combine NOAA temperatures with EIA heat rates to show how extreme summer temperatures degrade turbine efficiency and increase fuel consumption.", "3. Weather Stress Analysis: ")

    doc.save(output_path)
    print(f"Document 2 generated: {output_path}")

# ==============================================================================
# 3. BUILD DOCUMENT 3: TECHNICAL DATA ENGINEERING DEEP DIVE (WITH COMPLETE TABLES)
# ==============================================================================
def build_doc3(output_path):
    doc = create_document()
    add_header_title(doc, 
                     "Technical Data Engineering Deep Dive: Pipeline, Ingestion & Schemas", 
                     "Developer Reference for Ingestion Protocols, Table Schemas, Dimensions, and Fact Models")
    
    add_h1(doc, "1. Ingestion Protocols: How Each Source is Extracted")
    add_body(doc, "Each source presents unique extraction protocols, data formats, and defensive ingestion requirements:")
    
    headers = ["Source", "Ingestion Method", "Protocol / Tool", "Upstream Engineering Quirks"]
    widths = [Inches(1.0), Inches(1.3), Inches(1.4), Inches(2.7)]
    rows = [
        ["EIA-930", "REST API / CSV", "Python requests", "Hourly pagination; late-arriving settlement revisions."],
        ["EPA CAMPD", "Bulk CSV Portal", "Direct CSV extract", "Massive volume; common stack apportionment; quarterly resubmissions."],
        ["EIA-860", "Multi-tab Excel", "openpyxl / pandas", "Title on Row 1; column headers begin dynamically on Row 2."],
        ["EIA-923", "Multi-tab Excel", "openpyxl / pandas", "Metadata on Rows 1-5; headers on Row 6; '.' and 'NM' sentinels; wide monthly layout."],
        ["Crosswalk", "Static CSV", "pandas DataFrame", "Many-to-many bipartite adjacency mapping; prevents Cartesian products."],
        ["NOAA ISD", "Fixed-Width / CSV", "Regex parser", "Integer -9999 sentinels; quality flags appended directly to numeric strings."]
    ]
    tbl = doc.add_table(rows=1, cols=4)
    format_table(tbl, widths, headers, rows)

    add_h1(doc, "2. Data Volume, Sizing & Local Performance Strategy")
    add_body(doc, "A critical data engineering responsibility is sizing the workload so it runs reliably on developer laptops without memory crashes, while still exceeding all academic project rubric requirements:")
    
    v_headers = ["Scope Level", "Generating Assets", "Time Horizon", "Raw Row Count", "Pipeline Sizing"]
    v_widths = [Inches(1.3), Inches(1.2), Inches(1.2), Inches(1.4), Inches(1.3)]
    v_rows = [
        ["National Total (U.S.)", "12,300+ plants / 3,500 units", "Full Year (8,760 hrs)", "~30 Million rows", "3.5 GB (Needs distributed cluster)"],
        ["Phase 2 Scoped Batch", "254 profiled plants (~600 units)", "1 Target Month (720 hrs)", "~432,000 rows", "~45 MB (Sub-second on PostgreSQL)"],
        ["Course Minimum", "Dimensions: >= 100", "Facts: >= 10,000", ">= 10,000 rows", "Standard Lab requirement"]
    ]
    tbl_v = doc.add_table(rows=1, cols=5)
    format_table(tbl_v, v_widths, v_headers, v_rows)
    
    add_callout(doc, 
                "By bounding our extraction to ~254 profiled thermal plants with complex boiler configurations across key states (e.g., Texas ERCOT and PJM) over a 1 to 3 month window, our fact tables contain between 100,000 and 500,000 rows. This comfortably crushes the 10,000 row requirement while running in under 5 seconds on our local PostgreSQL instances.", 
                "Sizing Strategy")

    add_h1(doc, "3. Bronze Staging Architecture & Defensive Typing")
    add_body(doc, "All raw feeds land in the 'project_staging' schema. To ensure that an unannounced format change or malformed character never breaks the initial load, all incoming business columns are stored as VARCHAR. In addition, every Bronze table carries two mandatory audit columns: batch_id (UUID) and ingested_at (TIMESTAMP WITH TIME ZONE).")
    
    add_h1(doc, "4. The Kimball Bus Matrix (Architecture Blueprint)")
    add_body(doc, "The Bus Matrix shows exactly how our five conformed dimensions connect across our three Kimball fact table archetypes:")
    
    bm_headers = ["Fact Table Archetype", "Fact Table Name", "Dim Date", "Dim Plant", "Dim Generator", "Dim BA", "Dim Weather Station"]
    bm_widths = [Inches(1.5), Inches(1.7), Inches(0.6), Inches(0.6), Inches(0.7), Inches(0.6), Inches(0.7)]
    bm_rows = [
        ["Transactional Fact", "fact_hourly_emissions_weather", "✓", "✓", "✓ (via link)", "―", "✓"],
        ["Periodic Snapshot Fact", "fact_monthly_plant_operations", "✓", "✓", "―", "―", "―"],
        ["Aggregate Grid Fact", "fact_regional_grid_demand", "✓", "―", "―", "✓", "―"]
    ]
    tbl_bm = doc.add_table(rows=1, cols=7)
    format_table(tbl_bm, bm_widths, bm_headers, bm_rows)

    add_h1(doc, "5. Conformed Dimensions & Attribute Catalogs")
    add_body(doc, "The following tables define the physical schema and complete attribute list for each dimension in 'project_dw':")

    # Table 5.1: Dim_Date
    add_h2(doc, "Dimension 1: Dim_Date (Calendar Dimension)")
    add_body(doc, "Provides date rollups from day up to calendar quarter and year. Uses a smart integer YYYYMMDD primary key.")
    d_date_hdr = ["Column Name", "SQL Type", "Constraint", "Nullable", "Description & Sample Values"]
    d_date_w = [Inches(1.4), Inches(1.0), Inches(0.9), Inches(0.7), Inches(2.4)]
    d_date_rows = [
        ["date_key", "INTEGER", "PK", "NO", "Smart integer date key (e.g., 20230115)"],
        ["calendar_date", "DATE", "UNIQUE", "NO", "Standard calendar date (e.g., 2023-01-15)"],
        ["calendar_year", "SMALLINT", "―", "NO", "Four-digit calendar year (e.g., 2023)"],
        ["calendar_quarter", "SMALLINT", "―", "NO", "Calendar quarter (1, 2, 3, 4)"],
        ["calendar_month", "SMALLINT", "―", "NO", "Month number (1 to 12)"],
        ["month_name", "VARCHAR(15)", "―", "NO", "Full English month name (e.g., 'January')"],
        ["day_of_month", "SMALLINT", "―", "NO", "Day of the month (1 to 31)"],
        ["day_of_week", "SMALLINT", "―", "NO", "Day of the week (1 = Sunday, 7 = Saturday)"],
        ["day_name", "VARCHAR(10)", "―", "NO", "English day name (e.g., 'Sunday', 'Monday')"],
        ["is_weekend", "BOOLEAN", "―", "NO", "TRUE if Saturday or Sunday, else FALSE"]
    ]
    tbl_dd = doc.add_table(rows=1, cols=5)
    format_table(tbl_dd, d_date_w, d_date_hdr, d_date_rows)

    # Table 5.2: Dim_Plant
    add_h2(doc, "Dimension 2: Dim_Plant (Power Plant Facilities)")
    add_body(doc, "Master facility directory holding plant names, utility ownership, and spatial coordinates. Master natural key is orispl_code.")
    d_pl_hdr = ["Column Name", "SQL Type", "Constraint", "Nullable", "Description & Sample Values"]
    d_pl_w = [Inches(1.4), Inches(1.0), Inches(0.9), Inches(0.7), Inches(2.4)]
    d_pl_rows = [
        ["plant_key", "SERIAL", "PK", "NO", "Surrogate primary key (1, 2, 3...)"],
        ["orispl_code", "INTEGER", "UNIQUE", "NO", "Official federal plant identifier (e.g., 3470, 8102)"],
        ["plant_name", "VARCHAR(150)", "―", "NO", "Official plant name (e.g., 'W A Parish', 'Gavin')"],
        ["utility_id", "INTEGER", "―", "YES", "Utility operating entity identifier (e.g., 13315)"],
        ["utility_name", "VARCHAR(150)", "―", "YES", "Utility company name (e.g., 'NRG Texas Power LLC')"],
        ["latitude", "NUMERIC(9,6)", "―", "YES", "Geodetic latitude coordinate (e.g., 29.484200)"],
        ["longitude", "NUMERIC(9,6)", "―", "YES", "Geodetic longitude coordinate (e.g., -95.632200)"],
        ["state_code", "CHAR(2)", "―", "NO", "Two-letter state postal code (e.g., 'TX', 'OH')"],
        ["county_name", "VARCHAR(100)", "―", "YES", "County name (e.g., 'Fort Bend', 'Gallia')"],
        ["ba_code", "VARCHAR(20)", "―", "YES", "Balancing Authority regional grid code (e.g., 'ERCO')"],
        ["epa_region", "SMALLINT", "―", "YES", "EPA regional office jurisdiction (1 to 10)"],
        ["is_combined_heat_power", "BOOLEAN", "DEFAULT FALSE", "NO", "TRUE if facility co-generates industrial steam"]
    ]
    tbl_pl = doc.add_table(rows=1, cols=5)
    format_table(tbl_pl, d_pl_w, d_pl_hdr, d_pl_rows)

    # Table 5.3: Dim_Generator
    add_h2(doc, "Dimension 3: Dim_Generator (Slowly Changing Dimension Type 2)")
    add_body(doc, "Tracks individual generating machines, prime mover technology, fuel type, capacity, and operational status transitions.")
    d_gn_hdr = ["Column Name", "SQL Type", "Constraint", "Nullable", "SCD Type 2 Role & Description"]
    d_gn_w = [Inches(1.5), Inches(1.0), Inches(0.8), Inches(0.7), Inches(2.4)]
    d_gn_rows = [
        ["generator_key", "SERIAL", "PK", "NO", "Surrogate primary key (SCD 2 surrogate)"],
        ["orispl_code", "INTEGER", "FK", "NO", "Plant foreign key matching dim_plant(orispl_code)"],
        ["generator_id", "VARCHAR(20)", "―", "NO", "Machine identifier (e.g., '1', '2', 'CTG1', 'ST1')"],
        ["prime_mover_code", "VARCHAR(10)", "―", "NO", "Turbine technology (ST=Steam, GT=Gas, CC=Comb Cycle)"],
        ["primary_energy_source", "VARCHAR(10)", "―", "NO", "Primary fuel code (BIT=Coal, NG=Gas, NUC=Nuclear)"],
        ["nameplate_capacity_mw", "NUMERIC(10,2)", "―", "YES", "Maximum rated electrical capacity (e.g., 560.00)"],
        ["operating_status", "VARCHAR(30)", "―", "NO", "Monitored SCD 2 status: 'OP' (Operating), 'RE' (Retired)"],
        ["row_effective_date", "DATE", "―", "NO", "SCD 2 Start Date (e.g., 1977-01-01)"],
        ["row_expiration_date", "DATE", "DEFAULT 9999-12-31", "NO", "SCD 2 End Date ('9999-12-31' if currently active)"],
        ["is_current", "BOOLEAN", "DEFAULT TRUE", "NO", "SCD 2 Current Flag: TRUE for active record, else FALSE"]
    ]
    tbl_gn = doc.add_table(rows=1, cols=5)
    format_table(tbl_gn, d_gn_w, d_gn_hdr, d_gn_rows)

    # Table 5.4: Dim_Balancing_Authority
    add_h2(doc, "Dimension 4: Dim_Balancing_Authority (Regional Grid Operators)")
    add_body(doc, "Regional grid transmission operators responsible for balancing regional electrical supply and demand.")
    d_ba_hdr = ["Column Name", "SQL Type", "Constraint", "Nullable", "Description & Sample Values"]
    d_ba_w = [Inches(1.4), Inches(1.0), Inches(0.9), Inches(0.7), Inches(2.4)]
    d_ba_rows = [
        ["ba_key", "SERIAL", "PK", "NO", "Surrogate primary key"],
        ["ba_code", "VARCHAR(20)", "UNIQUE", "NO", "Official BA code (e.g., 'ERCO', 'PJM', 'CISO', 'MISO')"],
        ["ba_name", "VARCHAR(150)", "―", "NO", "Full name (e.g., 'Electric Reliability Council of Texas')"],
        ["region", "VARCHAR(50)", "―", "YES", "Interconnection territory (e.g., 'Texas', 'Eastern', 'Western')"],
        ["is_active", "BOOLEAN", "DEFAULT TRUE", "YES", "TRUE if the balancing authority is actively dispatching"]
    ]
    tbl_ba = doc.add_table(rows=1, cols=5)
    format_table(tbl_ba, d_ba_w, d_ba_hdr, d_ba_rows)

    # Table 5.5: Dim_Weather_Station
    add_h2(doc, "Dimension 5: Dim_Weather_Station (NOAA Weather Observatories)")
    add_body(doc, "Automated ground stations (ASOS / AWOS) providing synoptic meteorological observations within 50 km of power plants.")
    d_ws_hdr = ["Column Name", "SQL Type", "Constraint", "Nullable", "Description & Sample Values"]
    d_ws_w = [Inches(1.4), Inches(1.0), Inches(0.9), Inches(0.7), Inches(2.4)]
    d_ws_rows = [
        ["station_key", "SERIAL", "PK", "NO", "Surrogate primary key"],
        ["station_id", "VARCHAR(25)", "UNIQUE", "NO", "NOAA USAF-WBAN identifier (e.g., '72059400188')"],
        ["station_name", "VARCHAR(150)", "―", "YES", "Station name (e.g., 'HOUSTON SUGARLAND AP')"],
        ["state_code", "CHAR(2)", "―", "YES", "State postal code (e.g., 'TX', 'OH')"],
        ["latitude", "NUMERIC(9,6)", "―", "YES", "Station latitude coordinate (e.g., 29.622200)"],
        ["longitude", "NUMERIC(9,6)", "―", "YES", "Station longitude coordinate (e.g., -95.656500)"],
        ["elevation_m", "NUMERIC(7,2)", "―", "YES", "Station elevation above sea level in meters (e.g., 25.00)"]
    ]
    tbl_ws = doc.add_table(rows=1, cols=5)
    format_table(tbl_ws, d_ws_w, d_ws_hdr, d_ws_rows)

    add_h1(doc, "6. Fact Table Catalogs & Measure Archetypes")
    add_body(doc, "The warehouse implements Kimball's three distinct fact table archetypes:")

    # Table 6.1: Fact 1
    add_h2(doc, "Fact 1: fact_hourly_emissions_weather (Transactional Fact - Partitioned)")
    add_body(doc, "Grain: One row per smokestack unit at a facility per clock hour. Range-partitioned by date_key for query performance.")
    f1_hdr = ["Column Name", "SQL Type", "Role / Constraint", "Description & Units"]
    f1_w = [Inches(1.6), Inches(1.1), Inches(1.3), Inches(2.4)]
    f1_rows = [
        ["date_key", "INTEGER", "PK, FK to dim_date", "Calendar date identifier (YYYYMMDD)"],
        ["hour_of_day", "SMALLINT", "PK (0 to 23)", "Clock hour of observation"],
        ["plant_key", "INTEGER", "PK, FK to dim_plant", "Power plant facility surrogate key"],
        ["unit_id", "VARCHAR(20)", "PK (Natural)", "Smokestack / Boiler unit identifier"],
        ["station_key", "INTEGER", "FK to dim_weather", "Nearest NOAA weather station surrogate key"],
        ["gross_load_mw", "NUMERIC(10,2)", "Additive Measure", "Gross electrical power generated in Megawatts"],
        ["heat_input_mmbtu", "NUMERIC(12,3)", "Additive Measure", "Thermal heat released by fuel combustion (MMBtu)"],
        ["so2_mass_lbs", "NUMERIC(12,3)", "Additive Measure", "Sulfur dioxide emissions mass in pounds"],
        ["nox_mass_lbs", "NUMERIC(12,3)", "Additive Measure", "Nitrogen oxides emissions mass in pounds"],
        ["co2_mass_tons", "NUMERIC(12,3)", "Additive Measure", "Carbon dioxide emissions mass in short tons"],
        ["ambient_temp_celsius", "NUMERIC(5,2)", "Non-additive Measure", "NOAA surface air temperature in degrees Celsius"],
        ["wind_speed_mps", "NUMERIC(5,2)", "Non-additive Measure", "NOAA surface wind speed in meters per second"],
        ["weather_distance_km", "NUMERIC(6,2)", "Non-additive Measure", "Haversine distance from plant to station (km)"]
    ]
    tbl_f1 = doc.add_table(rows=1, cols=4)
    format_table(tbl_f1, f1_w, f1_hdr, f1_rows)

    # Table 6.2: Fact 2
    add_h2(doc, "Fact 2: fact_monthly_plant_operations (Periodic Snapshot Fact)")
    add_body(doc, "Grain: One row per plant, prime mover, and energy source for one calendar month.")
    f2_hdr = ["Column Name", "SQL Type", "Role / Constraint", "Description & Units"]
    f2_w = [Inches(1.7), Inches(1.1), Inches(1.3), Inches(2.3)]
    f2_rows = [
        ["snapshot_key", "SERIAL", "PK (Surrogate)", "Unique monthly snapshot identifier"],
        ["month_start_date_key", "INTEGER", "FK to dim_date", "First day of reporting month (YYYYMM01)"],
        ["plant_key", "INTEGER", "FK to dim_plant", "Power plant facility surrogate key"],
        ["prime_mover_code", "VARCHAR(10)", "Attribute", "Turbine engine technology (ST, GT, CC, etc.)"],
        ["energy_source_code", "VARCHAR(10)", "Attribute", "Energy source consumed (BIT, SUB, NG, etc.)"],
        ["net_generation_mwh", "NUMERIC(14,3)", "Additive Measure", "Net electricity sent to grid (May be negative during outages!)"],
        ["fuel_consumed_physical", "NUMERIC(14,3)", "Additive (Single Unit)", "Physical fuel volume (Tons, Barrels, Mcf)"],
        ["fuel_consumed_mmbtu", "NUMERIC(14,3)", "Additive Measure", "Total heat energy consumed in MMBtu"],
        ["avg_heat_rate_btu_kwh", "NUMERIC(10,2)", "Non-additive Ratio", "Fuel heat rate efficiency (Recomputed from sums)"],
        ["delivered_fuel_cost_per_mmbtu", "NUMERIC(8,2)", "Non-additive Metric", "Average delivered fuel price in $/MMBtu"],
        ["ending_fuel_stock_physical", "NUMERIC(14,3)", "Semi-additive Measure", "Fuel stored on-site at month end (Not summed over time)"]
    ]
    tbl_f2 = doc.add_table(rows=1, cols=4)
    format_table(tbl_f2, f2_w, f2_hdr, f2_rows)

    # Table 6.3: Fact 3
    add_h2(doc, "Fact 3: fact_regional_grid_demand (Aggregate Grid Fact)")
    add_body(doc, "Grain: One row per balancing authority regional grid operator for one clock hour.")
    f3_hdr = ["Column Name", "SQL Type", "Role / Constraint", "Description & Units"]
    f3_w = [Inches(1.6), Inches(1.1), Inches(1.3), Inches(2.4)]
    f3_rows = [
        ["date_key", "INTEGER", "PK, FK to dim_date", "Calendar date identifier (YYYYMMDD)"],
        ["hour_of_day", "SMALLINT", "PK (0 to 23)", "Clock hour of observation"],
        ["ba_key", "INTEGER", "PK, FK to dim_ba", "Balancing Authority regional grid operator surrogate key"],
        ["demand_mw", "NUMERIC(12,2)", "Additive Measure", "Total electrical demand / customer load in Megawatts"],
        ["demand_forecast_mw", "NUMERIC(12,2)", "Additive Measure", "Day-ahead forecasted electricity demand (MW)"],
        ["net_gen_coal_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional power generation from coal (MW)"],
        ["net_gen_gas_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional power generation from natural gas (MW)"],
        ["net_gen_nuclear_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional power generation from nuclear (MW)"],
        ["net_gen_hydro_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional power generation from hydro (MW)"],
        ["net_gen_wind_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional renewable power from wind (MW)"],
        ["net_gen_solar_mw", "NUMERIC(12,2)", "Additive Measure", "Real-time regional renewable power from solar (MW)"],
        ["net_interchange_mw", "NUMERIC(12,2)", "Additive Measure", "Net power imported/exported across regional ties (MW)"]
    ]
    tbl_f3 = doc.add_table(rows=1, cols=4)
    format_table(tbl_f3, f3_w, f3_hdr, f3_rows)

    add_h1(doc, "7. Reporting Layer & Power BI Dashboard Mapping")
    add_body(doc, "The dimensional model directly feeds three curated views in 'project_reporting', which connect directly to our 3-page Power BI dashboard:")
    add_bullet(doc, "Rolls up emissions and net generation to compute CO2/SO2/NOx intensity per MWh by plant, state, and month. Feeds Page 1 (Executive Overview).", "vw_emissions_intensity: ")
    add_bullet(doc, "Calculates monthly heat rate efficiency, delivered fuel costs, and identifies offline plants with negative net generation. Feeds Page 2 (Detailed Engineering Analysis).", "vw_plant_performance: ")
    add_bullet(doc, "Aggregates regional grid demand peaks, fuel dispatch mix, and renewable penetration percentages. Feeds Page 3 (Grid Decision Support).", "vw_monthly_generation: ")

    doc.save(output_path)
    print(f"Document 3 generated: {output_path}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "01_Project_Documentation", "Team_Guides")
    os.makedirs(out_dir, exist_ok=True)
    
    file1 = os.path.join(out_dir, "01_Project_Introduction_and_Overview.docx")
    file2 = os.path.join(out_dir, "02_Data_Sources_and_Connections_Guide.docx")
    file3 = os.path.join(out_dir, "03_Technical_Data_Engineering_Deep_Dive.docx")
    
    build_doc1(file1)
    build_doc2(file2)
    build_doc3(file3)
    
    print("\nAll 3 Team Onboarding Guides successfully re-built with rich tables!")
