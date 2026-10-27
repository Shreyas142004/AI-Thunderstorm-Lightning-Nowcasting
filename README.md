# ⚡ AeroCast AI — Convective Weather & Thunderstorm Nowcasting System for Karnataka

> **An intelligent, physics-informed nowcasting platform engineered for real-time thunderstorm and lightning prediction within a 0 to 90-minute window (+30m, +60m, +90m), combining atmospheric thermodynamics, a 27-year regional climatology, and Google Gemini Generative AI across Karnataka, India.**

---

## 📌 Project Overview

Tropical thunderstorms, cloud-to-ground lightning discharges, and localized downbursts inflict severe damage across Karnataka, particularly in the Western Ghats and coastal belt (Dakshina Kannada, Udupi, Kodagu, Chikkamagaluru, and Shivamogga). 

Conventional Numerical Weather Prediction (NWP) models (GFS/ECMWF) update only every 3 to 6 hours on coarse grids, failing to resolve rapid convective storm cells igniting and striking within 30 to 60 minutes. Furthermore, standard machine learning models frequently trigger **nocturnal false alarms** in coastal valleys due to high nighttime relative humidity ($>90\%$).

**AeroCast AI** overcomes these challenges by unifying:
1. **Live High-Resolution Atmospheric Telemetry** (Open-Meteo & Visual Crossing fallback).
2. **62-Feature Atmospheric Physics Engine** (Dew Point Depression, Vapor Pressure Deficit, and Diurnal Solar Insolation Weighting).
3. **27-Year Karnataka Historical Climatology** ($9,862$ verified daily observations from 2000 to 2027).
4. **Soft-Voting GBDT Ensemble Core** (LightGBM, XGBoost, and HistGradientBoosting) achieving **91.24% Holdout Accuracy**.
5. **Authoritative 30,753-Village Boundary Engine** (`karnataka_places.py` indexing all 31 districts, 240 taluks, and 30,753 villages).
6. **Google Gemini Generative AI** translating numerical distributions into plain-language synoptic advisories for agriculture, transit, and public safety.
7. **Interactive S-Band Doppler Radar Canvas** with concentric range rings ($25\text{ km}$, $50\text{ km}$, $100\text{ km}$).

---

## 🌟 Key Capabilities & Features

* **⚡ 0 to 90-Minute Nowcasting**: Delivers calibrated storm and lightning risk probabilities for immediate frontline decision support.
* **⏱️ 3-Step Dynamic Timeline Progression**: Real-time convective hazard projection cards at **+30m**, **+60m**, and **+90m** horizons with dynamic risk-colored theming:
  - 🟢 **Low / No Risk** ($<35\%$): Fair Weather / Clear Sky
  - 🟡 **Moderate Watch** ($35\% - 69.9\%$): Convective Initiation / Thunderstorm Watch
  - 🔴 **Critical Alert** ($\ge 70\%$): Severe Thunderstorm / Downburst / Lightning Warning
* **🚫 Zero Nocturnal False Alarms**: Uses continuous boundary-layer saturation metrics (Dew Point Depression $\text{DPD} = T - T_d$ and Vapor Pressure Deficit $\text{VPD}$) modulated by local diurnal solar heating ($D_f$) to prevent false warnings during calm, high-humidity nighttime hours.
* **🗺️ Interactive Leaflet S-Band Doppler Radar**: Renders interactive radar sweeps with concentric range rings ($25\text{ km}$, $50\text{ km}$, $100\text{ km}$) and simulated reflectivity echo contours.
* **📍 Authoritative Karnataka Boundary Lock**: Powered by `processed_data/karnataka_villages.csv` (30,753 villages, 240 mandals, 31 districts). Queries outside Karnataka (e.g., Goa, Sikkim, Andhra Pradesh, Mumbai) are strictly geo-fenced — the map flies to their real geographical position, predictions and telemetry are disabled, and a prominent warning alert is displayed.
* **🌾 Sector-Specific Generative Advisories**: Google Gemini AI synthesizes plain-language guidance:
  - **Plantation & Agriculture**: Areca nut drying, pepper harvest, and rubber tapping precautions.
  - **Travel & Highway Safety**: Ghat road slickness, visibility drops, and valley downdrafts.
  - **Aviation & Outdoors**: Lightning strike hazards and outdoor safety protocols.
