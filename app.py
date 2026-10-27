"""
AeroCast AI — Convective Nowcasting System Web Backend
======================================================
Serves the real-time AI weather nowcasting dashboard, integrating:
- Dual-source meteorological data fetcher (Open-Meteo & Visual Crossing fallback)
- 62-feature atmospheric physics pipeline (DPD, VPD, Theta-e, Moisture Flux)
- Serialized 91.24% holdout ensemble model (LGBM + XGB + HistGradientBoosting)
- Google Gemini API AI Chief Meteorologist & Advisory Engine
- Interactive Karnataka Doppler radar & sub-location micro-zones
"""

import os
import json
import math
import datetime
from pathlib import Path
# pyrefly: ignore[missing-import]
from flask import Flask, render_template, jsonify, request

from config import MODELS_DIR, GEMINI_API_KEY
import predict_live as pl
from gemini_nowcast import (
    predict_weather_with_gemini_and_dataset,
    generate_gemini_advisory,
    compute_dataset_physics_prior
)

app = Flask(__name__)

# Load model and schema at startup
MODEL, FEATURE_COLS = pl.load_model_and_schema()

# Cache for recent queries to avoid hammering external weather APIs
PREDICTION_CACHE = {}
CACHE_TTL_SECONDS = 180


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/")
def index():
    """Render the main Convective Nowcasting dashboard."""
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    """Avoid 404 for browser favicon requests."""
    return ("", 204)


@app.route("/api/locations")
def get_locations():
    """Return available Karnataka locations with predefined coordinates."""
    locations = []
    for city, coords in pl.KARNATAKA_CITY_COORDINATES.items():
        sub_locs = pl.KARNATAKA_SUB_LOCATIONS.get(city, [])
        locations.append({
            "name": city.capitalize(),
            "lat": coords["lat"],
            "lon": coords["lon"],
            "address": coords.get("address", f"{city.capitalize()}, Karnataka, India"),
            "sub_locations_count": len(sub_locs)
        })
    return jsonify(locations)


