import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_existing_system_diagram(filepath):
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.5)
    ax.axis('off')
    
    # Background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    
    # Title Banner
    title_box = patches.FancyBboxPatch((0.5, 6.6), 13, 0.7, boxstyle="round,pad=0.1",
                                       fc="#1E293B", ec="#0F172A", lw=1.5)
    ax.add_patch(title_box)
    ax.text(7.0, 6.95, "Existing Operational Meteorological Forecasting Workflow in Karnataka",
            ha='center', va='center', color='white', fontsize=14, fontweight='bold', family='sans-serif')
    
    # 4 Main Stages
    stages = [
        {"x": 0.5, "title": "1. Data Collection", "color": "#E2E8F0", "edge": "#94A3B8", "items": [
            "Regional NWP Models\n(GFS / ECMWF)",
            "Sparse Surface AWS\n(Synoptic Spacing 30-50km)",
            "Broadband Geostationary\nSatellite Radiance",
            "Periodic Manual\nObserver Logs"
        ]},
        {"x": 3.8, "title": "2. Numerical Simulation", "color": "#FEF3C7", "edge": "#F59E0B", "items": [
            "High Execution Latency\n(3 to 6-Hour Refresh Lag)",
            "Coarse Spatial Grid\n(3 km to 12 km Resolution)",
            "Spin-up Latency\n(Misses Rapid Convective Cells)",
            "Absence of Continuous\nThermodynamic Soundings"
        ]},
        {"x": 7.1, "title": "3. Forecasting Logic", "color": "#FEE2E2", "edge": "#EF4444", "items": [
            "Rigid Heuristic Thresholds\n(RH > 80% Binary Triggers)",
            "Nocturnal Inversion Blindspot\n(Mist/Fog Flagged as Storm)",
            "No Multi-Decadal Historical\nClimatological Calibration",
            "Extreme Probability Swings\n(0% or 100% False Alarms)"
        ]},
        {"x": 10.4, "title": "4. Dissemination & Users", "color": "#F1F5F9", "edge": "#64748B", "items": [
            "Coarse District Bulletins\n(Static PDF Tables)",
            "Delayed Public Release\n(2 to 4-Hour Dissemination Lag)",
            "No Localized Micro-Zones\n(e.g., Taluk-Level Guidance)",
            "Vulnerable End Users\n(Farmers, Public Left Unwarned)"
        ]}
    ]
    
    for s in stages:
        # Container Box
        box = patches.FancyBboxPatch((s['x'], 0.8), 3.1, 5.5, boxstyle="round,pad=0.12",
                                     fc=s['color'], ec=s['edge'], lw=1.8)
        ax.add_patch(box)
        # Header Box
        header = patches.FancyBboxPatch((s['x'] + 0.1, 5.7), 2.9, 0.5, boxstyle="round,pad=0.08",
                                        fc=s['edge'], ec=s['edge'], lw=1)
        ax.add_patch(header)
        ax.text(s['x'] + 1.55, 5.95, s['title'], ha='center', va='center',
                color='white', fontsize=11, fontweight='bold', family='sans-serif')
        
        # Sub items
        y_pos = 4.8
        for item in s['items']:
            item_box = patches.FancyBboxPatch((s['x'] + 0.2, y_pos - 0.4), 2.7, 0.85,
                                              boxstyle="round,pad=0.08", fc="white", ec="#CBD5E1", lw=1)
            ax.add_patch(item_box)
            ax.text(s['x'] + 1.55, y_pos + 0.02, item, ha='center', va='center',
                    color='#1E293B', fontsize=8.5, family='sans-serif', multialignment='center')
            y_pos -= 1.15
            
    # Connectors / Arrows
    for arrow_x in [3.65, 6.95, 10.25]:
        ax.annotate("", xy=(arrow_x + 0.15, 3.4), xytext=(arrow_x - 0.05, 3.4),
                    arrowprops=dict(arrowstyle="->", lw=2.5, color="#64748B"))

    # Bottleneck Banner
    bn_box = patches.FancyBboxPatch((0.5, 0.15), 13, 0.55, boxstyle="round,pad=0.08",
                                    fc="#991B1B", ec="#7F1D1D", lw=1.5)
    ax.add_patch(bn_box)
    ax.text(7.0, 0.42, "CRITICAL DEFICIENCIES: High Latency (3-6h) | Nocturnal False Alarms | Coarse Grid (12km) | No Actionable Advisories",
            ha='center', va='center', color='white', fontsize=10, fontweight='bold', family='sans-serif')
            
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Saved existing system diagram:", filepath)


