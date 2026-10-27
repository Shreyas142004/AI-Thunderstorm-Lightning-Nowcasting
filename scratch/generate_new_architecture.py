import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_monitor(ax, cx, cy, w=0.50, h=0.36):
    ax.add_patch(patches.FancyBboxPatch((cx - w/2, cy - h/2 + 0.04), w, h,
                                       boxstyle='round,pad=0.02', fc='white', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Rectangle((cx - w/2 + 0.035, cy - h/2 + 0.075), w - 0.07, h - 0.07,
                                   fc='#F3F4F6', ec='black', lw=0.8, zorder=7))
    ax.plot([cx, cx], [cy - h/2 + 0.04, cy - h/2 - 0.04], color='black', lw=1.4, zorder=6)
    ax.plot([cx - 0.14, cx + 0.14], [cy - h/2 - 0.04, cy - h/2 - 0.04], color='black', lw=1.4, zorder=6)

def draw_radar(ax, cx, cy, r=0.22):
    ax.add_patch(patches.Circle((cx, cy), r, fc='#F9FAFB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Circle((cx, cy), r * 0.65, fc='none', ec='black', lw=0.8, ls='--', zorder=7))
    ax.add_patch(patches.Circle((cx, cy), r * 0.32, fc='none', ec='black', lw=0.8, zorder=7))
    ax.plot([cx - r, cx + r], [cy, cy], color='black', lw=0.8, zorder=7)
    ax.plot([cx, cx], [cy - r, cy + r], color='black', lw=0.8, zorder=7)
    ax.plot([cx, cx + r*0.7], [cy, cy + r*0.7], color='black', lw=1.5, zorder=8)

def draw_server(ax, cx, cy, w=0.50, h=0.36):
    for dy in [0.09, 0.0, -0.09]:
        ax.add_patch(patches.FancyBboxPatch((cx - w/2, cy + dy - 0.035), w, 0.07,
                                           boxstyle='round,pad=0.012', fc='white', ec='black', lw=1.0, zorder=6))
        ax.plot([cx - w/2 + 0.06, cx + w/2 - 0.14], [cy + dy, cy + dy], color='#4B5563', lw=1.0, zorder=7)
        ax.plot([cx + w/2 - 0.08, cx + w/2 - 0.04], [cy + dy, cy + dy], 'o', color='black', markersize=2.0, zorder=7)

def draw_shield(ax, cx, cy, w=0.36, h=0.42):
    pts = np.array([
        [cx - w/2, cy + h/2],
        [cx + w/2, cy + h/2],
        [cx + w/2, cy - h/6],
        [cx, cy - h/2],
        [cx - w/2, cy - h/6]
    ])
    ax.add_patch(patches.Polygon(pts, closed=True, fc='#F3F4F6', ec='black', lw=1.2, zorder=6))
    ax.plot([cx - 0.08, cx - 0.02, cx + 0.09], [cy, cy - 0.06, cy + 0.08], color='black', lw=1.8, zorder=7)

def draw_gear(ax, cx, cy, r=0.18):
    ax.add_patch(patches.Circle((cx, cy), r, fc='#E5E7EB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Circle((cx, cy), r * 0.45, fc='white', ec='black', lw=1.0, zorder=7))
    for deg in range(0, 360, 45):
        rad = np.radians(deg)
        x1, y1 = cx + (r - 0.02) * np.cos(rad), cy + (r - 0.02) * np.sin(rad)
        x2, y2 = cx + (r + 0.06) * np.cos(rad), cy + (r + 0.06) * np.sin(rad)
        ax.plot([x1, x2], [y1, y2], color='black', lw=2.2, zorder=6)

def draw_brain(ax, cx, cy, s=0.18):
    ax.plot(cx, cy + s*0.7, 'o', color='black', markersize=4.0, zorder=7)
    ax.plot(cx - s*0.65, cy - s*0.5, 'o', color='black', markersize=3.5, zorder=7)
    ax.plot(cx + s*0.65, cy - s*0.5, 'o', color='black', markersize=3.5, zorder=7)
    ax.plot(cx - s*0.25, cy - s*0.5, 'o', color='black', markersize=3.0, zorder=7)
    ax.plot(cx + s*0.25, cy - s*0.5, 'o', color='black', markersize=3.0, zorder=7)
    ax.plot([cx, cx - s*0.65], [cy + s*0.7, cy - s*0.5], color='black', lw=1.2, zorder=6)
    ax.plot([cx, cx + s*0.65], [cy + s*0.7, cy - s*0.5], color='black', lw=1.2, zorder=6)
    ax.plot([cx, cx - s*0.25], [cy + s*0.7, cy - s*0.5], color='black', lw=1.0, zorder=6)
    ax.plot([cx, cx + s*0.25], [cy + s*0.7, cy - s*0.5], color='black', lw=1.0, zorder=6)

def draw_sparkle(ax, cx, cy, s=0.22):
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

def draw_database(ax, cx, cy, w=0.50, h=0.40):
    ax.add_patch(patches.Rectangle((cx - w/2, cy - h/2 + 0.06), w, h - 0.12,
                                   fc='#F9FAFB', ec='black', lw=1.2, zorder=6))
    ax.add_patch(patches.Ellipse((cx, cy + h/2 - 0.06), w, 0.13,
                                 fc='white', ec='black', lw=1.2, zorder=7))
    ax.add_patch(patches.Arc((cx, cy), w, 0.12, theta1=180, theta2=360,
                             color='black', lw=1.0, zorder=7))
    ax.add_patch(patches.Arc((cx, cy - h/2 + 0.06), w, 0.13, theta1=180, theta2=360,
                             color='black', lw=1.2, zorder=7))


def generate_architecture_diagram(filepath):
    # Total canvas: 18.0 x 10.6 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(18.0, 10.6), dpi=300)
    ax.set_xlim(0, 18.0)
    ax.set_ylim(0, 10.6)
    ax.axis('off')
    
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # -------------------------------------------------------------------------
    # MAIN HEADER
    # -------------------------------------------------------------------------
    title_box = patches.FancyBboxPatch((0.5, 9.75), 17.0, 0.65, boxstyle='round,pad=0.06',
                                       fc='#E5E7EB', ec='black', lw=1.6, zorder=2)
    ax.add_patch(title_box)
    ax.text(9.0, 10.07, "AeroCast AI: 4-Tier Operational System Architecture",
            ha='center', va='center', fontsize=14.0, fontweight='bold', family='sans-serif', color='black')

    # =========================================================================
    # 1. PRESENTATION LAYER (WHAT USER CAN SEE ON DASHBOARD)
    # Coordinates: x in [0.5, 3.9], width = 3.4, height = 9.05 (y in [0.45, 9.50])
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch((0.5, 0.45), 3.4, 9.05, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(0.7, 9.22, "1. Presentation Layer (Dashboard)", fontsize=11.0, fontweight='bold', family='sans-serif')
    
    # 1.1 S-Band Doppler Radar Map
    ax.add_patch(patches.FancyBboxPatch((0.68, 6.45), 3.04, 2.55, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_radar(ax, 2.2, 8.35, r=0.22)
    ax.text(2.2, 7.82, "Interactive S-Band Doppler Radar", ha='center', va='center',
            fontsize=9.2, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(2.2, 7.05, "Leaflet.js Geospatial Mapping Canvas\n25–100 km Range Rings & dBZ Reflectivity\nLive Precipitation Echo Tracking & Motion",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 1.2 Convective Risk & Timeline Cards
    ax.add_patch(patches.FancyBboxPatch((0.68, 3.50), 3.04, 2.65, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_monitor(ax, 2.2, 5.42)
    ax.text(2.2, 4.85, "Convective Risk & Timeline Cards", ha='center', va='center',
            fontsize=9.2, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(2.2, 4.10, "+30m, +60m, +90m Nowcast Horizons\nDynamic Severity Badges (Green / Yellow / Red)\nReal-Time Telemetry HUD (DPD, VPD, T, RH)",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 1.3 Taluk Micro-Zones & AI Advisory
    ax.add_patch(patches.FancyBboxPatch((0.68, 0.65), 3.04, 2.55, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_sparkle(ax, 2.2, 2.45, s=0.22)
    ax.text(2.2, 1.95, "Taluk Micro-Zones & AI Advisory", ha='center', va='center',
            fontsize=9.2, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(2.2, 1.25, "Sub-Zone Hazard Tables (Puttur, Sullia, etc.)\nGemini Plain-Language Synoptic Bulletins\nSector Advisories (Agri / Transport / Safety)",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # =========================================================================
    # 2. GATEWAY & SECURITY LAYER
    # Coordinates: x in [4.35, 7.75], width = 3.4, height = 9.05 (y in [0.45, 9.50])
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch((4.35, 0.45), 3.4, 9.05, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(4.55, 9.22, "2. Gateway & Security Layer", fontsize=11.0, fontweight='bold', family='sans-serif')

    # 2.1 FastAPI REST Gateway
    ax.add_patch(patches.FancyBboxPatch((4.55, 5.25), 3.0, 3.80, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_server(ax, 6.05, 8.32)
    ax.text(6.05, 7.60, "FastAPI REST Gateway", ha='center', va='center',
            fontsize=10.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(6.05, 6.45, "High-Throughput Async REST Endpoints\n(/api/predict, /api/radar, /api/bulletin)\nRequest Routing & Load Dispatching\nStrict CORS & Rate Limiting Enforcement\nJSON Telemetry & Nowcast Serialization",
            ha='center', va='center', fontsize=7.4, color='#374151', family='sans-serif', zorder=5)

    # 2.2 Security & JWT Authentication Engine
    ax.add_patch(patches.FancyBboxPatch((4.55, 0.65), 3.0, 3.90, boxstyle='round,pad=0.06',
                                       fc='#F3F4F6', ec='black', lw=1.2, zorder=2))
    draw_shield(ax, 6.05, 3.82)
    ax.text(6.05, 3.10, "JWT Auth & Security Engine", ha='center', va='center',
            fontsize=10.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(6.05, 1.90, "JSON Web Token (JWT) Cryptographic Auth\nToken Expiration & Signature Verification\nAPI Key Verification & Role Permissions\nKarnataka Boundary Lock Validator\n(11.5°N–18.6°N, 74.0°E–78.6°E Bounding)",
            ha='center', va='center', fontsize=7.3, color='#374151', family='sans-serif', zorder=5)

    # Bidirectional arrow between Gateway and Security
    ax.annotate("", xy=(6.05, 5.23), xytext=(6.05, 4.57),
                arrowprops=dict(arrowstyle="<->", lw=1.4, color='black'))
    ax.text(6.05, 4.90, "Auth Interceptor / Verify Token", ha='center', va='center', fontsize=7.2,
            fontweight='bold', color='black', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='black', lw=0.6))

    # =========================================================================
    # 3. CORE SERVICES & AI ENGINE (MODEL, API & DATASET PROCESSING)
    # Coordinates: x in [8.85, 17.5], width = 8.65, height = 4.25 (y in [5.25, 9.50])
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch((8.85, 5.25), 8.65, 4.25, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(9.05, 9.22, "3. Core Services & AI Engine (Model, API & Dataset Processing)",
            fontsize=11.0, fontweight='bold', family='sans-serif')

    # 3.1 API Telemetry Processing
    ax.add_patch(patches.FancyBboxPatch((9.05, 7.30), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_server(ax, 9.60, 8.18, w=0.38, h=0.28)
    ax.text(11.30, 8.48, "API Telemetry Processing", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.30, 7.78, "Open-Meteo & IMD Radar Live Ingestion\nMulti-Level Atmospheric Sounding Ingest\nCoordinate Resolution & Missing Fill",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 3.2 Dataset & Physics Processing
    ax.add_patch(patches.FancyBboxPatch((13.25, 7.30), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='#E5E7EB', ec='black', lw=1.2, zorder=2))
    draw_gear(ax, 13.80, 8.18, r=0.16)
    ax.text(15.50, 8.48, "Dataset & Physics Processing", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(15.50, 7.78, "62 Thermodynamic Features (DPD, VPD, θe)\nDiurnal Solar Weighting (Df Factor)\nBoundary-Layer Stability Filtering",
            ha='center', va='center', fontsize=7.2, color='#1F2937', family='sans-serif', zorder=5)

    # 3.3 Soft-Voting GBDT Ensemble (Model Processing)
    ax.add_patch(patches.FancyBboxPatch((9.05, 5.40), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_brain(ax, 9.60, 6.28, s=0.16)
    ax.text(11.30, 6.58, "Soft-Voting GBDT Ensemble", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.30, 5.88, "LightGBM + XGBoost + HistGradient\n91.2% Test Accuracy (+30, +60, +90m)\nMulti-Horizon Storm Classification",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 3.4 Chief Meteorologist AI Engine (Model Processing)
    ax.add_patch(patches.FancyBboxPatch((13.25, 5.40), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_sparkle(ax, 13.80, 6.28, s=0.18)
    ax.text(15.50, 6.58, "Chief Meteorologist AI", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(15.50, 5.88, "Google Gemini LLM Reasoning Engine\nMulti-Factor Synoptic Understanding\nPlain-Language Sector Warnings",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # Horizontal arrows inside Core Services
    ax.annotate("", xy=(13.20, 8.18), xytext=(13.12, 8.18),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color='black', mutation_scale=10))
    ax.annotate("", xy=(13.20, 6.28), xytext=(13.12, 6.28),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color='black', mutation_scale=10))

    # =========================================================================
    # 4. STORAGE LAYER
    # Coordinates: x in [8.85, 17.5], width = 8.65, height = 4.25 (y in [0.45, 4.70])
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch((8.85, 0.45), 8.65, 4.25, boxstyle='round,pad=0.1',
                                       fc='white', ec='black', lw=1.5, zorder=1))
    ax.text(9.05, 4.42, "4. Storage Layer", fontsize=11.0, fontweight='bold', family='sans-serif')

    # 4.1 27-Year Karnataka Climatological Dataset
    ax.add_patch(patches.FancyBboxPatch((9.05, 2.50), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 9.60, 3.38)
    ax.text(11.30, 3.68, "27-Yr Climatological Dataset", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.30, 2.98, "9,862 Daily Observations (1997–2024)\nRegional Rain & Storm Frequency Priors\nOptimized Fast-Query Parquet Format",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 4.2 Model Artifacts Repository
    ax.add_patch(patches.FancyBboxPatch((13.25, 2.50), 4.05, 1.75, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 13.80, 3.38)
    ax.text(15.50, 3.68, "Model Artifacts Repository", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(15.50, 2.98, "Serialized Model Pipelines (.joblib)\nLightGBM, XGBoost, Scalers & Weights\nIn-Memory High-Speed Loading",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 4.3 Database & Query Cache
    ax.add_patch(patches.FancyBboxPatch((9.05, 0.65), 4.05, 1.70, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 9.60, 1.50)
    ax.text(11.30, 1.80, "Database & Query Cache", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(11.30, 1.10, "PostgreSQL / SQLite Session Store\nJWT Auth Tokens & Audit Request Logs\nFast Telemetry Response Caching",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # 4.4 Geospatial Repository
    ax.add_patch(patches.FancyBboxPatch((13.25, 0.65), 4.05, 1.70, boxstyle='round,pad=0.06',
                                       fc='white', ec='black', lw=1.2, zorder=2))
    draw_database(ax, 13.80, 1.50)
    ax.text(15.50, 1.80, "Geospatial GeoJSON Repository", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='black', family='sans-serif', zorder=5)
    ax.text(15.50, 1.10, "Karnataka State & Taluk Polygons\nRadar Station Coordinates & Rings\nCartoDB Base Layer Vector Tiles",
            ha='center', va='center', fontsize=7.2, color='#374151', family='sans-serif', zorder=5)

    # =========================================================================
    # INTERCONNECTING ARROWS ACROSS TIERS (WITH CLEAN 1.10 GAP)
    # =========================================================================
    # 1. Presentation -> FastAPI Gateway (HTTPS / WSS)
    for y_pos in [7.72, 4.82, 1.92]:
        ax.plot([3.74, 4.12, 4.12, 4.53], [y_pos, y_pos, 7.15, 7.15], color='black', lw=1.2)
    ax.annotate("", xy=(4.53, 7.15), xytext=(4.43, 7.15),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color='black', mutation_scale=10))
    ax.text(4.12, 7.45, "HTTPS\nREST / WSS", fontsize=7.2, color='black', fontweight='bold',
            ha='center', family='sans-serif', bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))

    # 2. FastAPI Gateway -> Core Services & AI Engine (Telemetry & Inference Dispatch)
    ax.plot([7.57, 9.03], [8.18, 8.18], color='black', lw=1.4)
    ax.annotate("", xy=(9.03, 8.18), xytext=(8.93, 8.18),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=11))
    ax.text(8.30, 8.52, "Dispatches\nTelemetry &\nInference", fontsize=7.2, color='black',
            fontweight='bold', ha='center', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='black', lw=0.6))

    # 3. DIRECT CONNECTION: JWT Auth -> Core Services & AI Engine
    # Route: starts at (7.57, 3.20) -> (8.30, 3.20) -> (8.30, 6.28) -> (9.03, 6.28)
    ax.plot([7.57, 8.30, 8.30, 9.03], [3.20, 3.20, 6.28, 6.28], color='black', lw=1.4)
    ax.annotate("", xy=(9.03, 6.28), xytext=(8.93, 6.28),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=11))
    ax.text(8.30, 4.70, "Direct Connect:\nJWT Token Validation\nto Core & AI Engine", fontsize=6.8, color='black',
            fontweight='bold', ha='center', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='black', lw=0.6))

    # 4. DIRECT CONNECTION: JWT Auth -> Storage Layer
    # Direct horizontal connection from (7.57, 1.50) -> (9.03, 1.50)
    ax.plot([7.57, 9.03], [1.50, 1.50], color='black', lw=1.4)
    ax.annotate("", xy=(9.03, 1.50), xytext=(8.93, 1.50),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color='black', mutation_scale=11))
    ax.text(8.30, 1.82, "Direct Connect:\nJWT Session &\nToken Store",
            fontsize=6.8, color='black', fontweight='bold', ha='center', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='black', lw=0.6))

    # 5. Core Services <---> Storage Layer (Clean gap between 4.70 and 5.25)
    ax.annotate("", xy=(11.08, 4.70), xytext=(11.08, 5.25),
                arrowprops=dict(arrowstyle="<->", lw=1.3, color='black', mutation_scale=11))
    ax.text(11.08, 4.975, "Reads 27-Yr Climatology Norms", fontsize=7.1, color='black', fontweight='bold',
            ha='center', va='center', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='black', lw=0.5))

    ax.annotate("", xy=(15.28, 4.70), xytext=(15.28, 5.25),
                arrowprops=dict(arrowstyle="<->", lw=1.3, color='black', mutation_scale=11))
    ax.text(15.28, 4.975, "Loads Models & Caches Advisories", fontsize=7.1, color='black', fontweight='bold',
            ha='center', va='center', family='sans-serif',
            bbox=dict(boxstyle='square,pad=0.12', fc='white', ec='black', lw=0.5))

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, facecolor='white', edgecolor='none')
    plt.close()
    print("Saved refined 4-tier system architecture diagram:", filepath)

if __name__ == '__main__':
    generate_architecture_diagram('report/proposed_system_architecture.png')