* **🎨 Dual Theme Design System**: Handcrafted responsive UI supporting **Warm Beige** (Light) and **Roasted Espresso** (Dark) themes.

---

## 🏗️ 4-Tier System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    1. PRESENTATION LAYER (USER DASHBOARD)               │
│  - Interactive S-Band Doppler Radar (Leaflet.js Range Rings 25-100 km) │
│  - Convective Risk Dial & Timeline Cards (+30m / +60m / +90m)           │
│  - Taluk Micro-Zones & Gemini Sector Advisories (Agri, Transit, Public) │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / REST Requests
┌────────────────────────────────────▼────────────────────────────────────┐
│              2. GATEWAY & BOUNDARY VALIDATION LAYER (FLASK)             │
│  - Flask 3.0+ REST Gateway (Request Routing, CORS & In-Memory Cache)    │
│  - Karnataka State Boundary Validator (11.5°N–18.6°N, 74.0°E–78.6°E)     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Dispatches Validated Queries
┌────────────────────────────────────▼────────────────────────────────────┐
│                    3. CORE SERVICES & AI INFERENCE ENGINE               │
│  - Ingestion: Open-Meteo High-Resolution Telemetry & Live Soundings     │
│  - Physics Engine: 62 Atmospheric Features (DPD, VPD, Df Factor, Theta) │
│  - ML Classifier: Soft-Voting GBDT Ensemble (LightGBM + XGBoost + HGB)  │
│  - Generative AI: Google Gemini Cloud LLM (Synoptic Advisory Synthesis) │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Reads / Serializes
┌────────────────────────────────────▼────────────────────────────────────┐
│                             4. STORAGE LAYER                            │
│  - 27-Year Karnataka Climate Dataset (9,862 verified daily records)     │
│  - 30,753 Karnataka Villages & Taluks LGD Census Repository (CSV)       │
│  - Serialized Trained Models Repository (best_convective_model.joblib)  │
│  - Geospatial GeoJSON Boundaries & Telemetry Response Cache             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
D:\Projects\Major-Project\
├── app.py                          # Flask REST API Web Server & Nowcasting Endpoints
├── config.py                       # Global configuration & environment loader
├── karnataka_places.py             # 30,753 Villages Index & State Boundary Validation Engine
├── gemini_nowcast.py               # Google Gemini Generative AI Advisory Engine
├── predict_live.py                 # Live Meteorological Telemetry Fetcher & ML Pipeline
├── preprocess_features.py          # 62-Feature Physics Engineering Pipeline
├── train_models.py                 # GBDT Model Benchmarking & Serialization Script
├── requirements.txt                # Python Dependencies & Environment Specifications
├── README.md                       # Comprehensive Project Documentation
├── .env                            # API Keys & Local Configuration
├── .gitignore                      # Git tracking exclusions
│
├── dataset/
│   └── karnataka_dataset.xlsx      # 27-Year Karnataka Meteorological Records (2000–2027)
│
├── processed_data/
│   ├── karnataka_convective_features.csv # Cleaned & Processed 62-Feature Matrix
│   └── karnataka_villages.csv      # 30,753 Villages, 240 Taluks & 31 Districts (LGD Directory)
│
├── models/
│   ├── best_convective_model.joblib# Serialized Winning Soft-Voting GBDT Ensemble
│   ├── feature_columns.json        # 62 Feature Schema for Live Inference
│   └── metrics_summary.json        # Holdout Evaluation Metrics Summary
│
├── static/
│   ├── css/
│   │   └── style.css               # Warm Beige (Light) & Roasted Espresso (Dark) Theme Tokens
│   ├── js/
│   │   └── app.js                  # Frontend Telemetry, Doppler Radar & UI Interactivity
│   └── vendor/
│       ├── leaflet.css             # Leaflet GIS Mapping Stylesheet
│       └── leaflet.js              # Leaflet GIS Interactive Mapping Engine
│
├── templates/
│   └── index.html                  # Responsive Convective Weather Dashboard Template
│
└── report/
    ├── AeroCast_AI_Report.tex      # Academic Project Report (LaTeX Source, 25 Papers Surveyed)
    ├── AeroCast_AI_PPT.pptx        # Final Project Presentation Slide Deck
    ├── proposed_system_architecture.png # 4-Tier Black & White System Architecture Diagram
    ├── studentDashboard.png        # Screenshot: Convective Risk Dial & Telemetry Stack
    ├── headDashboard.png           # Screenshot: S-Band Doppler Radar & Micro-Zones Panel
    └── skillGap.png                # Screenshot: 3-Step Timeline Progression & Gemini Advisories