def create_proposed_system_diagram(filepath):
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8.5)
    ax.axis('off')
    
    # Background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    
    # Title Banner
    title_box = patches.FancyBboxPatch((0.5, 7.6), 14, 0.7, boxstyle="round,pad=0.1",
                                       fc="#0F172A", ec="#0284C7", lw=2)
    ax.add_patch(title_box)
    ax.text(7.5, 7.95, "Proposed System Architecture and Data Processing Pipeline (AeroCast AI)",
            ha='center', va='center', color='white', fontsize=14, fontweight='bold', family='sans-serif')
            
    # 3 Architectural Tiers
    # Tier 1: Ingestion
    t1_box = patches.FancyBboxPatch((0.5, 0.5), 4.3, 6.8, boxstyle="round,pad=0.12",
                                    fc="#EFF6FF", ec="#3B82F6", lw=1.8)
    ax.add_patch(t1_box)
    t1_hdr = patches.FancyBboxPatch((0.65, 6.7), 4.0, 0.5, boxstyle="round,pad=0.08",
                                    fc="#1D4ED8", ec="#1D4ED8", lw=1)
    ax.add_patch(t1_hdr)
    ax.text(2.65, 6.95, "TIER 1: Multi-Source Data Ingestion", ha='center', va='center',
            color='white', fontsize=10.5, fontweight='bold', family='sans-serif')
            
    t1_items = [
        ("Live Atmospheric Telemetry", "Open-Meteo High-Res API\nVisual Crossing Fallback Engine\n(T, Td, RH, P, Wind Vectors, Cloud)"),
        ("27-Year Regional Climatology", "Karnataka Historical Records\n9,862 Daily Observations (2000-2027)\nEmpirical Rain & Convective Baseline"),
        ("Geospatial Boundary Validation", "Reverse Geocoding Engine\nStrict Karnataka Polygon Enforcer\nLat: 11.5N-18.6N, Lon: 74.0E-78.6E")
    ]
    y_pos = 5.6
    for title, desc in t1_items:
        ibox = patches.FancyBboxPatch((0.75, y_pos - 0.7), 3.8, 1.4, boxstyle="round,pad=0.08",
                                      fc="white", ec="#93C5FD", lw=1)
        ax.add_patch(ibox)
        ax.text(2.65, y_pos + 0.35, title, ha='center', va='center',
                color='#1E40AF', fontsize=9.5, fontweight='bold', family='sans-serif')
        ax.text(2.65, y_pos - 0.15, desc, ha='center', va='center',
                color='#334155', fontsize=8, family='sans-serif', multialignment='center')
        y_pos -= 1.85
        
    # Tier 2: Analytical & AI Core
    t2_box = patches.FancyBboxPatch((5.35, 0.5), 4.3, 6.8, boxstyle="round,pad=0.12",
                                    fc="#FAF5FF", ec="#9333EA", lw=1.8)
    ax.add_patch(t2_box)
    t2_hdr = patches.FancyBboxPatch((5.5, 6.7), 4.0, 0.5, boxstyle="round,pad=0.08",
                                    fc="#7E22CE", ec="#7E22CE", lw=1)
    ax.add_patch(t2_hdr)
    ax.text(7.5, 6.95, "TIER 2: Physics & Dual AI Engine", ha='center', va='center',
            color='white', fontsize=10.5, fontweight='bold', family='sans-serif')
            
    t2_items = [
        ("62-Feature Physics Pipeline", "Thermodynamic Indices (DPD, VPD)\nEquivalent Potential Temperature (Theta-e)\nDiurnal Solar Weighting (Df Suppression)"),
        ("Soft-Voting GBDT Ensemble", "LightGBM + XGBoost + HistGradient\nTrained Holdout Accuracy: 91.2%\nBaseline Storm Probability Generation"),
        ("Gemini Generative AI Synthesizer", "Automated Chief Meteorologist\nMulti-Modal Synoptic Reasoning\nBayesian Prior & Advisory Authoring")
    ]
    y_pos = 5.6
    for title, desc in t2_items:
        ibox = patches.FancyBboxPatch((5.6, y_pos - 0.7), 3.8, 1.4, boxstyle="round,pad=0.08",
                                      fc="white", ec="#D8B4FE", lw=1)
        ax.add_patch(ibox)
        ax.text(7.5, y_pos + 0.35, title, ha='center', va='center',
                color='#6B21A8', fontsize=9.5, fontweight='bold', family='sans-serif')
        ax.text(7.5, y_pos - 0.15, desc, ha='center', va='center',
                color='#334155', fontsize=8, family='sans-serif', multialignment='center')
        y_pos -= 1.85
        
    # Tier 3: Presentation & Decision Support
    t3_box = patches.FancyBboxPatch((10.2, 0.5), 4.3, 6.8, boxstyle="round,pad=0.12",
                                    fc="#F0FDF4", ec="#16A34A", lw=1.8)
    ax.add_patch(t3_box)
    t3_hdr = patches.FancyBboxPatch((10.35, 6.7), 4.0, 0.5, boxstyle="round,pad=0.08",
                                    fc="#15803D", ec="#15803D", lw=1)
    ax.add_patch(t3_hdr)
    ax.text(12.35, 6.95, "TIER 3: Decision Support & Interface", ha='center', va='center',
            color='white', fontsize=10.5, fontweight='bold', family='sans-serif')
            
    t3_items = [
        ("Interactive Doppler Radar Map", "Leaflet.js Geospatial Canvas\n25km, 50km, 100km Concentric Rings\nLive Station Blip & Taluk Micro-Zones"),
        ("Dynamic Alert & 3-Step Timeline", "+30m, +60m, +90m Hazard Progression\nColor-Coded Badges (Green/Yellow/Red)\nContinuous 0-100% Calibrated Metric"),
        ("Multi-Sector Plain Advisories", "Agricultural Harvest Guidance\nTransit & Highway Flood Warnings\nOutdoor Safety & Power Utility Alerts")
    ]
    y_pos = 5.6
    for title, desc in t3_items:
        ibox = patches.FancyBboxPatch((10.45, y_pos - 0.7), 3.8, 1.4, boxstyle="round,pad=0.08",
                                      fc="white", ec="#86EFAC", lw=1)
        ax.add_patch(ibox)
        ax.text(12.35, y_pos + 0.35, title, ha='center', va='center',
                color='#166534', fontsize=9.5, fontweight='bold', family='sans-serif')
        ax.text(12.35, y_pos - 0.15, desc, ha='center', va='center',
                color='#334155', fontsize=8, family='sans-serif', multialignment='center')
        y_pos -= 1.85

    # Connectors between tiers
    ax.annotate("", xy=(5.3, 3.9), xytext=(4.85, 3.9),
                arrowprops=dict(arrowstyle="->", lw=3, color="#2563EB"))
    ax.annotate("", xy=(10.15, 3.9), xytext=(9.7, 3.9),
                arrowprops=dict(arrowstyle="->", lw=3, color="#9333EA"))
                
    # Footer Highlights
    f_box = patches.FancyBboxPatch((0.5, 0.05), 14, 0.38, boxstyle="round,pad=0.05",
                                   fc="#047857", ec="#065F46", lw=1)
    ax.add_patch(f_box)
    ax.text(7.5, 0.24, "KEY ADVANTAGES: 0-90m Lead Time | Boundary-Layer Physics (DPD/VPD) | Zero Nocturnal False Alarms | Generative AI Bulletins",
            ha='center', va='center', color='white', fontsize=9.5, fontweight='bold', family='sans-serif')

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Saved proposed system diagram:", filepath)

create_existing_system_diagram("report/existing_system_workflow.png")
create_proposed_system_diagram("report/proposed_system_architecture.png")
