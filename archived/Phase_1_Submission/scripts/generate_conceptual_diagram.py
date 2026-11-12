import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.dirname(SCRIPT_DIR)

def create_conceptual_model():
    # Ultra-wide, high-resolution canvas: 26 x 16 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(26, 16), dpi=300)
    ax.set_xlim(0, 26)
    ax.set_ylim(0, 16)
    ax.axis('off')

    # Premium slate background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Title Banner
    ax.text(13.0, 15.35, "U.S. Bulk Power & Emissions Lakehouse: Conceptual Data Model", 
            fontsize=22, fontweight='bold', ha='center', color='#0F172A', fontfamily='sans-serif')
    ax.text(13.0, 14.90, "High-Level Business Entities, Enterprise Relationships & Multi-Grain Process Cardinalities", 
            fontsize=12.5, style='italic', ha='center', color='#475569', fontfamily='sans-serif')

    def draw_entity(x, y, w, h, title, bullets, color_header, color_body, category=""):
        # Container Box
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                             facecolor=color_body, edgecolor='#CBD5E1', linewidth=1.5)
        ax.add_patch(box)
        # Header banner
        header = FancyBboxPatch((x, y + h - 0.8), w, 0.8, boxstyle="round,pad=0.08,rounding_size=0.15",
                                facecolor=color_header, edgecolor=color_header, linewidth=1.5)
        ax.add_patch(header)
        ax.fill([x, x+w, x+w, x], [y+h-0.8, y+h-0.8, y+h-0.5, y+h-0.5], color=color_header)
        ax.text(x + w/2, y + h - 0.45, title, fontsize=11, fontweight='bold', ha='center', va='center', color='#FFFFFF')

        # Subtitle category if provided
        start_y = y + h - 1.15
        if category:
            ax.text(x + 0.35, start_y, category, fontsize=8.2, fontweight='bold', color=color_header, va='center')
            start_y -= 0.42

        # Bullet points
        for b in bullets:
            ax.text(x + 0.35, start_y, "•", fontsize=9.0, color=color_header, va='center')
            ax.text(x + 0.65, start_y, b, fontsize=8.6, color='#334155', va='center')
            start_y -= 0.38

    # =========================================================================
    # TIER 1: CONFORMED MASTER ENTITIES (TOP ROW - Y: 10.4 to 14.2)
    # Five distinct horizontal blocks with wide separation (1.8 unit gap Plant->Gen)
    # =========================================================================

    # 1. Calendar Date
    date_bullets = [
        "Universal temporal reference frame",
        "Year, Quarter, Month, Day, Hour hierarchies",
        "Standardized US Regional Timezones (EST/CST)",
        "Pre-calculated weekend & holiday flags"
    ]
    draw_entity(0.8, 10.4, 4.4, 3.8, "CALENDAR DATE", date_bullets, '#334155', '#F1F5F9',
                category="CONFORMED MASTER DIMENSION")

    # 2. Power Plant
    plant_bullets = [
        "Physical generating facility master",
        "Universal ORISPL natural business key",
        "Operating utility owner & balancing authority",
        "Geographic county, state & GPS coordinates"
    ]
    draw_entity(5.6, 10.4, 4.8, 3.8, "POWER PLANT", plant_bullets, '#0284C7', '#E0F2FE',
                category="CONFORMED MASTER DIMENSION")

    # 3. Generating Unit (Gap = 1.8 units from Plant)
    gen_bullets = [
        "Individual prime mover turbine / boiler",
        "Nameplate generation capacity (MW)",
        "Combustion fuel technology (Coal, Gas, Nuc)",
        "SCD Type 2 capacity & status lifecycle"
    ]
    draw_entity(12.2, 10.4, 4.5, 3.8, "GENERATING UNIT", gen_bullets, '#7C3AED', '#F5F3FF',
                category="SCD TYPE 2 OUTRIGGER")

    # 4. Weather Station
    ws_bullets = [
        "NOAA Synoptic automated surface station",
        "USAF-WBAN composite natural identifier",
        "Spatial coordinates & ground elevation",
        "Maximum 50 km plant pairing radius"
    ]
    draw_entity(17.1, 10.4, 4.4, 3.8, "WEATHER STATION", ws_bullets, '#0D9488', '#F0FDFA',
                category="CONFORMED MASTER DIMENSION")

    # 5. Balancing Authority
    ba_bullets = [
        "Regional electric reliability coordinator",
        "Grid operator authority (PJM, ERCOT, MISO)",
        "Eastern, Western & Texas Interconnections",
        "EIA-930 hourly telemetry publisher"
    ]
    draw_entity(21.8, 10.4, 3.5, 3.8, "BALANCING AUTHORITY", ba_bullets, '#D97706', '#FFFBEB',
                category="CONFORMED MASTER DIMENSION")

    # =========================================================================
    # TIER 2: CORE BUSINESS PROCESSES (BOTTOM ROW - Y: 0.8 to 7.2)
    # Three spacious business process blocks with zero horizontal collision
    # =========================================================================

    # 6. Hourly Emissions & Weather
    emiss_bullets = [
        "Grain: Clock hour per smokestack generating unit",
        "Continuous Emission Monitoring System (CEMS)",
        "Gross electricity generated (Gross Load MW)",
        "Fuel thermal heat input consumed (MMBtu)",
        "Pollutant masses: SO2 (lbs), NOx (lbs), CO2 (tons)",
        "Surface ambient temperature & wind speed overlay",
        "Spatial linkage within 50 km weather radius"
    ]
    draw_entity(0.8, 0.8, 7.6, 6.4, "HOURLY EMISSIONS & WEATHER", emiss_bullets, '#059669', '#ECFDF5',
                category="BUSINESS PROCESS: Smokestack Telemetry (Tx Fact)")

    # 7. Monthly Facility Operations
    monthly_bullets = [
        "Grain: Plant, prime mover & fuel type per month",
        "EIA-923 monthly generation & fuel accounting",
        "Net electricity delivered to grid (Net MWh)",
        "Negative generation tracked during station outage",
        "Total thermal & physical fuel consumption",
        "Operating heat rate thermal efficiency (Btu/kWh)",
        "Delivered fuel costs ($/MMBtu) & stock balances"
    ]
    draw_entity(8.9, 0.8, 7.8, 6.4, "MONTHLY PLANT OPERATIONS", monthly_bullets, '#059669', '#ECFDF5',
                category="BUSINESS PROCESS: Facility Fuel Accounting (Snapshot)")

    # 8. Regional Grid Dispatch
    grid_bullets = [
        "Grain: Balancing authority per clock hour",
        "EIA-930 hourly grid demand & supply telemetry",
        "Real-time consumer demand load (MW)",
        "Day-ahead forecasted electricity demand",
        "Hourly generation dispatch by 6 fuel categories",
        "(Coal, Natural Gas, Nuclear, Hydro, Wind, Solar)",
        "Net regional import / export interchange flow"
    ]
    draw_entity(17.3, 0.8, 7.9, 6.4, "REGIONAL GRID DISPATCH", grid_bullets, '#D97706', '#FFFBEB',
                category="BUSINESS PROCESS: Regional Grid Balance (Aggregate)")

    # =========================================================================
    # RELATIONSHIP ROUTING (MIDDLE CORRIDOR - Y: 7.2 to 10.4)
    # Orthogonal elbow paths with dedicated Y-tracks, zero line crossings through boxes
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
    draw_path([(10.4, 12.3), (12.2, 12.3)], "Composed Of [1 : M]", '#7C3AED', label_pos=(11.3, 12.3))

    # 2. Plant to Emissions (Clean elbow)
    draw_path([(7.2, 10.4), (7.2, 8.8), (4.5, 8.8), (4.5, 7.2)], "Emits From [1 : M]", '#0284C7', label_pos=(5.8, 8.8))

    # 3. Plant to Monthly (Clean elbow)
    draw_path([(9.0, 10.4), (9.0, 8.2), (12.5, 8.2), (12.5, 7.2)], "Reports Fuel [1 : M]", '#0284C7', label_pos=(10.7, 8.2))

    # 4. Date to Emissions (Direct vertical drop)
    draw_path([(2.5, 10.4), (2.5, 7.2)], "Frames Hourly [1 : M]", '#334155', label_pos=(2.5, 9.3))

    # 5. Date to Monthly (Corridor routing)
    draw_path([(3.8, 10.4), (3.8, 9.6), (10.2, 9.6), (10.2, 7.2)], "Frames Monthly [1 : M]", '#334155', label_pos=(7.0, 9.6))

    # 6. Date to Grid (High corridor routing)
    draw_path([(4.5, 10.4), (4.5, 10.0), (19.5, 10.0), (19.5, 7.2)], "Frames Hourly [1 : M]", '#334155', label_pos=(14.5, 10.0))

    # 7. Weather Station to Emissions (Low corridor routing)
    draw_path([(18.0, 10.4), (18.0, 7.8), (6.0, 7.8), (6.0, 7.2)], "Synoptic Weather (<=50km) [1 : M]", '#0D9488', label_pos=(12.0, 7.8))

    # 8. Balancing Authority to Grid (Direct vertical drop)
    draw_path([(23.0, 10.4), (23.0, 7.2)], "Balances Grid Load [1 : M]", '#D97706', label_pos=(23.0, 9.0))

    # Legend / Taxonomy Banner (Top Left)
    leg = FancyBboxPatch((0.8, 14.55), 7.8, 0.55, boxstyle="round,pad=0.04,rounding_size=0.08",
                         facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1.0)
    ax.add_patch(leg)
    ax.text(1.0, 14.82, "TAXONOMY:", fontsize=8.0, fontweight='bold', color='#1E293B', va='center')
    ax.plot([2.5, 2.9], [14.82, 14.82], color='#0284C7', lw=3.5)
    ax.text(3.05, 14.82, "Conformed Entity", fontsize=8.0, color='#334155', va='center')
    ax.plot([5.3, 5.7], [14.82, 14.82], color='#059669', lw=3.5)
    ax.text(5.85, 14.82, "Business Process", fontsize=8.0, color='#334155', va='center')

    plt.tight_layout()
    output_path = os.path.join(SUBMISSION_DIR, "Conceptual_Model_Diagram.png")
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Successfully generated clear {output_path}")

if __name__ == "__main__":
    create_conceptual_model()
