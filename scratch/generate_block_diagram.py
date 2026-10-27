import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_block_diagram(filepath):
    fig, ax = plt.subplots(figsize=(14, 6.5), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6.5)
    ax.axis('off')
    
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    
    # Title
    t_box = patches.FancyBboxPatch((0.5, 5.7), 13, 0.65, boxstyle="round,pad=0.08",
                                   fc="#0F172A", ec="#0284C7", lw=1.5)
    ax.add_patch(t_box)
    ax.text(7.0, 6.02, "High-Level Conceptual Block Diagram of Proposed Convective Nowcasting System",
            ha='center', va='center', color='white', fontsize=12.5, fontweight='bold', family='sans-serif')
            
    # 5 Horizontal Blocks
    blocks = [
        {"x": 0.5, "title": "User Request &\nGeospatial Filter", "desc": "Karnataka Boundary Check\nReverse Geocoding\nStation Identification", "color": "#EFF6FF", "border": "#3B82F6", "hdr": "#1D4ED8"},
        {"x": 3.15, "title": "Telemetry &\nClimatology Data", "desc": "Live Open-Meteo AWS\nVisual Crossing Backup\n27-Yr Climatology Prior", "color": "#F0FDF4", "border": "#22C55E", "hdr": "#15803D"},
        {"x": 5.8, "title": "Thermodynamics &\nFeature Pipeline", "desc": "62 Physics Indicators\nDPD & VPD Computation\nDiurnal Solar Weighting", "color": "#FEF3C7", "border": "#EAB308", "hdr": "#B45309"},
        {"x": 8.45, "title": "Dual AI Engine &\nEnsemble Core", "desc": "GBDT Soft-Voting (91.2%)\nLightGBM + XGBoost\nGemini Meteorologist LLM", "color": "#FAF5FF", "border": "#A855F7", "hdr": "#7E22CE"},
        {"x": 11.1, "title": "Decision Support\n& Visualization", "desc": "Leaflet Radar Canvas\nDynamic 3-Step Timeline\nSector Advisories", "color": "#FFF1F2", "border": "#F43F5E", "hdr": "#BE123C"}
    ]
    
    for b in blocks:
        box = patches.FancyBboxPatch((b['x'], 1.2), 2.4, 4.0, boxstyle="round,pad=0.1",
                                     fc=b['color'], ec=b['border'], lw=1.6)
        ax.add_patch(box)
        
        hdr = patches.FancyBboxPatch((b['x'] + 0.1, 4.3), 2.2, 0.75, boxstyle="round,pad=0.06",
                                     fc=b['hdr'], ec=b['hdr'], lw=1)
        ax.add_patch(hdr)
        ax.text(b['x'] + 1.2, 4.68, b['title'], ha='center', va='center',
                color='white', fontsize=9.5, fontweight='bold', family='sans-serif', multialignment='center')
                
        d_box = patches.FancyBboxPatch((b['x'] + 0.15, 1.5), 2.1, 2.5, boxstyle="round,pad=0.06",
                                       fc="white", ec="#CBD5E1", lw=1)
        ax.add_patch(d_box)
        ax.text(b['x'] + 1.2, 2.75, b['desc'], ha='center', va='center',
                color='#334155', fontsize=8.5, family='sans-serif', multialignment='center', linespacing=1.6)

    # Arrows between blocks
    for arr_x in [2.95, 5.6, 8.25, 10.9]:
        ax.annotate("", xy=(arr_x + 0.15, 3.2), xytext=(arr_x - 0.05, 3.2),
                    arrowprops=dict(arrowstyle="->", lw=2.5, color="#475569"))
                    
    # Bottom Summary
    sum_box = patches.FancyBboxPatch((0.5, 0.3), 13, 0.55, boxstyle="round,pad=0.06",
                                     fc="#1E293B", ec="#0F172A", lw=1)
    ax.add_patch(sum_box)
    ax.text(7.0, 0.57, "End-to-End Operational Pipeline: Low-Latency Telemetry --> Physics Transformation --> Calibrated Ensemble & LLM --> Interactive Radar Decision Support",
            ha='center', va='center', color='white', fontsize=8.5, fontweight='bold', family='sans-serif')
            
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Saved proposed system block diagram:", filepath)

create_block_diagram("report/proposed_system_block_diagram.png")
