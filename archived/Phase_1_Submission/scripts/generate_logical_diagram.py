import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)

def create_logical_model():
    # Ultra-wide, high-resolution canvas with generous spacing: 28 x 16.5 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(28, 16.5), dpi=300)
    ax.set_xlim(0, 28)
    ax.set_ylim(0, 16.5)
    ax.axis('off')

    # Premium slate background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Title Banner
    ax.text(14.0, 15.8, "U.S. Bulk Power & Emissions Lakehouse: Logical Dimensional Model", 
            fontsize=22, fontweight='bold', ha='center', color='#0F172A', fontfamily='sans-serif')
    ax.text(14.0, 15.35, "Enterprise Kimball Bus Architecture: Conformed Dimensions, Multi-Grain Fact Archetypes & Bus Cardinalities", 
            fontsize=12.5, style='italic', ha='center', color='#475569', fontfamily='sans-serif')

    def draw_table(x, y, w, h, title, items, header_color, bg_color='#FFFFFF', border_color='#CBD5E1'):
        # Container Box
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                             facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        # Header banner
        header = FancyBboxPatch((x, y + h - 0.8), w, 0.8, boxstyle="round,pad=0.08,rounding_size=0.15",
                                facecolor=header_color, edgecolor=header_color, linewidth=1.5)
        ax.add_patch(header)
        ax.fill([x, x+w, x+w, x], [y+h-0.8, y+h-0.8, y+h-0.5, y+h-0.5], color=header_color)
        ax.text(x + w/2, y + h - 0.45, title, fontsize=11, fontweight='bold', ha='center', va='center', color='#FFFFFF')

        # Items
        line_y = y + h - 1.2
        for item in items:
            prefix, name, desc = item
            if prefix == "PK":
                color_p = '#B91C1C'
                fw = 'bold'
            elif prefix == "FK":
                color_p = '#1D4ED8'
                fw = 'bold'
            elif prefix == "UK":
                color_p = '#B45309'
                fw = 'bold'
            elif prefix == "M":
                color_p = '#047857'
                fw = 'bold'
            elif prefix == "G":
                # Grain banner inside box
                gb = FancyBboxPatch((x + 0.15, line_y - 0.15), w - 0.3, 0.42, boxstyle="round,pad=0.03,rounding_size=0.08",
                                    facecolor='#F3E8FF', edgecolor='#D8B4FE', lw=1.0)
                ax.add_patch(gb)
                ax.text(x + 0.3, line_y + 0.06, f"MANDATORY GRAIN DECLARATION:", fontsize=8.0, fontweight='bold', color='#6B21A8', va='center')
                ax.text(x + 0.3, line_y - 0.10, desc, fontsize=8.2, color='#581C87', va='center', fontweight='medium')
                line_y -= 0.58
                continue
            else:
                color_p = '#64748B'
                fw = 'normal'

            ax.text(x + 0.3, line_y, prefix, fontsize=8.5, fontweight=fw, color=color_p, va='center')
            ax.text(x + 1.05, line_y, name, fontsize=8.8, fontweight='medium', color='#1E293B', va='center')
            if desc:
                ax.text(x + w - 0.3, line_y, desc, fontsize=8.2, color='#64748B', ha='right', va='center', style='italic')
            line_y -= 0.38

    # =========================================================================
    # TIER 1: CONFORMED DIMENSIONS (TOP ROW - Y: 10.0 to 14.9)
    # Five distinct horizontal blocks with wide separation (1.8 unit gap Plant->Gen)
    # =========================================================================
    
    # 1. Dim Date
    date_items = [
        ("PK", "Date_Key", "Surrogate [YYYYMMDD]"),
        ("UK", "Calendar_Date", "Natural Key [Date]"),
        ("", "Calendar_Year", "Hierarchy Level 1"),
        ("", "Calendar_Quarter", "Hierarchy Level 2"),
        ("", "Calendar_Month", "Hierarchy Level 3"),
        ("", "Month_Name", "Jan - Dec"),
        ("", "Day_Of_Month", "1 - 31"),
        ("", "Day_Of_Week", "1 - 7"),
        ("", "Day_Name", "Monday - Sunday"),
        ("", "Is_Weekend_Flag", "True / False")
    ]
    draw_table(0.8, 10.0, 4.8, 4.9, "DIM_DATE (Conformed)", date_items, '#475569')

    # 2. Dim Plant (ends at 5.8 + 4.8 = 10.6)
    plant_items = [
        ("PK", "Plant_Key", "Surrogate Identifier"),
        ("UK", "ORISPL_Code", "Universal Natural Key"),
        ("", "Plant_Name", "Standardized Title"),
        ("", "Utility_ID", "Parent Owner"),
        ("", "Utility_Name", "Operating Utility"),
        ("", "Latitude / Longitude", "GPS Coordinates"),
        ("", "State_Code", "State Postal Code"),
        ("", "County_Name", "County Jurisdiction"),
        ("", "Balancing_Auth_Code", "Grid ISO / RTO Link"),
        ("", "EPA_Region", "Administrative Region"),
        ("", "Is_Combined_Heat_Power", "Cogeneration Flag")
    ]
    draw_table(5.8, 9.8, 4.8, 5.1, "DIM_PLANT (Conformed)", plant_items, '#0284C7')

    # 3. Dim Generator (SCD Type 2 Outrigger) - starts at 12.4 (1.8-unit gap)
    gen_items = [
        ("PK", "Generator_Key", "Surrogate Identifier"),
        ("FK", "ORISPL_Code", "Link to Master Plant"),
        ("UK", "Generator_ID", "Physical Asset Code"),
        ("", "Prime_Mover_Code", "Turbine / Engine Type"),
        ("", "Primary_Energy_Source", "Combustion Fuel Code"),
        ("", "Nameplate_Capacity_MW", "Rated Maximum MW"),
        ("", "Operating_Status", "OP, SB, RE (SCD-2)"),
        ("", "Row_Effective_Date", "SCD Type 2 Start"),
        ("", "Row_Expiration_Date", "SCD Type 2 End / NULL"),
        ("", "Is_Current_Flag", "True = Active Lifecycle")
    ]
    draw_table(12.4, 10.0, 4.7, 4.9, "DIM_GENERATOR (SCD Type 2)", gen_items, '#7C3AED')

    # 4. Dim Weather Station
    ws_items = [
        ("PK", "Station_Key", "Surrogate Identifier"),
        ("UK", "Station_ID", "USAF-WBAN Composite"),
        ("", "Station_Name", "NOAA Synoptic Location"),
        ("", "State_Code", "Geographic Territory"),
        ("", "Latitude / Longitude", "Station Coordinates"),
        ("", "Elevation_Meters", "Height Above Sea Level")
    ]
    draw_table(17.5, 11.2, 4.6, 3.7, "DIM_WEATHER_STATION", ws_items, '#0D9488')

    # 5. Dim Balancing Authority
    ba_items = [
        ("PK", "BA_Key", "Surrogate Identifier"),
        ("UK", "BA_Code", "ISO/RTO (PJM, CISO..)"),
        ("", "BA_Name", "Grid Operator Title"),
        ("", "Interconnection", "Eastern, Western, Texas"),
        ("", "Is_Active_Flag", "Operational Status")
    ]
    draw_table(22.5, 11.6, 4.8, 3.3, "DIM_BALANCING_AUTH", ba_items, '#D97706')

    # =========================================================================
    # TIER 2: KIMBALL FACT TABLES (BOTTOM ROW - Y: 0.8 to 7.6)
    # Three spacious fact tables with generous column widths and zero collision
    # =========================================================================

    # 6. Fact Hourly Emissions & Weather (Transactional Fact)
    emiss_items = [
        ("G", "One row per generating unit per clock hour", ""),
        ("FK", "Date_Key", "Join to DIM_DATE"),
        ("FK", "Plant_Key", "Join to DIM_PLANT"),
        ("FK", "Station_Key", "Join to DIM_WEATHER_STATION"),
        ("PK", "Hour_Of_Day", "0 - 23 Hourly Grain"),
        ("PK", "Unit_ID", "Smokestack CEMS Unit"),
        ("M", "Gross_Load_MW", "Additive (Total Generation)"),
        ("M", "Heat_Input_MMBtu", "Additive (Fuel Thermal Energy)"),
        ("M", "SO2_Mass_Lbs", "Additive (Sulfur Dioxide)"),
        ("M", "NOx_Mass_Lbs", "Additive (Nitrogen Oxides)"),
        ("M", "CO2_Mass_Tons", "Additive (Carbon Dioxide)"),
        ("M", "Ambient_Temp_Celsius", "Non-Additive (Averaged)"),
        ("M", "Wind_Speed_MPS", "Non-Additive (Averaged)"),
        ("M", "Weather_Distance_KM", "Spatial Lineage (<= 50km)")
    ]
    draw_table(0.8, 0.8, 8.4, 6.8, "FACT_HOURLY_EMISSIONS_WEATHER (Transactional Fact)", 
               emiss_items, '#059669', bg_color='#F0FDF4')

    # 7. Fact Monthly Plant Operations (Periodic Snapshot Fact)
    monthly_items = [
        ("G", "One row per plant, prime mover, and fuel per month", ""),
        ("PK", "Snapshot_Key", "Surrogate Periodic Identifier"),
        ("FK", "Month_Start_Date_Key", "Join to DIM_DATE"),
        ("FK", "Plant_Key", "Join to DIM_PLANT"),
        ("", "Prime_Mover_Code", "Degenerate Turbine Code"),
        ("", "Energy_Source_Code", "Degenerate Fuel Code"),
        ("M", "Net_Generation_MWh", "Additive (Can be Negative)"),
        ("M", "Fuel_Consumed_MMBtu", "Additive (Thermal Energy)"),
        ("M", "Fuel_Consumed_Physical", "Semi-Additive (Tons / Mcf)"),
        ("M", "Avg_Heat_Rate_Btu_kWh", "Non-Additive Ratio (Eff.)"),
        ("M", "Delivered_Fuel_Cost_MMBtu", "Non-Additive Ratio ($/MMBtu)"),
        ("M", "Ending_Fuel_Stock", "Semi-Additive Snapshot Balance")
    ]
    draw_table(9.6, 0.8, 8.6, 6.0, "FACT_MONTHLY_PLANT_OPS (Periodic Snapshot)", 
               monthly_items, '#059669', bg_color='#F0FDF4')

    # 8. Fact Regional Grid Demand (Aggregate Grid Fact)
    grid_items = [
        ("G", "One row per balancing authority per clock hour", ""),
        ("FK", "Date_Key", "Join to DIM_DATE"),
        ("FK", "BA_Key", "Join to DIM_BALANCING_AUTH"),
        ("PK", "Hour_Of_Day", "0 - 23 Hourly Grain"),
        ("M", "Demand_MW", "Additive Consumer Load"),
        ("M", "Demand_Forecast_MW", "Day-Ahead Forecasted Load"),
        ("M", "Net_Gen_Coal_MW", "Coal Generation Dispatch"),
        ("M", "Net_Gen_Gas_MW", "Natural Gas Dispatch"),
        ("M", "Net_Gen_Nuclear_MW", "Nuclear Baseload Dispatch"),
        ("M", "Net_Gen_Hydro_MW", "Hydroelectric Dispatch"),
        ("M", "Net_Gen_Wind_MW", "Clean Renewable Wind"),
        ("M", "Net_Gen_Solar_MW", "Clean Renewable Solar"),
        ("M", "Net_Interchange_MW", "Imports (+) / Exports (-)")
    ]
    draw_table(18.6, 0.8, 8.6, 6.4, "FACT_REGIONAL_GRID_DEMAND (Aggregate Grid)", 
               grid_items, '#D97706', bg_color='#FFFBEB')

    # =========================================================================
    # RELATIONSHIP ROUTING (MIDDLE CORRIDOR - Y: 7.6 to 9.8)
    # Clean orthogonal and direct elbow paths with zero text collisions
    # =========================================================================
    def draw_path(points, label="", color='#64748B', label_pos=None):
        xs, ys = zip(*points)
        ax.plot(xs, ys, color=color, lw=1.6, zorder=3)
        if label:
            if label_pos:
                lx, ly = label_pos
            else:
                mid_idx = len(points) // 2
                lx = (points[mid_idx-1][0] + points[mid_idx][0]) / 2
                ly = (points[mid_idx-1][1] + points[mid_idx][1]) / 2
            ax.text(lx, ly, label, fontsize=8.2, color=color, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=color, lw=0.9, zorder=4))

    # 1. Plant to Generator Outrigger (Horizontal bridge across 1.8-unit gap)
    draw_path([(10.6, 12.2), (12.4, 12.2)], "1 : M (SCD2)", '#7C3AED', label_pos=(11.5, 12.2))

    # 2. Plant to Fact Emissions (Clean elbow)
    draw_path([(7.2, 9.8), (7.2, 8.8), (4.8, 8.8), (4.8, 7.6)], "1 : M", '#0284C7', label_pos=(6.0, 8.8))

    # 3. Plant to Fact Monthly (Clean elbow)
    draw_path([(9.0, 9.8), (9.0, 8.2), (13.0, 8.2), (13.0, 6.8)], "1 : M", '#0284C7', label_pos=(11.0, 8.2))

    # 4. Date to Fact Emissions (Direct vertical drop)
    draw_path([(2.6, 10.0), (2.6, 7.6)], "1 : M", '#475569', label_pos=(2.6, 8.8))

    # 5. Date to Fact Monthly (Corridor routing)
    draw_path([(3.8, 10.0), (3.8, 9.2), (10.8, 9.2), (10.8, 6.8)], "1 : M", '#475569', label_pos=(7.3, 9.2))

    # 6. Date to Fact Grid (High corridor routing)
    draw_path([(4.5, 10.0), (4.5, 9.6), (20.5, 9.6), (20.5, 7.2)], "1 : M", '#475569', label_pos=(15.5, 9.6))

    # 7. Weather Station to Fact Emissions (Low corridor routing)
    draw_path([(18.5, 11.2), (18.5, 8.5), (6.5, 8.5), (6.5, 7.6)], "1 : M", '#0D9488', label_pos=(13.5, 8.5))

    # 8. Balancing Authority to Fact Grid (Direct vertical drop)
    draw_path([(24.5, 11.6), (24.5, 7.2)], "1 : M", '#D97706', label_pos=(24.5, 9.4))

    plt.tight_layout()
    output_path = os.path.join(SUBMISSION_DIR, "Logical_Model_Diagram.png")
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Successfully generated clear {output_path}")

if __name__ == "__main__":
    create_logical_model()
