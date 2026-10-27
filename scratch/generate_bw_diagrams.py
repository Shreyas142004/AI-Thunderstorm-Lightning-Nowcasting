# pyrefly: ignore[missing-import]
import matplotlib
matplotlib.use('Agg')
# pyrefly: ignore[missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore[missing-import]
import matplotlib.patches as patches
# pyrefly: ignore[missing-import]
import numpy as np

# -------------------------------------------------------------
# ICON DRAWING PRIMITIVES (Black & White / Grayscale)
# -------------------------------------------------------------
def draw_monitor(ax, cx, cy, w=0.54, h=0.38):
    """Draws a clean monitor icon."""
    ax.add_patch(patches.FancyBboxPatch((cx - w/2, cy - h/2 + 0.05), w, h,
                                       boxstyle='round,pad=0.02', fc='white', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Rectangle((cx - w/2 + 0.04, cy - h/2 + 0.09), w - 0.08, h - 0.08,
                                   fc='#F3F4F6', ec='black', lw=0.8, zorder=7))
    ax.plot([cx, cx], [cy - h/2 + 0.05, cy - h/2 - 0.05], color='black', lw=1.4, zorder=6)
    ax.plot([cx - 0.16, cx + 0.16], [cy - h/2 - 0.05, cy - h/2 - 0.05], color='black', lw=1.4, zorder=6)

def draw_smartphone(ax, cx, cy, w=0.30, h=0.50):
    """Draws a clean smartphone icon."""
    ax.add_patch(patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                       boxstyle='round,pad=0.02', fc='white', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Rectangle((cx - w/2 + 0.035, cy - h/2 + 0.07), w - 0.07, h - 0.14,
                                   fc='#F3F4F6', ec='black', lw=0.8, zorder=7))
    ax.plot([cx - 0.05, cx + 0.05], [cy + h/2 - 0.04, cy + h/2 - 0.04], color='black', lw=1.0, zorder=7)
    ax.plot(cx, cy - h/2 + 0.035, 'o', color='black', markersize=2.2, zorder=7)

def draw_radar(ax, cx, cy, r=0.22):
    """Draws a clean radar dish / scope icon."""
    ax.add_patch(patches.Circle((cx, cy), r, fc='#F9FAFB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Circle((cx, cy), r * 0.65, fc='none', ec='black', lw=0.8, ls='--', zorder=7))
    ax.add_patch(patches.Circle((cx, cy), r * 0.32, fc='none', ec='black', lw=0.8, zorder=7))
    ax.plot([cx - r, cx + r], [cy, cy], color='black', lw=0.8, zorder=7)
    ax.plot([cx, cx], [cy - r, cy + r], color='black', lw=0.8, zorder=7)
    ax.plot([cx, cx + r*0.7], [cy, cy + r*0.7], color='black', lw=1.5, zorder=8)

def draw_server(ax, cx, cy, w=0.52, h=0.38):
    """Draws a clean 3-tier server rack icon."""
    for dy in [0.11, 0.0, -0.11]:
        ax.add_patch(patches.FancyBboxPatch((cx - w/2, cy + dy - 0.045), w, 0.09,
                                           boxstyle='round,pad=0.015', fc='white', ec='black', lw=1.0, zorder=6))
        ax.plot([cx - w/2 + 0.08, cx + w/2 - 0.16], [cy + dy, cy + dy], color='#4B5563', lw=1.0, zorder=7)
        ax.plot([cx + w/2 - 0.09, cx + w/2 - 0.05], [cy + dy, cy + dy], 'o', color='black', markersize=2.0, zorder=7)

def draw_shield(ax, cx, cy, w=0.38, h=0.44):
    """Draws a clean security shield icon."""
    pts = np.array([
        [cx - w/2, cy + h/2],
        [cx + w/2, cy + h/2],
        [cx + w/2, cy - h/6],
        [cx, cy - h/2],
        [cx - w/2, cy - h/6]
    ])
    ax.add_patch(patches.Polygon(pts, closed=True, fc='#F3F4F6', ec='black', lw=1.2, zorder=6))
    ax.plot([cx - 0.08, cx - 0.02, cx + 0.09], [cy, cy - 0.07, cy + 0.08], color='black', lw=1.8, zorder=7)

def draw_gear(ax, cx, cy, r=0.22):
    """Draws a mechanical gear icon."""
    ax.add_patch(patches.Circle((cx, cy), r, fc='#E5E7EB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Circle((cx, cy), r * 0.42, fc='white', ec='black', lw=1.0, zorder=7))
    for deg in range(0, 360, 45):
        rad = np.radians(deg)
        x1, y1 = cx + (r - 0.02) * np.cos(rad), cy + (r - 0.02) * np.sin(rad)
        x2, y2 = cx + (r + 0.07) * np.cos(rad), cy + (r + 0.07) * np.sin(rad)
        ax.plot([x1, x2], [y1, y2], color='black', lw=2.4, zorder=6)

def draw_brain(ax, cx, cy, s=0.22):
    """Draws a clean neural/decision tree icon."""
    ax.plot(cx, cy + s*0.7, 'o', color='black', markersize=4.5, zorder=7)
    ax.plot(cx - s*0.65, cy - s*0.5, 'o', color='black', markersize=3.8, zorder=7)
    ax.plot(cx + s*0.65, cy - s*0.5, 'o', color='black', markersize=3.8, zorder=7)
    ax.plot(cx - s*0.25, cy - s*0.5, 'o', color='black', markersize=3.2, zorder=7)
    ax.plot(cx + s*0.25, cy - s*0.5, 'o', color='black', markersize=3.2, zorder=7)
    ax.plot([cx, cx - s*0.65], [cy + s*0.7, cy - s*0.5], color='black', lw=1.2, zorder=6)
    ax.plot([cx, cx + s*0.65], [cy + s*0.7, cy - s*0.5], color='black', lw=1.2, zorder=6)
    ax.plot([cx, cx - s*0.25], [cy + s*0.7, cy - s*0.5], color='black', lw=1.0, zorder=6)
    ax.plot([cx, cx + s*0.25], [cy + s*0.7, cy - s*0.5], color='black', lw=1.0, zorder=6)

def draw_sparkle(ax, cx, cy, s=0.26):
    """Draws a clean 4-point generative AI sparkle icon."""
    pts = np.array([
        [cx, cy + s],
        [cx + s*0.22, cy + s*0.22],
        [cx + s, cy],
        [cx + s*0.22, cy - s*0.22],
        [cx, cy - s],
        [cx - s*0.22, cy - s*0.22],
        [cx - s, cy],
        [cx - s*0.22, cy + s*0.22]
    ])
    ax.add_patch(patches.Polygon(pts, closed=True, fc='#F3F4F6', ec='black', lw=1.2, zorder=6))
    pts2 = np.array([
        [cx + s*0.65, cy + s*0.8],
        [cx + s*0.73, cy + s*0.65],
        [cx + s*0.88, cy + s*0.8],
        [cx + s*0.73, cy + s*0.95]
    ])
    ax.add_patch(patches.Polygon(pts2, closed=True, fc='black', ec='black', lw=0.8, zorder=7))

def draw_database(ax, cx, cy, w=0.54, h=0.50):
    """Draws a clean database cylinder icon."""
    ax.add_patch(patches.Rectangle((cx - w/2, cy - h/2 + 0.08), w, h - 0.16,
                                   fc='#F9FAFB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Ellipse((cx, cy + h/2 - 0.08), w, 0.16,
                                 fc='white', ec='black', lw=1.2, zorder=7))
    ax.add_patch(patches.Arc((cx, cy), w, 0.15, theta1=180, theta2=360,
                             color='black', lw=1.0, zorder=7))
    ax.add_patch(patches.Arc((cx, cy - h/2 + 0.08), w, 0.16, theta1=180, theta2=360,
                             color='black', lw=1.2, zorder=7))


# -------------------------------------------------------------
# 1. PROPOSED SYSTEM ARCHITECTURE (Exact Layout as Sample Image)
# -------------------------------------------------------------
def create_proposed_architecture_bw(filepath):
    fig, ax = plt.subplots(figsize=(15.5, 8.5), dpi=300)
    ax.set_xlim(0, 15.5)
    ax.set_ylim(0, 8.5)
    ax.axis('off')
    
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # ---------------- 1. PRESENTATION LAYER ----------------
    ax.add_patch(patches.FancyBboxPatch((0.5, 0.6), 3.1, 7.3, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(0.75, 7.55, "1. Presentation Layer", fontsize=11.5, fontweight='bold', family='sans-serif')
    
    # Inner boxes
    pres_boxes = [
        {"y": 5.5, "title": "AeroCast Web Portal", "sub": "(React.js / HTML5 + CSS)", "icon": "monitor"},
        {"y": 3.5, "title": "Observer Mobile App", "sub": "(Flutter / PWA Client)", "icon": "mobile"},
        {"y": 1.5, "title": "Interactive Doppler Radar", "sub": "(Leaflet.js Geospatial Engine)", "icon": "radar"}
    ]
    for b in pres_boxes:
        bx = patches.FancyBboxPatch((0.7, b['y']), 2.7, 1.5, boxstyle='round,pad=0.08',
                                    fc='white', ec='black', lw=1.2, zorder=2)
        ax.add_patch(bx)
        if b['icon'] == 'monitor':
            draw_monitor(ax, 2.05, b['y'] + 1.05)
        elif b['icon'] == 'mobile':
            draw_smartphone(ax, 2.05, b['y'] + 1.05)
        elif b['icon'] == 'radar':
            draw_radar(ax, 2.05, b['y'] + 1.05)
            
        ax.text(2.05, b['y'] + 0.48, b['title'], ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
        ax.text(2.05, b['y'] + 0.22, b['sub'], ha='center', va='center',
                fontsize=8, color='#374151', family='sans-serif', zorder=5)
                
    # ---------------- 2. GATEWAY & SECURITY ----------------
    ax.add_patch(patches.FancyBboxPatch((4.3, 1.6), 2.7, 6.3, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(4.55, 7.55, "2. Gateway & Security", fontsize=11.5, fontweight='bold', family='sans-serif')
    
    # Sub-box 1: FastAPI / Flask REST Gateway
    ax.add_patch(patches.FancyBboxPatch((4.5, 5.0), 2.3, 1.95, boxstyle='round,pad=0.08',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_server(ax, 5.65, 6.38)
    ax.text(5.65, 5.75, "Flask REST Gateway", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(5.65, 5.40, "(Routing, Telemetry Fetch\n& JSON Serialization)", ha='center', va='center',
            fontsize=7.5, color='#374151', family='sans-serif', zorder=5)
            
    # Sub-box 2: Karnataka Boundary Lock & Validator
    ax.add_patch(patches.FancyBboxPatch((4.5, 2.1), 2.3, 1.95, boxstyle='round,pad=0.08',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_shield(ax, 5.65, 3.48)
    ax.text(5.65, 2.85, "Karnataka Boundary Lock", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(5.65, 2.50, "(Strict Polygon Validator:\n11.5°N–18.6°N, 74.0°E–78.6°E)", ha='center', va='center',
            fontsize=7.5, color='#374151', family='sans-serif', zorder=5)
            
    # Vertical bidirectional arrow between Gateway and Validator
    ax.annotate("", xy=(5.65, 4.95), xytext=(5.65, 4.08),
                arrowprops=dict(arrowstyle="<->", lw=1.3, color='black'))
    ax.text(5.65, 4.52, "Verify", ha='center', va='center', fontsize=8, color='black', fontweight='bold',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'))

    # ---------------- 3. CORE SERVICES & AI ENGINE ----------------
    ax.add_patch(patches.FancyBboxPatch((7.8, 3.4), 7.2, 4.5, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(8.05, 7.55, "3. Core Services & AI Engine", fontsize=11.5, fontweight='bold', family='sans-serif')
    
    # Component 1: Atmospheric Physics Engine (Highlighted in light gray)
    ax.add_patch(patches.FancyBboxPatch((8.0, 3.8), 2.05, 3.25, boxstyle='round,pad=0.08',
                                       fc='#E5E7EB', ec='black', lw=1.3, zorder=2))
    draw_gear(ax, 9.02, 6.28)
    ax.text(9.02, 5.45, "Atmospheric\nPhysics Engine", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(9.02, 4.55, "(62 Feature Pipeline:\nDPD, VPD, θe,\nDiurnal Df Factor)", ha='center', va='center',
            fontsize=7.5, color='#1F2937', family='sans-serif', zorder=5)
            
    # Arrow from Physics to GBDT Ensemble
    ax.annotate("", xy=(10.45, 5.35), xytext=(10.08, 5.35),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=12))
    ax.text(10.26, 5.65, "Pass\nEligible", ha='center', va='center', fontsize=7, color='black',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))
    
    # Component 2: Soft-Voting GBDT Ensemble
    ax.add_patch(patches.FancyBboxPatch((10.48, 3.8), 2.05, 3.25, boxstyle='round,pad=0.08',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_brain(ax, 11.5, 6.28)
    ax.text(11.5, 5.45, "Soft-Voting\nGBDT Ensemble", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.5, 4.55, "(LightGBM, XGBoost,\nHistGradientBoosting:\n91.2% Accuracy)", ha='center', va='center',
            fontsize=7.5, color='#374151', family='sans-serif', zorder=5)

    # Arrow from GBDT to Gemini
    ax.annotate("", xy=(12.93, 5.35), xytext=(12.56, 5.35),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=12))
    ax.text(12.74, 5.65, "Skill\nGaps", ha='center', va='center', fontsize=7, color='black',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))

    # Component 3: Chief Meteorologist AI
    ax.add_patch(patches.FancyBboxPatch((12.96, 3.8), 1.85, 3.25, boxstyle='round,pad=0.08',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_sparkle(ax, 13.88, 6.28)
    ax.text(13.88, 5.45, "Chief Meteorologist\nAI Engine", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(13.88, 4.55, "(Google Gemini API:\nSynoptic Bulletins\n& Sector Advisories)", ha='center', va='center',
            fontsize=7.5, color='#374151', family='sans-serif', zorder=5)

    # ---------------- 4. STORAGE LAYER ----------------
    ax.add_patch(patches.FancyBboxPatch((7.8, 0.6), 7.2, 2.5, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(8.05, 2.78, "4. Storage Layer", fontsize=11.5, fontweight='bold', family='sans-serif')
    
    # Sub-box 1: PostgreSQL Database (aligned under Card 2 GBDT)
    ax.add_patch(patches.FancyBboxPatch((10.3, 0.78), 2.4, 1.7, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 11.5, 1.95)
    ax.text(11.5, 1.38, "PostgreSQL Database", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.5, 1.05, "(27-Yr Climatology Prior,\nRules, Probabilities, Scores)", ha='center', va='center',
            fontsize=7.0, color='#374151', family='sans-serif', zorder=5)

    # Sub-box 2: Supabase Storage (aligned under Card 3 Gemini)
    ax.add_patch(patches.FancyBboxPatch((12.8, 0.78), 2.05, 1.7, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 13.82, 1.95)
    ax.text(13.82, 1.38, "Supabase Storage", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(13.82, 1.05, "(Model Binaries, Radar\nTiles & Advisory Cache)", ha='center', va='center',
            fontsize=7.0, color='#374151', family='sans-serif', zorder=5)

    # ---------------- INTERCONNECTING ARROWS & LABELS ----------------
    # Presentation to Gateway (HTTPS) - entering Gateway left edge (x=4.3)
    # Card 1 (y=6.25)
    ax.plot([3.4, 3.85, 3.85, 4.28], [6.25, 6.25, 6.25, 6.25], color='black', lw=1.2)
    ax.annotate("", xy=(4.28, 6.25), xytext=(4.2, 6.25),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(3.85, 6.4, "HTTPS", fontsize=7.0, color='black', fontweight='bold', ha='center', family='sans-serif')
    
    # Card 2 (y=4.25)
    ax.plot([3.4, 3.85, 3.85, 4.28], [4.25, 4.25, 5.85, 5.85], color='black', lw=1.2)
    ax.annotate("", xy=(4.28, 5.85), xytext=(4.2, 5.85),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(3.6, 4.4, "HTTPS", fontsize=7.0, color='black', fontweight='bold', ha='center', family='sans-serif')
    
    # Card 3 (y=2.25)
    ax.plot([3.4, 3.85, 3.85, 4.28], [2.25, 2.25, 5.45, 5.45], color='black', lw=1.2)
    ax.annotate("", xy=(4.28, 5.45), xytext=(4.2, 5.45),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(3.6, 2.4, "HTTPS", fontsize=7.0, color='black', fontweight='bold', ha='center', family='sans-serif')

    # Gateway to Core Services (Validate Rules)
    ax.annotate("", xy=(7.98, 5.95), xytext=(6.82, 5.95),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=12))
    ax.text(7.4, 6.25, "Validates\nRules", fontsize=7.5, color='black', fontweight='bold', ha='center',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'))

    # Security / Gateway down to Storage Layer (Upload Docs)
    ax.plot([5.65, 5.65, 10.28], [2.08, 1.45, 1.45], color='black', lw=1.2)
    ax.annotate("", xy=(10.28, 1.45), xytext=(10.18, 1.45),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(7.4, 1.62, "Upload Docs", fontsize=7.5, color='black', fontweight='bold', ha='center',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'))

    # From GBDT down to PostgreSQL (Save Scores) - vertical straight arrow
    ax.annotate("", xy=(11.5, 2.5), xytext=(11.5, 3.78),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(11.55, 3.15, "Save Scores", fontsize=7.5, color='black', ha='left', va='center',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))

    # From Gemini down to Supabase Storage (Save Prep) - vertical straight arrow
    ax.annotate("", xy=(13.82, 2.5), xytext=(13.82, 3.78),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(13.87, 3.15, "Save Prep", fontsize=7.5, color='black', ha='left', va='center',
            family='sans-serif', bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor='white', edgecolor='none')
    plt.close()
    print("Saved proposed system architecture (B&W):", filepath)


# -------------------------------------------------------------
# 2. EXISTING SYSTEM WORKFLOW (Clean B&W / Grayscale Flowchart)
# -------------------------------------------------------------
def create_existing_workflow_bw(filepath):
    fig, ax = plt.subplots(figsize=(15.5, 7.5), dpi=300)
    ax.set_xlim(0, 15.5)
    ax.set_ylim(0, 7.5)
    ax.axis('off')
    
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    stages = [
        {"x": 0.5, "title": "1. Data Collection", "items": [
            "Regional NWP Models\n(GFS / ECMWF Global Runs)",
            "Sparse Surface AWS\n(Coarse Spacing: 30–50 km)",
            "Broadband Geostationary\nSatellite Cloud Telemetry",
            "Periodic Manual\nStation Observer Logs"
        ]},
        {"x": 4.3, "title": "2. Numerical Simulation", "items": [
            "High Execution Latency\n(3 to 6-Hour Update Lag)",
            "Coarse Spatial Grid\n(3 km to 12 km Resolution)",
            "Model Spin-Up Blindspot\n(Misses 30–60m Convection)",
            "Absence of Real-Time\nThermodynamic Soundings"
        ]},
        {"x": 8.1, "title": "3. Forecasting Logic", "items": [
            "Rigid Heuristic Rules\n(Fixed RH > 80% Trigger)",
            "Nocturnal Inversion Blindspot\n(Valley Mist Flagged as Storm)",
            "No Multi-Decadal Historical\nClimatological Calibration",
            "Extreme Probability Swings\n(0% or 100% Volatile Jumps)"
        ]},
        {"x": 11.9, "title": "4. Dissemination & Users", "items": [
            "Coarse District Bulletins\n(Static Tabular PDF Reports)",
            "Delayed Public Release\n(2 to 4-Hour Dissemination Lag)",
            "No Localized Micro-Zones\n(e.g., Taluk-Level Guidance)",
            "Vulnerable Rural Sectors\n(Farmers Left Unprepared)"
        ]}
    ]
    
    for s in stages:
        # Outer container
        box = patches.FancyBboxPatch((s['x'], 0.95), 3.1, 6.2, boxstyle="round,pad=0.08",
                                     fc='white', ec='black', lw=1.5)
        ax.add_patch(box)
        
        # Header banner (light gray fill)
        hdr = patches.FancyBboxPatch((s['x'] + 0.1, 6.5), 2.9, 0.5, boxstyle="round,pad=0.05",
                                     fc='#E5E7EB', ec='black', lw=1.1)
        ax.add_patch(hdr)
        ax.text(s['x'] + 1.55, 6.75, s['title'], ha='center', va='center',
                color='black', fontsize=10.5, fontweight='bold', family='sans-serif')
        
        # Items
        y_pos = 5.65
        for item in s['items']:
            ibox = patches.FancyBboxPatch((s['x'] + 0.16, y_pos - 0.45), 2.78, 0.92,
                                          boxstyle="round,pad=0.06", fc='white', ec='black', lw=0.9)
            ax.add_patch(ibox)
            ax.text(s['x'] + 1.55, y_pos, item, ha='center', va='center',
                    color='black', fontsize=8, family='sans-serif', multialignment='center')
            y_pos -= 1.22

    # Connecting arrows between stages with ample clear gaps
    stage_arrows = [
        {"x1": 3.62, "x2": 4.28, "label": "Batch Sync\n(3-6h Lag)"},
        {"x1": 7.42, "x2": 8.08, "label": "Raw Grids\n(12 km)"},
        {"x1": 11.22, "x2": 11.88, "label": "Static PDF\nBulletins"}
    ]
    for sa in stage_arrows:
        ax.annotate("", xy=(sa['x2'], 4.0), xytext=(sa['x1'], 4.0),
                    arrowprops=dict(arrowstyle="-|>", lw=1.6, color='black', mutation_scale=13))
        ax.text((sa['x1'] + sa['x2'])/2, 4.35, sa['label'], ha='center', va='center',
                fontsize=7.2, color='black', fontweight='bold', family='sans-serif', multialignment='center',
                bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'))

    # Critical Deficiencies Banner at bottom
    bn_box = patches.FancyBboxPatch((0.5, 0.2), 14.5, 0.55, boxstyle="round,pad=0.06",
                                    fc='#F3F4F6', ec='black', lw=1.3)
    ax.add_patch(bn_box)
    ax.text(7.75, 0.47, "CRITICAL DEFICIENCIES: High Update Latency (3–6h)  |  Nocturnal False Alarms (Mist Mistaken for Storms)  |  Coarse 12 km Grid  |  No Plain-Language Advisories",
            ha='center', va='center', color='black', fontsize=8.2, fontweight='bold', family='sans-serif')

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor='white', edgecolor='none')
    plt.close()
    print("Saved existing system workflow (B&W):", filepath)


# -------------------------------------------------------------
# 3. PROPOSED SYSTEM BLOCK DIAGRAM (Clean B&W / Grayscale Pipeline)
# -------------------------------------------------------------
def create_proposed_block_diagram_bw(filepath):
    fig, ax = plt.subplots(figsize=(16.0, 7.2), dpi=300)
    ax.set_xlim(0, 16.0)
    ax.set_ylim(0, 7.2)
    ax.axis('off')
    
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    blocks = [
        {"x": 0.5, "w": 2.4, "title": "1. User Query &\nGeospatial Filter",
         "sub": "Reverse Geocoding\nStation Coordinate Check\nStrict Karnataka Boundary\n(11.5°N–18.6°N, 74.0°E–78.6°E)",
         "icon": "shield", "highlight": False},
        {"x": 3.6, "w": 2.4, "title": "2. Telemetry Ingestion\n& Observation Cache",
         "sub": "Live Open-Meteo REST API\nVisual Crossing Fallback\nSurface Observations (T, Td)\nRelative Humidity, Wind, P",
         "icon": "server", "highlight": False},
        {"x": 6.7, "w": 2.4, "title": "3. Atmospheric Physics\nFeature Pipeline",
         "sub": "62 Engineered Variables\nDew Point Depression (DPD)\nVapor Pressure Deficit (VPD)\nDiurnal Insolation Factor (Df)",
         "icon": "gear", "highlight": True},
        {"x": 9.8, "w": 2.4, "title": "4. Dual AI & Bayesian\nClimatology Engine",
         "sub": "Soft-Voting GBDT (91.2%)\nLightGBM + XGBoost Ensemble\n27-Yr Climatology Prior DB\nGemini Meteorologist LLM",
         "icon": "sparkle", "highlight": False},
        {"x": 12.9, "w": 2.4, "title": "5. Decision Support &\nInteractive Display",
         "sub": "S-Band Doppler Radar Canvas\nDynamic 3-Step Timeline Cards\nTaluk Micro-Zones Panel\nAgriculture & Transit Advisories",
         "icon": "radar", "highlight": False}
    ]
    
    for b in blocks:
        # Outer container box
        fc_color = '#F3F4F6' if b['highlight'] else 'white'
        box = patches.FancyBboxPatch((b['x'], 0.95), b['w'], 5.8, boxstyle="round,pad=0.08",
                                     fc=fc_color, ec='black', lw=1.4)
        ax.add_patch(box)
        
        # Header box
        hdr_fc = '#E5E7EB' if b['highlight'] else '#F9FAFB'
        hdr = patches.FancyBboxPatch((b['x'] + 0.08, 5.85), b['w'] - 0.16, 0.82, boxstyle="round,pad=0.05",
                                     fc=hdr_fc, ec='black', lw=1.0)
        ax.add_patch(hdr)
        ax.text(b['x'] + b['w']/2, 6.26, b['title'], ha='center', va='center',
                color='black', fontsize=9, fontweight='bold', family='sans-serif', multialignment='center')
        
        # Icon
        ic_cx = b['x'] + b['w']/2
        if b['icon'] == 'shield':
            draw_shield(ax, ic_cx, 5.15)
        elif b['icon'] == 'server':
            draw_server(ax, ic_cx, 5.15)
        elif b['icon'] == 'gear':
            draw_gear(ax, ic_cx, 5.15)
        elif b['icon'] == 'sparkle':
            draw_sparkle(ax, ic_cx, 5.15)
        elif b['icon'] == 'radar':
            draw_radar(ax, ic_cx, 5.15)
            
        # Description box
        d_box = patches.FancyBboxPatch((b['x'] + 0.1, 1.15), b['w'] - 0.2, 3.35, boxstyle="round,pad=0.05",
                                       fc='white', ec='black', lw=0.9)
        ax.add_patch(d_box)
        ax.text(ic_cx, 2.82, b['sub'], ha='center', va='center',
                color='black', fontsize=7.8, family='sans-serif', multialignment='center', linespacing=1.6)

    # Connecting arrows between blocks with 0.7 gap
    gaps = [
        {"x1": 2.92, "x2": 3.58, "label": "Coordinates"},
        {"x1": 6.02, "x2": 6.68, "label": "Raw\nTelemetry"},
        {"x1": 9.12, "x2": 9.78, "label": "Physics\nVector"},
        {"x1": 12.22, "x2": 12.88, "label": "Calibrated\nJSON"}
    ]
    for g in gaps:
        ax.annotate("", xy=(g['x2'], 3.85), xytext=(g['x1'], 3.85),
                    arrowprops=dict(arrowstyle="-|>", lw=1.6, color='black', mutation_scale=13))
        ax.text((g['x1'] + g['x2'])/2, 4.3, g['label'], ha='center', va='center',
                fontsize=7.2, color='black', fontweight='bold', family='sans-serif', multialignment='center',
                bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'))

    # Bottom Pipeline Summary Box
    sum_box = patches.FancyBboxPatch((0.5, 0.2), 14.8, 0.52, boxstyle="round,pad=0.06",
                                     fc='#F3F4F6', ec='black', lw=1.2)
    ax.add_patch(sum_box)
    ax.text(7.9, 0.46, "DATA PROCESSING PIPELINE: Location Request --> Telemetry Ingestion --> 62 Physics Features --> GBDT Ensemble & Gemini LLM --> Radar Decision Dashboard",
            ha='center', va='center', color='black', fontsize=7.8, fontweight='bold', family='sans-serif')

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor='white', edgecolor='none')
    plt.close()
    print("Saved proposed system block diagram (B&W):", filepath)


if __name__ == "__main__":
    create_proposed_architecture_bw("report/proposed_system_architecture.png")
    create_existing_workflow_bw("report/existing_system_workflow.png")
    create_proposed_block_diagram_bw("report/proposed_system_block_diagram.png")
    print("All 3 B&W diagrams generated successfully!")
