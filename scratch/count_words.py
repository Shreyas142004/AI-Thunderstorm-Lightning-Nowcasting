import re

abstract = r"""\noindent \textbf{AeroCast AI} is an intelligent, physics-informed convective weather and thunderstorm nowcasting system engineered to deliver high-precision, short-term ($0$--$90$ minutes) meteorological predictions across Karnataka, with specialized calibration for the Western Ghats and coastal regions. Tropical thunderstorms, convective lightning discharges, and localized downbursts pose severe risks to agriculture, transport, and public safety. Conventional Numerical Weather Prediction models suffer from update latency ($3$--$6$ hours) and coarse resolutions that fail to resolve fast-evolving convective cells igniting within $30$ to $60$ minutes. AeroCast AI bridges this gap by unifying a 27-year historical Karnataka climatological dataset ($9,862$ verified daily records from 2000 to 2027), real-time atmospheric telemetry, and multimodal generative reasoning via the Google Gemini API. The system implements a 62-feature atmospheric pipeline computing continuous thermodynamic indices, including Dew Point Depression, Vapor Pressure Deficit, and Equivalent Potential Temperature to suppress nocturnal false alarms. A soft-voting Gradient Boosted Decision Tree ensemble (LightGBM, XGBoost, HistGradientBoosting) achieves 91.2\% holdout accuracy, calibrated alongside climatological priors. Integrated Gemini AI reasoning translates complex predictive distributions into calibrated convective risk probabilities, a 3-step timeline progression ($+30$m, $+60$m, $+90$m), and plain-language domain advisories for agriculture, transit, and public safety. An interactive Leaflet.js Doppler radar interface delivers accessible, low-latency decision support for regional disaster preparedness."""

s = abstract
s = re.sub(r'\\noindent\s*', '', s)
s = re.sub(r'\\textbf\{([^}]+)\}', r'\1', s)
s = re.sub(r'\\cite\{[^}]+\}', '', s)
s = s.replace(r'\%', '%')
s = re.sub(r'\$([^$]+)\$', r'\1', s)
s = s.replace('--', '-')

words = s.split()
print("Readable word count:", len(words))
print("Raw LaTeX space-separated words:", len(abstract.split()))