```

---

## 📊 Machine Learning Pipeline & Evaluation

The predictive engine was benchmarked on a **70% Training / 30% Testing** chronological split across the 27-year Karnataka climatological dataset:
- **Training Set (70% | 2000–2018)**: 6,568 historical daily observation records.
- **Holdout Test Set (30% | 2019–2027)**: 3,287 historical daily observation records.

### Benchmark Results on 30% Holdout Test Set

| Model Architecture | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Baseline)** | 86.43% | 0.8273 | 0.9069 | 0.8653 | 0.9490 |
| **Random Forest Classifier** | 83.69% | 0.8128 | 0.8581 | 0.8349 | 0.9203 |
| **HistGradientBoosting (Scikit-Learn)** | 90.84% | 0.8732 | 0.9468 | 0.9085 | 0.9716 |
| **LightGBM Classifier** | 90.90% | 0.8717 | 0.9506 | 0.9094 | 0.9713 |
| **XGBoost Classifier** | 91.27% | 0.8850 | 0.9405 | 0.9119 | 0.9712 |
| **Soft Voting GBDT Ensemble (Winning Model)** 🏆 | **91.24%** | **0.8773** | **0.9506** | **0.9125** | **0.9723** |

*The winning **Soft Voting Ensemble (weights: LightGBM: 1.2, XGBoost: 1.2, HistGradientBoosting: 1.0)** was fitted on 100% of historical records ($9,862$ samples) and serialized to `models/best_convective_model.joblib`.*

---

## 🔬 Mathematical Formulations

### 1. Dew Point Depression (DPD)
$$\text{DPD} = T - T_d$$
where $T$ is dry-bulb surface temperature ($^\circ\text{C}$) and $T_d$ is dew point temperature ($^\circ\text{C}$). A $\text{DPD} < 3^\circ\text{C}$ indicates near-surface saturation.

### 2. Vapor Pressure Deficit (VPD)
Using the Magnus-Tetens formulation for saturation vapor pressure ($e_s$) and actual vapor pressure ($e$):
$$e = 6.112 \times \exp\left(\frac{17.67 \times T_d}{T_d + 243.5}\right), \quad e_s = 6.112 \times \exp\left(\frac{17.67 \times T}{T + 243.5}\right)$$
$$\text{VPD} = e_s - e \quad (\text{hPa})$$

### 3. Diurnal Solar Insolation Factor ($D_f$)
Convective initiation in tropical regimes is fundamentally governed by daytime solar heating. Convective potential is modulated across four diurnal time windows:
$$D_f(h) = \begin{cases} 
1.25, & 13 \le h \le 18 \quad (\text{Afternoon thermal convection peak}) \\
1.00, & 11 \le h < 13 \;\lor\; 18 < h \le 20 \quad (\text{Transition hours}) \\
0.70, & 07 \le h < 11 \quad (\text{Morning boundary-layer heating}) \\
0.42, & \text{otherwise} \quad (\text{Nocturnal radiational cooling})
\end{cases}$$

### 4. Bayesian Climatological Prior Fusion
Combines 27-year historical monthly precipitation frequencies $P_{\text{base}}(m)$ (ranging from $2.1\%$ in January to $62.4\%$ in July) with real-time convective energy $E_{\text{conv}}$:
$$P_{\text{fused}} = 0.35 \times P_{\text{base}}(m) + 0.65 \times (E_{\text{conv}} \times D_f)$$
*Eliminates false alarms during calm, high-humidity nighttime periods in coastal valleys (e.g., Puttur, Bantwal), yielding realistic low risk ($15\text{–}28\%$, Green alert) rather than false $98\%$ critical alarms.*

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.10 or higher.
- Modern web browser (Chrome, Edge, Firefox) with WebGL enabled.

### 2. Installation
Clone the repository and install required Python dependencies:
```bash
git clone https://github.com/your-username/AeroCast-AI.git
cd AeroCast-AI
pip install -r requirements.txt
```
*(Dependencies: `flask`, `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `xgboost`, `joblib`, `openpyxl`)*

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
VISUAL_CROSSING_API_KEY=your_visual_crossing_key_here  # Optional fallback
```

### 4. Train / Re-evaluate Models
```bash
python preprocess_features.py  # Generates 62-feature dataset
python train_models.py         # Trains and benchmarks GBDT ensemble
```

### 5. Launch Real-Time Nowcasting Web Server
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Verification & Out-of-Bounds Testing

The system was rigorously evaluated across Karnataka microclimates and out-of-state test queries:

| Test Query | Region / State | Boundary Status | Coordinates | Probability Output | Dashboard Behavior |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Puttur** | Dakshina Kannada, KA | ✅ Inside KA | `12.7667°N, 75.2016°E` | `28.5%` (Low Risk) | Full Live Weather, Timeline & S-Band Radar active |
| **Bengaluru** | Bengaluru Urban, KA | ✅ Inside KA | `12.9716°N, 77.5946°E` | `18.5%` (Low Risk) | Live Telemetry & Sector Advisories active |
| **108 Kalthur** | Udupi, KA | ✅ Inside KA | `13.2248°N, 74.7431°E` | `75.2%` (Critical) | High Convective Alert with dynamic Red styling |
| **Goa** | Goa State | ❌ Outside KA | `15.2993°N, 74.1240°E` | `N/A (Disabled)` | Map flies to Goa, weather hidden, warning banner displayed |
| **Sikkim** | Sikkim State | ❌ Outside KA | `27.5330°N, 88.5122°E` | `N/A (Disabled)` | Map flies to Sikkim, predictions locked |
| **Andhra Pradesh** | Andhra Pradesh State | ❌ Outside KA | `15.9129°N, 79.7400°E` | `N/A (Disabled)` | Map flies to AP, predictions locked |
| **Mumbai** | Maharashtra State | ❌ Outside KA | `19.0760°N, 72.8777°E` | `N/A (Disabled)` | Out-of-bounds alert, radar scan inactive |

---

## 📄 Academic Deliverables

- **LaTeX Project Report**: [`report/AeroCast_AI_Report.tex`](file:///d:/Projects/Major-Project/report/AeroCast_AI_Report.tex) — Complete 5-chapter report compliant with university guidelines, surveying 25 recent research papers with mathematical formulations and comparative analysis.
- **Project Presentation Deck**: [`report/AeroCast_AI_PPT.pptx`](file:///d:/Projects/Major-Project/report/AeroCast_AI_PPT.pptx) — Presentation slide deck with crisp bullet points, architecture diagrams, and literature review references.

---

## 📜 License
This project is developed for academic and disaster-preparedness research purposes.
