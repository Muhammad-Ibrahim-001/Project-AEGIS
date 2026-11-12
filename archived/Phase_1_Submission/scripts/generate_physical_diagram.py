import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)

def create_physical_model():
    # Ultra-wide, high-resolution canvas with generous spacing: 30 x 18 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(30, 18), dpi=300)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 18)
    ax.axis('off')

    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Title Banner
    ax.text(15.0, 17.3, "U.S. Bulk Power & Emissions Lakehouse: Physical Star Schema DDL Model", 
            fontsize=23, fontweight='bold', ha='center', color='#0F172A', fontfamily='sans-serif')
    ax.text(15.0, 16.85, "Physical Relational Contracts, Exact DDL Data Types, Delta Lake Liquid Clustering & Explicit Fact Table Grains", 
            fontsize=13, style='italic', ha='center', color='#475569', fontfamily='sans-serif')

    def draw_physical_table(x, y, w, h, title, items, header_color, bg_color='#FFFFFF', border_color='#CBD5E1', cluster_info="", is_dim=False):
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

        # Cluster banner if present
        line_y = y + h - 1.2
        if cluster_info:
            cb = FancyBboxPatch((x + 0.15, line_y - 0.12), w - 0.3, 0.4, boxstyle="round,pad=0.03,rounding_size=0.08",
                                facecolor='#EFF6FF', edgecolor='#BFDBFE', lw=1.0)
            ax.add_patch(cb)
            ax.text(x + 0.3, line_y + 0.08, f"OPTIMIZATION: {cluster_info}", fontsize=8.0, fontweight='bold', color='#1D4ED8', va='center')
            line_y -= 0.52

        # Items
        for item in items:
            if is_dim:
                # Dimension 3-zone layout: (prefix, col_name, ddl_spec)
                prefix, col_name, ddl_spec = item
                if prefix == "PK":
                    color_p = '#B91C1C'
                    fw = 'bold'
                elif prefix == "FK":
                    color_p = '#1D4ED8'
                    fw = 'bold'
                elif prefix == "UK":
                    color_p = '#B45309'
                    fw = 'bold'
                else:
                    color_p = '#64748B'
                    fw = 'normal'

                ax.text(x + 0.25, line_y, prefix, fontsize=8.2, fontweight=fw, color=color_p, va='center')
                ax.text(x + 1.05, line_y, col_name, fontsize=8.6, fontweight='medium', color='#0F172A', va='center')
                ax.text(x + w - 0.25, line_y, ddl_spec, fontsize=8.0, color='#047857', ha='right', va='center', fontfamily='monospace')
                line_y -= 0.38
            else:
                # Fact 4-zone layout: (prefix, col_name, data_type, note)
                prefix, col_name, data_type, note = item
                if prefix == "PK":
                    color_p = '#B91C1C'
                    fw = 'bold'
                elif prefix == "FK":
                    color_p = '#1D4ED8'
                    fw = 'bold'
                elif prefix == "PK/FK":
                    color_p = '#7C3AED'
                    fw = 'bold'
                elif prefix == "UK":
                    color_p = '#B45309'
                    fw = 'bold'
                elif prefix == "G":
                    # Grain banner inside box
                    gb = FancyBboxPatch((x + 0.15, line_y - 0.15), w - 0.3, 0.45, boxstyle="round,pad=0.03,rounding_size=0.08",
                                        facecolor='#FEF3C7', edgecolor='#FCD34D', lw=1.2)
                    ax.add_patch(gb)
                    ax.text(x + 0.3, line_y + 0.08, f"MANDATORY GRAIN DECLARATION:", fontsize=7.8, fontweight='bold', color='#92400E', va='center')
                    ax.text(x + 0.3, line_y - 0.10, col_name, fontsize=8.2, color='#78350F', va='center', fontweight='medium')
                    line_y -= 0.60
                    continue
                else:
                    color_p = '#64748B'
                    fw = 'normal'

                ax.text(x + 0.25, line_y, prefix, fontsize=8.2, fontweight=fw, color=color_p, va='center')
                ax.text(x + 1.15, line_y, col_name, fontsize=8.6, fontweight='medium', color='#0F172A', va='center')
                ax.text(x + 4.3, line_y, data_type, fontsize=8.2, color='#047857', va='center', fontfamily='monospace')
                ax.text(x + w - 0.25, line_y, note, fontsize=7.8, color='#64748B', ha='right', va='center', style='italic')
                line_y -= 0.38

    # =========================================================================
    # TIER 1: CONFORMED DIMENSIONS (TOP ROW - Y: 10.2 to 15.8)
    # Five distinct horizontal positions, zero text collision, exact DDL spec (1.8 unit gap Plant->Gen)
    # =========================================================================

    # 1. Dim Date
    dim_date_items = [
        ("PK", "date_key", "INT NOT NULL (YYYYMMDD)"),
        ("UK", "calendar_date", "DATE NOT NULL UNIQUE"),
        ("", "calendar_year", "SMALLINT NOT NULL"),
        ("", "calendar_quarter", "SMALLINT NOT NULL (1-4)"),
        ("", "calendar_month", "SMALLINT NOT NULL (1-12)"),
        ("", "month_name", "VARCHAR(20) NOT NULL"),
        ("", "day_of_month", "SMALLINT NOT NULL (1-31)"),
        ("", "day_of_week", "SMALLINT NOT NULL (1-7)"),
        ("", "day_name", "VARCHAR(20) NOT NULL"),
        ("", "is_weekend", "BOOLEAN DEFAULT false")
    ]
    draw_physical_table(0.8, 10.6, 5.2, 5.0, "gold_warehouse.dim_date", dim_date_items, '#334155', is_dim=True)

    # 2. Dim Plant (ends at 6.4 + 5.2 = 11.6)
    dim_plant_items = [
        ("PK", "plant_key", "BIGINT IDENTITY PRIMARY KEY"),
        ("UK", "orispl_code", "INT NOT NULL UNIQUE"),
        ("", "plant_name", "VARCHAR(255) NOT NULL"),
        ("", "utility_id", "INT NULL"),
        ("", "utility_name", "VARCHAR(255) NULL"),
        ("", "latitude", "NUMERIC(9,6) NULL"),
        ("", "longitude", "NUMERIC(9,6) NULL"),
        ("", "state_code", "CHAR(2) NOT NULL"),
        ("", "county_name", "VARCHAR(100) NULL"),
        ("", "ba_code", "VARCHAR(50) NOT NULL"),
        ("", "epa_region", "SMALLINT NULL [1-10]"),
        ("", "is_combined_heat_power", "BOOLEAN DEFAULT false")
    ]
    draw_physical_table(6.4, 10.2, 5.2, 5.4, "gold_warehouse.dim_plant", dim_plant_items, '#0284C7', is_dim=True)

    # 3. Dim Generator (SCD-2) - starts at 13.4 (1.8-unit gap from Plant)
    dim_gen_items = [
        ("PK", "generator_key", "BIGINT IDENTITY PRIMARY KEY"),
        ("FK", "orispl_code", "INT (FK -> dim_plant)"),
        ("UK", "generator_id", "VARCHAR(50) Physical Asset ID"),
        ("", "prime_mover_code", "VARCHAR(20) (ST, GT, CT, CA..)"),
        ("", "primary_energy_source", "VARCHAR(20) (SUB, BIT, NG..)"),
        ("", "nameplate_capacity_mw", "NUMERIC(10,2) >= 0.00 MW"),
        ("", "operating_status", "VARCHAR(20) (OP, SB, RE, OA)"),
        ("", "row_effective_date", "DATE (SCD2 Valid From)"),
        ("", "row_expiration_date", "DATE (SCD2 Valid To / 9999)"),
        ("", "is_current", "BOOLEAN (true = Active)")
    ]
    draw_physical_table(13.4, 10.6, 5.0, 5.0, "gold_warehouse.dim_generator (SCD-2)", dim_gen_items, '#7C3AED', is_dim=True)

    # 4. Dim Weather Station
    dim_ws_items = [
        ("PK", "station_key", "BIGINT IDENTITY PRIMARY KEY"),
        ("UK", "station_id", "VARCHAR(50) USAF-WBAN Key"),
        ("", "station_name", "VARCHAR(255) NOAA Station Title"),
        ("", "state_code", "CHAR(2) State Territory"),
        ("", "latitude", "NUMERIC(9,6) Station Latitude"),
        ("", "longitude", "NUMERIC(9,6) Station Longitude"),
        ("", "elevation_m", "NUMERIC(8,2) Meters ASL")
    ]
    draw_physical_table(18.8, 11.6, 4.8, 4.0, "gold_warehouse.dim_weather_station", dim_ws_items, '#0D9488', is_dim=True)

    # 5. Dim Balancing Authority
    dim_ba_items = [
        ("PK", "ba_key", "BIGINT IDENTITY PRIMARY KEY"),
        ("UK", "ba_code", "VARCHAR(50) NOT NULL UNIQUE"),
        ("", "ba_name", "VARCHAR(255) NOT NULL"),
        ("", "interconnection_region", "VARCHAR(50) (East, West, TX)"),
        ("", "is_active", "BOOLEAN NOT NULL DEFAULT true")
    ]
    draw_physical_table(24.0, 11.9, 5.2, 3.7, "gold_warehouse.dim_ba", dim_ba_items, '#D97706', is_dim=True)

    # =========================================================================
    # TIER 2: PHYSICAL FACT TABLES (BOTTOM ROW - Y: 0.8 to 8.0)
    # Three spacious tables with distinct columns and zero overlap
    # =========================================================================

    # 6. Fact Hourly Emissions & Weather
    fact_emiss_items = [
        ("G", "One row per generating unit per clock hour (Unit-Hour Grain)", "", ""),
        ("PK/FK", "date_key", "INT", "FK -> dim_date"),
        ("PK", "hour_of_day", "SMALLINT", "0 to 23 Clock Hour"),
        ("PK/FK", "plant_key", "BIGINT", "FK -> dim_plant"),
        ("PK", "unit_id", "VARCHAR(50)", "CEMS Boiler / Stack ID"),
        ("FK", "station_key", "BIGINT", "FK -> dim_weather_station"),
        ("", "gross_load_mw", "NUMERIC(12,4)", "Gross Generator Output"),
        ("", "heat_input_mmbtu", "NUMERIC(14,4)", "Thermal Energy Consumed"),
        ("", "so2_mass_lbs", "NUMERIC(14,4)", "Sulfur Dioxide Mass"),
        ("", "nox_mass_lbs", "NUMERIC(14,4)", "Nitrogen Oxides Mass"),
        ("", "co2_mass_tons", "NUMERIC(14,4)", "Carbon Dioxide Short Tons"),
        ("", "ambient_temp_celsius", "NUMERIC(6,2)", "NOAA Surface Air Temp"),
        ("", "wind_speed_mps", "NUMERIC(6,2)", "NOAA Surface Wind Speed"),
        ("", "weather_distance_km", "NUMERIC(6,2)", "Haversine Distance (<=50km)")
    ]
    draw_physical_table(0.8, 0.8, 8.8, 7.2, "gold_warehouse.fact_hourly_emissions_weather", fact_emiss_items, 
                        '#059669', bg_color='#F0FDF4', cluster_info="CLUSTER BY (date_key, plant_key)")

    # 7. Fact Monthly Plant Operations
    fact_monthly_items = [
        ("G", "One row per plant, prime mover, and fuel per month", "", ""),
        ("PK", "snapshot_key", "BIGINT IDENTITY", "PRIMARY KEY [1..N]"),
        ("FK", "month_start_date_key", "INT", "FK -> dim_date"),
        ("FK", "plant_key", "BIGINT", "FK -> dim_plant"),
        ("", "prime_mover_code", "VARCHAR(20)", "Turbine Technology"),
        ("", "energy_source_code", "VARCHAR(20)", "Fuel Consumed"),
        ("", "net_generation_mwh", "NUMERIC(14,4)", "Allows Negative (Station Load)"),
        ("", "fuel_consumed_mmbtu", "NUMERIC(16,4)", "Thermal Fuel Energy"),
        ("", "fuel_consumed_physical", "NUMERIC(16,4)", "Physical Mass / Vol (Tons/Mcf)"),
        ("", "avg_heat_rate_btu_kwh", "NUMERIC(12,2)", "Thermal Efficiency Ratio"),
        ("", "delivered_fuel_cost_per_mmbtu", "NUMERIC(10,4)", "Fuel Delivery Cost ($/MMBtu)"),
        ("", "ending_fuel_stock_physical", "NUMERIC(16,4)", "Monthly Closing Stock")
    ]
    draw_physical_table(10.0, 0.8, 9.0, 6.7, "gold_warehouse.fact_monthly_plant_operations", fact_monthly_items, 
                        '#059669', bg_color='#F0FDF4', cluster_info="CLUSTER BY (month_start_date_key, plant_key)")

    # 8. Fact Regional Grid Demand
    fact_grid_items = [
        ("G", "One row per balancing authority per clock hour", "", ""),
        ("PK/FK", "date_key", "INT", "FK -> dim_date"),
        ("PK", "hour_of_day", "SMALLINT", "0 to 23 Clock Hour"),
        ("PK/FK", "ba_key", "BIGINT", "FK -> dim_ba"),
        ("", "demand_mw", "NUMERIC(14,2)", "Real-Time Consumer Load"),
        ("", "demand_forecast_mw", "NUMERIC(14,2)", "Day-Ahead Grid Forecast"),
        ("", "net_gen_coal_mw", "NUMERIC(14,2)", "Coal Generation Dispatch"),
        ("", "net_gen_gas_mw", "NUMERIC(14,2)", "Natural Gas Dispatch"),
        ("", "net_gen_nuclear_mw", "NUMERIC(14,2)", "Nuclear Baseload Dispatch"),
        ("", "net_gen_hydro_mw", "NUMERIC(14,2)", "Hydroelectric Dispatch"),
        ("", "net_gen_wind_mw", "NUMERIC(14,2)", "Wind Renewable Dispatch"),
        ("", "net_gen_solar_mw", "NUMERIC(14,2)", "Solar Renewable Dispatch"),
        ("", "net_interchange_mw", "NUMERIC(14,2)", "Net Regional Imports/Exports")
    ]
    draw_physical_table(19.4, 0.8, 9.2, 6.7, "gold_warehouse.fact_regional_grid_demand", fact_grid_items, 
                        '#D97706', bg_color='#FFFBEB', cluster_info="CLUSTER BY (date_key, ba_key)")

    # =========================================================================
    # RELATIONSHIP ROUTING (MIDDLE CORRIDOR - Y: 8.0 to 10.2)
    # Clean orthogonal elbow paths with white label halo, zero text collision
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

    # 1. Plant to Generator (Direct horizontal bridge across 1.8-unit gap)
    draw_path([(11.6, 12.8), (13.4, 12.8)], "1 : M (SCD2)", '#7C3AED', label_pos=(12.5, 12.8))

    # 2. Plant to Fact Emissions (Elbow)
    draw_path([(7.5, 10.2), (7.5, 8.8), (5.0, 8.8), (5.0, 8.0)], "1 : M", '#0284C7', label_pos=(6.2, 8.8))

    # 3. Plant to Fact Monthly (Elbow)
    draw_path([(9.4, 10.2), (9.4, 8.3), (13.5, 8.3), (13.5, 7.5)], "1 : M", '#0284C7', label_pos=(11.4, 8.3))

    # 4. Date to Fact Emissions (Direct vertical drop)
    draw_path([(2.8, 10.6), (2.8, 8.0)], "1 : M", '#475569', label_pos=(2.8, 9.3))

    # 5. Date to Fact Monthly (Elbow corridor)
    draw_path([(4.2, 10.6), (4.2, 9.4), (11.5, 9.4), (11.5, 7.5)], "1 : M", '#475569', label_pos=(7.8, 9.4))

    # 6. Date to Fact Grid (High corridor)
    draw_path([(5.0, 10.6), (5.0, 9.8), (21.5, 9.8), (21.5, 7.5)], "1 : M", '#475569', label_pos=(16.5, 9.8))

    # 7. Weather Station to Fact Emissions (Low corridor)
    draw_path([(19.2, 11.6), (19.2, 8.5), (7.0, 8.5), (7.0, 8.0)], "1 : M", '#0D9488', label_pos=(14.2, 8.5))

    # 8. Balancing Authority to Fact Grid (Direct vertical drop)
    draw_path([(25.0, 11.9), (25.0, 7.5)], "1 : M", '#D97706', label_pos=(25.0, 9.6))

    plt.tight_layout()
    output_path = os.path.join(SUBMISSION_DIR, "Physical_Model_Diagram.png")
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Successfully generated clear {output_path}")

if __name__ == "__main__":
    create_physical_model()
