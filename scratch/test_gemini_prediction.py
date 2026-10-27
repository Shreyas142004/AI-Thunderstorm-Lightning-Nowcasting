import os
import sys
import json
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GEMINI_API_KEY
import predict_live as pl

# Test with Puttur live data
wdata = pl.fetch_weather_data_accurate("Puttur")
print("Live weather for Puttur fetched:", wdata.get("temp"), "C, dew:", wdata.get("dew"), "C, clouds:", wdata.get("cloudcover"))

prompt = f"""You are AeroCast AI's Chief Meteorological Scientist specializing in convective nowcasting and atmospheric thermodynamics across Karnataka, India.

Your task is to predict the near-term CONVECTIVE STORM / THUNDERSTORM RISK PROBABILITY for:
Location: Puttur, Dakshina Kannada, Karnataka (Western Ghats Foothills)

LIVE ATMOSPHERIC TELEMETRY:
- Temperature: {wdata.get('temp')}°C
- Dew Point: {wdata.get('dew')}°C
- Relative Humidity: {wdata.get('humidity')}%
- Cloud Cover: {wdata.get('cloudcover')}%
- Barometric Pressure: {wdata.get('pressure')} hPa
- Wind Speed & Direction: {wdata.get('windspeed')} km/h ({wdata.get('winddir')}°)
- Current Sky Condition: {wdata.get('conditions')}
- Local Time: Late Night (23:30 IST)

HISTORICAL DATASET CLIMATOLOGY (Karnataka Meteorological Dataset):
- Month: October (Post-Monsoon Transition)
- Baseline Historical Karnataka Rain Probability in October: 55.0%
- Average Thunderstorm Dew Point: 20-24°C
- Nocturnal boundary layer saturation in coastal valleys is common without convective lifting.

Evaluate the thermodynamic stability, diurnal insolation absence at night, orographic moisture, and compute an accurate, calibrated convective storm probability (0-100%).

Respond ONLY with valid JSON with these keys:
{{
  "convective_probability": <float between 0 and 100>,
  "risk_level": <"FAIR WEATHER / LOW RISK" or "MODERATE CONVECTIVE WATCH" or "CRITICAL CONVECTIVE ALERT">,
  "alert_code": <"GREEN" or "YELLOW" or "RED">,
  "weather_condition": <short string e.g. "Partly Cloudy / Humid Night">,
  "synoptic_bulletin": <expert explanation of thermodynamics>
}}
"""

models_to_try = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-pro-latest"]
success = False

for model_name in models_to_try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }
    print(f"Trying model: {model_name}...")
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                out = res["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Success with {model_name}:")
                print(out)
                success = True
                break
        except Exception as e:
            print(f"Attempt {attempt+1} on {model_name} failed: {e}")
            import time
            time.sleep(1)
    if success:
        break