@app.route("/api/nowcast")
def get_nowcast():
    """
    Execute end-to-end nowcasting inference and Gemini advisory for a location.
    Query param: location (e.g. 'Puttur', 'Bangalore', 'Mangalore')
    """
    location = request.args.get("location", "Puttur").strip()
    now_ts = datetime.datetime.now().timestamp()

    # Check cache
    cache_key = location.lower()
    if cache_key in PREDICTION_CACHE:
        cached_data, timestamp = PREDICTION_CACHE[cache_key]
        if (now_ts - timestamp) < CACHE_TTL_SECONDS:
            return jsonify(cached_data)

    try:
        # 1. Fetch Real-Time Meteorological Observations & Coordinates
        weather_data = pl.fetch_weather_data_accurate(location)
        if not weather_data:
            return jsonify({"error": f"Failed to retrieve live weather observations for '{location}'"}), 502

        coord_info = pl.resolve_karnataka_coordinates(location)
        resolved_addr = weather_data.get("resolved_address") or (coord_info.get("name") if coord_info else f"{location}, Karnataka, India")
        is_ka = weather_data.get("is_karnataka", False)
        if coord_info:
            is_ka = coord_info.get("is_karnataka", is_ka)
            if not is_ka:
                resolved_addr = coord_info.get("name", resolved_addr)

        admin_region = coord_info.get("admin1", "") if coord_info else weather_data.get("admin1", "")
        country = coord_info.get("country", "") if coord_info else weather_data.get("country", "")
        lat = weather_data.get("latitude") or (coord_info.get("lat", 12.9141) if coord_info else 12.9141)
        lon = weather_data.get("longitude") or (coord_info.get("lon", 74.8560) if coord_info else 74.8560)

        region_str = f"{admin_region}, {country}" if admin_region else (country or "outside region")
        warning_msg = None
        now = datetime.datetime.now()

        if is_ka:
            # 2. Compute Domain Physics Features (Strictly for Karnataka Stations)
            temp = weather_data.get("temp") or 28.5
            dew = weather_data.get("dew") or 24.5
            humidity = weather_data.get("humidity") or 78.0
            windspeed = weather_data.get("windspeed") or 5.0
            winddir = weather_data.get("winddir") or 270.0
            cloudcover = weather_data.get("cloudcover") or 35.0
            pressure = weather_data.get("pressure") or 1002.0
            conditions = weather_data.get("conditions") or "Partially cloudy"

            dpd = round(temp - dew, 2)
            vp = round(6.112 * 2.71828 ** ((17.67 * dew) / (dew + 243.5)), 2)
            svp = round(6.112 * 2.71828 ** ((17.67 * temp) / (temp + 243.5)), 2)
            vpd = round(svp - vp, 2)
            # Physically continuous pressure tendency based on standard atmospheric baseline (1011.0 hPa)
            pressure_drop_1d = round(min(1.5, max(-3.0, (1011.0 - pressure) * 0.4)), 2)

            sample = pl.build_full_feature_dict(
                temp_c=temp,
                dew_c=dew,
                humidity=humidity,
                windspeed_kmh=windspeed,
                cloudcover=cloudcover,
                pressure_drop_1d=pressure_drop_1d,
                winddir=winddir,
                month=now.month,
                day_of_year=now.timetuple().tm_yday,
                pressure_hpa=pressure
            )

            telemetry_pack = {
                "temp": temp,
                "dew": dew,
                "dpd": dpd,
                "humidity": humidity,
                "vpd": vpd,
                "pressure": pressure,
                "pressure_drop": pressure_drop_1d,
                "windspeed": windspeed,
                "winddir": winddir,
                "cloudcover": cloudcover,
                "conditions": conditions
            }

            # Step A: Compute preliminary ML baseline
            ml_prior = pl.predict_convective_risk(MODEL, FEATURE_COLS, sample)

            # Step B: Prepare micro-zones structure
            micro_zones = []
            city_key = pl.get_city_key_if_major(location, resolved_addr)
            if city_key and city_key in pl.KARNATAKA_SUB_LOCATIONS:
                sub_list = pl.KARNATAKA_SUB_LOCATIONS.get(city_key, [])
            else:
                sub_list = [
                    {"name": f"{location} Central Market & Transit Hub", "query": location, "is_center": True},
                    {"name": f"{location} North / Highland Ridge", "query": location, "dlat": 0.09, "dlon": 0.02},
                    {"name": f"{location} South / River Basin", "query": location, "dlat": -0.09, "dlon": -0.02},
                    {"name": f"{location} East / Agro Corridor", "query": location, "dlat": 0.02, "dlon": 0.11},
                    {"name": f"{location} West / Transit Gateway", "query": location, "dlat": -0.02, "dlon": -0.11}
                ]

            zones_input_meta = []
            for idx, sub in enumerate(sub_list):
                sub_name = sub.get("name", "Zone")
                sub_q = sub.get("query", "").lower()
                is_center = sub.get("is_center", False)

                sub_coord = pl.KARNATAKA_CITY_COORDINATES.get(sub_q)
                if is_center:
                    sub_lat = lat
                    sub_lon = lon
                elif sub_coord and sub_q != city_key:
                    sub_lat = sub_coord["lat"]
                    sub_lon = sub_coord["lon"]
                elif "dlat" in sub and "dlon" in sub:
                    sub_lat = round(lat + sub["dlat"], 4)
                    sub_lon = round(lon + sub["dlon"], 4)
                else:
                    angle = (idx * (2 * 3.14159 / max(1, len(sub_list))))
                    sub_lat = round(lat + 0.08 * math.cos(angle), 4)
                    sub_lon = round(lon + 0.10 * math.sin(angle), 4)

                is_hill = any(k in sub_name.lower() for k in ["sullia", "foothill", "ridge", "peak", "chamundi", "ghats"])
                is_valley = any(k in sub_name.lower() for k in ["valley", "basin", "river", "lowland"])
                z_temp = round(temp + (0.5 if is_hill else (-0.4 if is_valley else 0.0)), 1)
                z_cloud = min(100.0, max(0.0, cloudcover + (14.0 if is_hill else (-8.0 if is_valley else 0.0))))
                z_hum = min(100.0, max(0.0, humidity + (5.0 if is_hill else (-3.0 if is_valley else 0.0))))

                zones_input_meta.append({
                    "name": sub_name,
                    "temp": z_temp,
                    "dew": dew,
                    "cloudcover": z_cloud,
                    "humidity": z_hum,
                    "lat": sub_lat,
                    "lon": sub_lon,
                    "is_center": is_center
                })

            # Step C: Call Hybrid Engine (Gemini AI + 27-Year Karnataka Dataset)
            ai_prediction = predict_weather_with_gemini_and_dataset(
                location=resolved_addr,
                weather_data=weather_data,
                ml_prior=ml_prior,
                sub_locations=zones_input_meta
            )

            # Extract calibrated prediction outputs
            convective_prob = ai_prediction.get("convective_probability", ml_prior.get("convective_probability", 25.0))
            alert_code = ai_prediction.get("alert_code", "GREEN")
            risk_level = ai_prediction.get("risk_level", "FAIR WEATHER / LOW RISK")
            weather_condition = ai_prediction.get("weather_condition", conditions)
            telemetry_pack["conditions"] = weather_condition

            prediction = {
                "convective_probability": convective_prob,
                "binary_prediction": 1 if convective_prob >= 50.0 else 0,
                "risk_level": risk_level,
                "alert_code": alert_code,
                "weather_condition": weather_condition,
                "model_source": ai_prediction.get("model", "Gemini AI + Karnataka Dataset Ensemble"),
                "is_available": True
            }

            # Synchronize 3-step timeline progression
            timeline = ai_prediction.get("timeline", [])
            if not timeline:
                timeline = pl.compute_nowcast_timeline(weather_data, MODEL, FEATURE_COLS)

            # Synchronize micro-zones
            ai_zones = {z.get("name"): z for z in ai_prediction.get("micro_zones", [])}
            for meta in zones_input_meta:
                z_name = meta["name"]
                matched = ai_zones.get(z_name)
                z_prob = matched["probability"] if matched else convective_prob
                z_code = matched["alert_code"] if matched else alert_code
                z_risk = matched["risk_level"] if matched else risk_level

                micro_zones.append({
                    "name": z_name,
                    "temp": meta["temp"],
                    "dew": meta["dew"],
                    "cloudcover": meta["cloudcover"],
                    "humidity": meta["humidity"],
                    "probability": z_prob,
                    "risk_level": z_risk,
                    "alert_code": z_code,
                    "lat": meta["lat"],
                    "lon": meta["lon"],
                    "is_center": meta["is_center"]
                })

            gemini_advisory = {
                "status": ai_prediction.get("status", "success"),
                "model": ai_prediction.get("model", "Gemini AI + Karnataka Dataset Ensemble"),
                "synoptic_bulletin": ai_prediction.get("synoptic_bulletin", ""),
                "ai_risk_assessment": risk_level,
                "agriculture_advisory": ai_prediction.get("agriculture_advisory", ""),
                "travel_safety_advisory": ai_prediction.get("travel_safety_advisory", ""),
                "aviation_outdoor_warning": ai_prediction.get("aviation_outdoor_warning", "")
            }

        else:
            warning_msg = f"Warning: '{location}' is located in {region_str}, outside Karnataka state boundary! AeroCast AI convective models and S-band Doppler radar are strictly calibrated for Karnataka (11.5°N - 18.6°N, 74.0°E - 78.6°E). Weather display and convective nowcast predictions are disabled for out-of-state locations."
            
            # Hide/disable weather telemetry for places outside Karnataka
            telemetry_pack = {
                "temp": None,
                "dew": None,
                "dpd": None,
                "humidity": None,
                "vpd": None,
                "pressure": None,
                "pressure_drop": None,
                "windspeed": None,
                "winddir": None,
                "cloudcover": None,
                "conditions": "Prediction Disabled (Outside Karnataka)"
            }
            
            prediction = {
                "convective_probability": None,
                "binary_prediction": None,
                "risk_level": "PREDICTION DISABLED (Outside Karnataka Boundary)",
                "alert_code": "DISABLED",
                "weather_condition": "Prediction Disabled (Outside Karnataka)",
                "model_source": "Disabled (Out-of-Region)",
                "is_available": False
            }
            
            timeline = [
                {"time_label": "+30m Projection", "minute_offset": 30, "probability": None, "alert_code": "DISABLED", "risk_level": "Disabled", "rain_rate_mmh": 0.0},
                {"time_label": "+60m Projection", "minute_offset": 60, "probability": None, "alert_code": "DISABLED", "risk_level": "Disabled", "rain_rate_mmh": 0.0},
                {"time_label": "+90m Projection", "minute_offset": 90, "probability": None, "alert_code": "DISABLED", "risk_level": "Disabled", "rain_rate_mmh": 0.0}
            ]
            micro_zones = []
            gemini_advisory = {
                "status": "out_of_bounds",
                "model": "AeroCast AI (Karnataka Boundary Lock)",
                "synoptic_bulletin": f"Station '{location}' ({resolved_addr}) is located outside Karnataka state boundary. AeroCast AI Doppler radar and thermodynamic convective nowcasting models are strictly calibrated for Karnataka & Western Ghats atmospheric physics. Convective storm prediction and weather display are disabled for this station.",
                "agriculture_advisory": "Convective nowcasting models are not calibrated for agricultural zones outside Karnataka.",
                "travel_safety_advisory": f"Refer to state meteorological departments for weather conditions in {resolved_addr}.",
                "aviation_outdoor_warning": "Nowcast convective radar grid is inactive for out-of-state sectors."
            }

        response_data = {
            "location": location,
            "resolved_address": resolved_addr,
            "latitude": lat,
            "longitude": lon,
            "is_karnataka": is_ka,
            "warning": warning_msg,
            "timestamp": now.strftime("%I:%M:%S %p IST"),
            "telemetry": telemetry_pack,
            "prediction": prediction,
            "timeline": timeline,
            "micro_zones": micro_zones,
            "gemini_advisory": gemini_advisory
        }

        # Store in cache
        PREDICTION_CACHE[cache_key] = (response_data, now_ts)
        return jsonify(response_data)

    except Exception as e:
        print(f"[ERROR] /api/nowcast failed: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" ⚡ AeroCast AI — Karnataka Convective Weather Nowcasting Server")
    print(" Model: Soft Voting Ensemble (LightGBM + XGBoost + HistGradientBoosting)")
    print(" AI Advisory: Google Gemini API (gemini-flash-lite / gemini-3.5-flash-lite)")
    print(" Dashboard URL: http://127.0.0.1:5000")
    print("=" * 70 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
