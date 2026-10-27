import shutil
from pathlib import Path
# pyrefly: ignore[missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore[missing-import]
import matplotlib.patches as patches

# 1. Copy dashboard screenshots
brain_dir = Path(r"C:\Users\SHREYAS RA\.gemini\antigravity-ide\brain\944bd2e3-75d2-4a0d-ba87-0d171a052264")
report_dir = Path("report")
report_dir.mkdir(exist_ok=True)

# Find matching screenshots
shots = {
    "studentDashboard.png": "puttur_main_page_loaded_1792479231226.png",
    "headDashboard.png": "kundapura_loaded_1792479736620.png",
    "skillGap.png": "dashboard_fully_loaded_1792425161286.png"
}

for dest, src in shots.items():
    src_path = brain_dir / src
    dest_path = report_dir / dest
    if src_path.exists():
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src} -> {dest}")
    else:
        # Fallback to any png
        any_png = list(brain_dir.glob("*.png"))
        if any_png:
            shutil.copy2(any_png[0], dest_path)
            print(f"Fallback copied {any_png[0].name} -> {dest}")

# 2. Generate Professional System Architecture Diagram (architecture.png)
fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis("off")

# Colors
c_telemetry = "#EBF3FA"
c_ai = "#F5EBE6"
c_ui = "#EDF4ED"
c_border = "#4A5568"

# Layer 1: Data Telemetry & Boundary Layer
rect1 = patches.FancyBboxPatch((0.5, 5.0), 11.0, 2.4, boxstyle="round,pad=0.2", ec="#3182CE", fc=c_telemetry, lw=2)
ax.add_patch(rect1)
ax.text(0.8, 7.1, "1. INGESTION & DATA VALIDATION LAYER", fontsize=12, fontweight="bold", color="#2B6CB0")

boxes_l1 = [
    ("Real-Time Telemetry\nOpen-Meteo REST API\n(Temp, Dew, Wind, Cloud, Press)", 0.8, 5.2, 3.2, 1.6),
    ("Geocoding & Boundary Guard\nKarnataka State Poly (11.5N-18.6N)\nOut-of-Bounds Lock & Alerts", 4.4, 5.2, 3.2, 1.6),
    ("27-Year Karnataka Dataset\nkarnataka_dataset.xlsx\n(9,862 Rows Climatology 2000-2027)", 8.0, 5.2, 3.2, 1.6)
]
for title, x, y, w, h in boxes_l1:
    b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", ec="#4299E1", fc="#FFFFFF", lw=1.5)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=8.5, color="#1A202C")

# Layer 2: Core Analytical & Generative AI Layer
rect2 = patches.FancyBboxPatch((0.5, 2.5), 11.0, 2.2, boxstyle="round,pad=0.2", ec="#DD6B20", fc=c_ai, lw=2)
ax.add_patch(rect2)
ax.text(0.8, 4.4, "2. ANALYTICAL & GENERATIVE AI ENGINE LAYER", fontsize=12, fontweight="bold", color="#C05621")

boxes_l2 = [
    ("62-Feature Physics Pipeline\nDew Point Depression (DPD)\nVPD (Magnus-Tetens) • Diurnal Factor", 0.8, 2.7, 3.2, 1.4),
    ("GBDT Soft-Voting Ensemble\nLightGBM + XGBoost + HistGB\n(91.2% Holdout Model)", 4.4, 2.7, 3.2, 1.4),
    ("Google Gemini Multimodal AI\nChief Meteorologist Reasoner\n(Synoptic Bulletins & Advisories)", 8.0, 2.7, 3.2, 1.4)
]
for title, x, y, w, h in boxes_l2:
    b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", ec="#ED8936", fc="#FFFFFF", lw=1.5)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=8.5, color="#1A202C")

# Layer 3: Presentation & Decision Support Layer
rect3 = patches.FancyBboxPatch((0.5, 0.3), 11.0, 1.9, boxstyle="round,pad=0.2", ec="#38A169", fc=c_ui, lw=2)
ax.add_patch(rect3)
ax.text(0.8, 1.9, "3. PRESENTATION & DECISION SUPPORT LAYER", fontsize=12, fontweight="bold", color="#276749")

boxes_l3 = [
    ("Concentric Risk Dial\n0-100% Probability\nDynamic Risk Pill (Grn/Yel/Red)", 0.8, 0.5, 2.5, 1.2),
    ("S-Band Doppler Radar\n25km / 50km / 100km Rings\nSimulated Reflectivity (dBZ)", 3.6, 0.5, 2.5, 1.2),
    ("3-Step Timeline Track\n+30m, +60m, +90m\nDynamic Risk Themed Cards", 6.4, 0.5, 2.5, 1.2),
    ("Micro-Zones & Advisories\nTaluk Corridor Monitoring\nAgriculture, Transit & Aviation", 9.2, 0.5, 2.0, 1.2)
]
for title, x, y, w, h in boxes_l3:
    b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", ec="#48BB78", fc="#FFFFFF", lw=1.5)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=8, color="#1A202C")

# Flow Arrows
arrow_style = dict(arrowstyle="->", lw=2, color="#2D3748")
ax.annotate("", xy=(2.4, 4.8), xytext=(2.4, 5.1), arrowprops=arrow_style)
ax.annotate("", xy=(6.0, 4.8), xytext=(6.0, 5.1), arrowprops=arrow_style)
ax.annotate("", xy=(9.6, 4.8), xytext=(9.6, 5.1), arrowprops=arrow_style)

ax.annotate("", xy=(2.0, 2.2), xytext=(2.0, 2.6), arrowprops=arrow_style)
ax.annotate("", xy=(4.8, 2.2), xytext=(4.8, 2.6), arrowprops=arrow_style)
ax.annotate("", xy=(7.6, 2.2), xytext=(7.6, 2.6), arrowprops=arrow_style)
ax.annotate("", xy=(10.2, 2.2), xytext=(10.2, 2.6), arrowprops=arrow_style)

plt.tight_layout()
arch_out = report_dir / "architecture.png"
plt.savefig(arch_out, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated system architecture diagram at {arch_out}")
