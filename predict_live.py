"""
Live Convective Weather & Thunderstorm Prediction Engine
========================================================
Project: AI-Based Thunderstorm & Convective Weather Nowcasting System
Location Domain: Karnataka State (Bangalore Observatory / Coastal & Inland Microclimates)

Description:
    Performs live inference using the trained best model artifact:
    - Fixed, canonical coordinate lookup for Karnataka cities (Bangalore -> Bengaluru, KA, India; Shimoga -> Shivamogga, KA, India).
    - Prevents mis-geocoding to foreign regions (Pakistan, Japan, etc.).
    - High-accuracy real-time meteorological weather fetcher (Open-Meteo + Visual Crossing fallback).
    - Precise WMO weather condition resolution (Clear, Mainly Clear, Partly Cloudy, Overcast, Drizzle, Rain, Thunderstorm).
    - Restricts queries to Karnataka locations (validates state boundary).
    - Performs sub-area / neighborhood-level predictions for major Karnataka cities (e.g. Mangalore, Bangalore, Mysore, Udupi, Hubli, Belgaum).
"""

import sys
import os
import json
import joblib
import argparse
import datetime
import urllib.request
import urllib.parse
import numpy as np
import pandas as pd
from pathlib import Path

from config import MODELS_DIR, VISUAL_CROSSING_API_KEY

# Ensure UTF-8 output encoding for Windows command line interfaces
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# -----------------------------------------------------------------------------
# WMO WEATHER CODES & ACCURATE WEATHER DESCRIPTIONS
# -----------------------------------------------------------------------------

WMO_WEATHER_DESCRIPTIONS = {
    0: 'Clear Sky',
    1: 'Mainly Clear',
    2: 'Partly Cloudy',
    3: 'Overcast Clouds',
    45: 'Fog & Mist',
    48: 'Depositing Rime Fog',
    51: 'Light Drizzle',
    53: 'Moderate Drizzle',
    55: 'Dense Drizzle',
    61: 'Slight Rain',
    63: 'Moderate Rain',
    65: 'Heavy Rain',
    80: 'Rain Showers',
    81: 'Moderate Rain Showers',
    82: 'Violent Rain Showers',
    95: 'Thunderstorm',
    96: 'Thunderstorm with Hail',
    99: 'Severe Thunderstorm'
}


def map_dataset_weather_condition(
    cloudcover: float,
    precip_mm: float = 0.0,
    wcode: int = None,
    raw_condition: str = None
) -> str:
    """
    Map weather condition using exact Visual Crossing dataset categories from karnataka_dataset.xlsx:
    - 'Clear' (cloudcover <= 20%)
    - 'Partially cloudy' (20% < cloudcover <= 75%)
    - 'Overcast' (cloudcover > 75%)
    - 'Rain, Partially cloudy' (precip > 0.1 mm & cloudcover <= 75%)
    - 'Rain, Overcast' (precip > 0.1 mm & cloudcover > 75%)
    - 'Thunderstorm' (WMO storm codes 95, 96, 99)
    """
    if wcode in [95, 96, 99] or (raw_condition and "thunderstorm" in raw_condition.lower()):
        return "Thunderstorm"

    if precip_mm > 0.1 or (raw_condition and "rain" in raw_condition.lower() and precip_mm > 0.1):
        if cloudcover > 75.0:
            return "Rain, Overcast"
        else:
            return "Rain, Partially cloudy"

    if cloudcover <= 20.0:
        return "Clear"
    elif cloudcover <= 75.0:
        return "Partially cloudy"
    else:
        return "Overcast"


# -----------------------------------------------------------------------------
# KARNATAKA GEOGRAPHIC BOUNDARY & SUB-LOCATION DEFINITIONS
# -----------------------------------------------------------------------------

KARNATAKA_CITY_COORDINATES = {
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru (Bangalore), Karnataka, India"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru (Bangalore), Karnataka, India"},
    "mangalore": {"lat": 12.9141, "lon": 74.8560, "name": "Mangaluru (Mangalore), Karnataka, India"},
    "mangaluru": {"lat": 12.9141, "lon": 74.8560, "name": "Mangaluru (Mangalore), Karnataka, India"},
    "shimoga": {"lat": 13.9299, "lon": 75.5681, "name": "Shivamogga (Shimoga), Karnataka, India"},
    "shivamogga": {"lat": 13.9299, "lon": 75.5681, "name": "Shivamogga (Shimoga), Karnataka, India"},
    "mysore": {"lat": 12.2958, "lon": 76.6394, "name": "Mysuru (Mysore), Karnataka, India"},
    "mysuru": {"lat": 12.2958, "lon": 76.6394, "name": "Mysuru (Mysore), Karnataka, India"},
    "udupi": {"lat": 13.3409, "lon": 74.7421, "name": "Udupi, Karnataka, India"},
    "hubli": {"lat": 15.3647, "lon": 75.1240, "name": "Hubballi (Hubli), Karnataka, India"},
    "hubballi": {"lat": 15.3647, "lon": 75.1240, "name": "Hubballi (Hubli), Karnataka, India"},
    "belgaum": {"lat": 15.8497, "lon": 74.4977, "name": "Belagavi (Belgaum), Karnataka, India"},
    "belagavi": {"lat": 15.8497, "lon": 74.4977, "name": "Belagavi (Belgaum), Karnataka, India"},
    "karwar": {"lat": 14.8094, "lon": 74.1303, "name": "Karwar, Karnataka, India"},
    "chikmagalur": {"lat": 13.3161, "lon": 75.7720, "name": "Chikkamagaluru (Chikmagalur), Karnataka, India"},
    "chikkamagaluru": {"lat": 13.3161, "lon": 75.7720, "name": "Chikkamagaluru (Chikmagalur), Karnataka, India"},
    "coorg": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri (Coorg), Karnataka, India"},
    "kodagu": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri (Coorg), Karnataka, India"},
    "madikeri": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri (Coorg), Karnataka, India"},
    "surathkal": {"lat": 12.9807, "lon": 74.8031, "name": "Surathkal, Mangalore, Karnataka, India"},
    "panambur": {"lat": 12.9463, "lon": 74.8055, "name": "Panambur, Mangalore, Karnataka, India"},
    "bajpe": {"lat": 12.9803, "lon": 74.8832, "name": "Bajpe (Airport Zone), Mangalore, Karnataka, India"},
    "kadri": {"lat": 12.8797, "lon": 74.8584, "name": "Kadri Hills, Mangalore, Karnataka, India"},
    "hampankatta": {"lat": 12.8698, "lon": 74.8431, "name": "Hampankatta, Mangalore, Karnataka, India"},
    "ullal": {"lat": 12.8080, "lon": 74.8532, "name": "Ullal Coast, Mangalore, Karnataka, India"},
    "kankanady": {"lat": 12.8672, "lon": 74.8622, "name": "Bendoorwell / Kankanady, Mangalore, Karnataka, India"},
    "whitefield": {"lat": 12.9698, "lon": 77.7500, "name": "Whitefield, Bangalore, Karnataka, India"},
    "electronic city": {"lat": 12.8399, "lon": 77.6770, "name": "Electronic City, Bangalore, Karnataka, India"},
    "yelahanka": {"lat": 13.1007, "lon": 77.5963, "name": "Yelahanka, Bangalore, Karnataka, India"},
    "indiranagar": {"lat": 12.9784, "lon": 77.6408, "name": "Indiranagar (HAL Zone), Bangalore, Karnataka, India"},
    "kengeri": {"lat": 12.9081, "lon": 77.4816, "name": "Kengeri, Bangalore, Karnataka, India"},
    "koramangala": {"lat": 12.9352, "lon": 77.6245, "name": "Koramangala, Bangalore, Karnataka, India"},
    "peenya": {"lat": 13.0285, "lon": 77.5197, "name": "Peenya, Bangalore, Karnataka, India"},
    "chamundi hill": {"lat": 12.2743, "lon": 76.6706, "name": "Chamundi Hill, Mysore, Karnataka, India"},
    "hebbal": {"lat": 12.3556, "lon": 76.6111, "name": "Hebbal Industrial Area, Mysore, Karnataka, India"},
    "jayalakshmipuram": {"lat": 12.3168, "lon": 76.6262, "name": "Jayalakshmipuram, Mysore, Karnataka, India"},
    "vijayanagar": {"lat": 12.3364, "lon": 76.6105, "name": "Vijayanagar, Mysore, Karnataka, India"},
    "nanjangud": {"lat": 12.1189, "lon": 76.6806, "name": "Nanjangud, Mysore, Karnataka, India"},
    "manipal": {"lat": 13.3525, "lon": 74.7869, "name": "Manipal, Udupi, Karnataka, India"},
    "malpe": {"lat": 13.3582, "lon": 74.7042, "name": "Malpe Coast & Harbor, Udupi, Karnataka, India"},
    "kaup": {"lat": 13.2248, "lon": 74.7431, "name": "Kaup Lighthouse, Udupi, Karnataka, India"},
    "dharwad": {"lat": 15.4589, "lon": 75.0078, "name": "Dharwad City, Karnataka, India"},
    "unkal": {"lat": 15.3857, "lon": 75.1292, "name": "Unkal Lake Zone, Hubli, Karnataka, India"},
    "vidyanagar": {"lat": 15.3670, "lon": 75.1280, "name": "Vidyanagar, Hubli, Karnataka, India"},
    "sambra": {"lat": 15.8593, "lon": 74.6183, "name": "Sambra Airport Zone, Belgaum, Karnataka, India"},
    "tilakwadi": {"lat": 15.8368, "lon": 74.5029, "name": "Tilakwadi, Belgaum, Karnataka, India"},
    "khanapur": {"lat": 15.6372, "lon": 74.5161, "name": "Khanapur Ghats, Belgaum, Karnataka, India"},
    "bhadravathi": {"lat": 13.8413, "lon": 75.7032, "name": "Bhadravathi, Shimoga, Karnataka, India"},
    "jog falls": {"lat": 14.2284, "lon": 74.8122, "name": "Jog Falls, Shimoga, Karnataka, India"},
    "gokarna": {"lat": 14.5435, "lon": 74.3188, "name": "Gokarna Coast, Uttara Kannada, Karnataka, India"},
    "sirsi": {"lat": 14.6195, "lon": 74.8354, "name": "Sirsi Ghats, Uttara Kannada, Karnataka, India"},
    "dandeli": {"lat": 15.2361, "lon": 74.6173, "name": "Dandeli Forest, Uttara Kannada, Karnataka, India"},
    "mullayanagiri": {"lat": 13.3908, "lon": 75.7214, "name": "Mullayanagiri Peak, Chikmagalur, Karnataka, India"},
    "mudigere": {"lat": 13.1364, "lon": 75.6385, "name": "Mudigere Estate Belt, Chikmagalur, Karnataka, India"},
    "kushalnagar": {"lat": 12.4565, "lon": 75.9642, "name": "Kushalnagar, Coorg, Karnataka, India"},
    "gonikoppal": {"lat": 12.1818, "lon": 75.8943, "name": "Gonikoppal, South Coorg, Karnataka, India"},
    "puttur": {"lat": 12.7667, "lon": 75.2016, "name": "Puttur, Dakshina Kannada, Karnataka, India"},
    "vittla": {"lat": 12.7674, "lon": 75.1012, "name": "Vitla (Vittla), Dakshina Kannada, Karnataka, India"},
    "vitla": {"lat": 12.7674, "lon": 75.1012, "name": "Vitla (Vittla), Dakshina Kannada, Karnataka, India"},
    "sullia": {"lat": 12.5606, "lon": 75.3905, "name": "Sullia, Dakshina Kannada, Karnataka, India"}
}

KARNATAKA_SUB_LOCATIONS = {
    "mangalore": [
        {"name": "Surathkal (NITK Coastal Belt)", "query": "Surathkal"},
        {"name": "Panambur Port & Beach", "query": "Panambur"},
        {"name": "Bajpe (Mangalore Airport Area)", "query": "Bajpe"},
        {"name": "Kadri Hills & Park Zone", "query": "Kadri"},
        {"name": "Hampankatta (City Centre)", "query": "Hampankatta"},
        {"name": "Ullal Coastal Zone", "query": "Ullal"},
        {"name": "Bendoorwell & Kankanady", "query": "Kankanady"}
    ],
    "bangalore": [
        {"name": "HAL Observatory & Indiranagar", "query": "Indiranagar"},
        {"name": "Electronic City (South IT Hub)", "query": "Electronic City"},
        {"name": "Whitefield (East Tech Corridor)", "query": "Whitefield"},
        {"name": "Yelahanka (North Bengaluru)", "query": "Yelahanka"},
        {"name": "Kengeri & Mysore Road", "query": "Kengeri"},
        {"name": "Koramangala & HSR Layout", "query": "Koramangala"},
        {"name": "Peenya Industrial Area", "query": "Peenya"}
    ],
    "mysore": [
        {"name": "Chamundi Hill & Palace Zone", "query": "Chamundi Hill"},
        {"name": "Hebbal Industrial Belt", "query": "Hebbal"},
        {"name": "Jayalakshmipuram & University", "query": "Jayalakshmipuram"},
        {"name": "Vijayanagar & Hootagalli", "query": "Vijayanagar"},
        {"name": "Nanjangud Industrial Area", "query": "Nanjangud"}
    ],
    "udupi": [
        {"name": "Manipal University Hill", "query": "Manipal"},
        {"name": "Malpe Beach & Fishing Harbor", "query": "Malpe"},
        {"name": "Udupi Town & Temple Square", "query": "Udupi"},
        {"name": "Kaup Lighthouse & Coast", "query": "Kaup"}
    ],
    "hubli": [
        {"name": "Hubli Airport & Gokul Road", "query": "Hubli Airport"},
        {"name": "Vidyanagar & BVB Campus", "query": "Vidyanagar"},
        {"name": "Unkal Lake & North Hubli", "query": "Unkal"},
        {"name": "Dharwad City Centre", "query": "Dharwad"}
    ],
    "belgaum": [
        {"name": "Belagavi City & Fort Zone", "query": "Belgaum"},
        {"name": "Sambra Airport Area", "query": "Sambra"},
        {"name": "Tilakwadi", "query": "Tilakwadi"},
        {"name": "Khanapur Western Ghats Border", "query": "Khanapur"}
    ],
    "shimoga": [
        {"name": "Shivamogga City Centre", "query": "Shimoga"},
        {"name": "Bhadravathi Industrial Zone", "query": "Bhadravathi"},
        {"name": "Jog Falls & Ghats Crest", "query": "Jog Falls"}
    ],
    "karwar": [
        {"name": "Karwar Bay & Port Zone", "query": "Karwar"},
        {"name": "Gokarna Beach Belt", "query": "Gokarna"},
        {"name": "Sirsi Ghats & Forest Region", "query": "Sirsi"},
        {"name": "Dandeli Rainforest Belt", "query": "Dandeli"}
    ],
    "chikmagalur": [
        {"name": "Mullayanagiri Peak", "query": "Mullayanagiri"},
        {"name": "Chikmagalur Town Centre", "query": "Chikmagalur"},
        {"name": "Mudigere Coffee Estate Belt", "query": "Mudigere"}
    ],
    "coorg": [
        {"name": "Madikeri Fort & Town", "query": "Madikeri"},
        {"name": "Kushalnagar & Cauvery Basin", "query": "Kushalnagar"},
        {"name": "Gonikoppal & South Coorg", "query": "Gonikoppal"}
    ],
    "puttur": [
        {"name": "Puttur Town Centre & Bus Stand", "query": "Puttur"},
        {"name": "Darbe & Bedrala Zone", "query": "Puttur"},
        {"name": "Nehru Nagar & Kabaka Zone", "query": "Puttur"},
        {"name": "Vitla (Vittla) Town Belt", "query": "vittla"},
        {"name": "Sullia Foothills Belt", "query": "sullia"}
    ]
}

CITY_ALIASES = {
    "mangaluru": "mangalore",
    "bengaluru": "bangalore",
    "mysuru": "mysore",
    "shivamogga": "shimoga",
    "belagavi": "belgaum",
    "hubballi": "hubli",
    "kodagu": "coorg",
    "chikkamagaluru": "chikmagalur"
}


def is_location_in_karnataka(location_query: str, resolved_address: str) -> bool:
    """Check if requested location or resolved address belongs to Karnataka state."""
    loc_lower = location_query.lower().strip()
    res_lower = resolved_address.lower().strip()

    # Reject foreign countries or out-of-state cities/regions explicitly
    rejected = [
        "pakistan", "japan", "maharashtra", "kerala", "tamil nadu", "andhra pradesh", "telangana",
        "united states", "united kingdom", "london", "mumbai", "delhi", "chennai", "kolkata", "hyderabad",
        "new york", "dubai", "singapore"
    ]
    for r in rejected:
        if r in loc_lower or r in res_lower:
            return False

    # Check if input matches known Karnataka city key directly
    for k in KARNATAKA_CITY_COORDINATES.keys():
        if k in loc_lower:
            return True

    if "karnataka" in res_lower or "karnataka" in loc_lower or "ka, india" in res_lower:
        return True

    return False


def get_city_key_if_major(location_query: str, resolved_address: str) -> str:
    """Identify if input location matches a major Karnataka city with sub-locations."""
    loc_lower = location_query.lower().strip()
    res_lower = resolved_address.lower().strip()
    combined = f"{loc_lower} {res_lower}"

    for raw_alias, target_key in CITY_ALIASES.items():
        if raw_alias in combined:
            return target_key

    for key in KARNATAKA_SUB_LOCATIONS.keys():
        if key in combined:
            return key

    return ""


# -----------------------------------------------------------------------------
# HIGH-ACCURACY DUAL-SOURCE WEATHER FETCHER
# -----------------------------------------------------------------------------

def resolve_karnataka_coordinates(location: str) -> dict:
    """
    Resolve coordinates specifically for Karnataka locations, preventing
    mis-geocoding to foreign regions (e.g. Pakistan or Japan).
    """
    loc_key = location.lower().strip()

    # 1. Exact match in pre-computed Karnataka database
    if loc_key in KARNATAKA_CITY_COORDINATES:
        return KARNATAKA_CITY_COORDINATES[loc_key]

    # 2. Substring match in pre-computed database
    for k, info in KARNATAKA_CITY_COORDINATES.items():
        if k in loc_key or loc_key in k:
            return info

    # 3. Dynamic geocoding with strict Karnataka, India search
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    gurl = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location + ' Karnataka India')}&count=5&language=en&format=json"
    
    try:
        greq = urllib.request.Request(gurl, headers=headers)
        gresp = urllib.request.urlopen(greq, timeout=6)
        gdata = json.loads(gresp.read().decode('utf-8'))
        results = gdata.get('results', [])

        for r in results:
            country = r.get('country', '').lower()
            admin1 = r.get('admin1', '').lower()
            if country == 'india' and ('karnataka' in admin1 or admin1 == ''):
                return {
                    "lat": float(r['latitude']),
                    "lon": float(r['longitude']),
                    "name": f"{r.get('name')}, {r.get('admin1', 'Karnataka')}, India"
                }
    except Exception:
        pass

    return None


def fetch_weather_data_accurate(location: str) -> dict:
    """
    Fetch pinpoint, real-time meteorological observations for Karnataka locations.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    coord_info = resolve_karnataka_coordinates(location)

    if coord_info:
        lat, lon = coord_info["lat"], coord_info["lon"]
        resolved_name = coord_info["name"]

        try:
            wurl = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,dew_point_2m,surface_pressure,wind_speed_10m,wind_direction_10m,cloud_cover,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,surface_pressure,wind_speed_10m,wind_direction_10m,cloud_cover,weather_code,precipitation&forecast_hours=6"
            wreq = urllib.request.Request(wurl, headers=headers)
            wresp = urllib.request.urlopen(wreq, timeout=6)
            resp_data = json.loads(wresp.read().decode('utf-8'))
            wdata = resp_data['current']
            hourly_data = resp_data.get('hourly', {})

            wcode = wdata.get('weather_code', 0)
            precip = float(wdata.get('precipitation', 0.0))
            raw_cond = WMO_WEATHER_DESCRIPTIONS.get(wcode, f"Weather Code {wcode}")
            cond_text = map_dataset_weather_condition(float(wdata['cloud_cover']), precip, wcode, raw_cond)

            return {
                "resolved_address": resolved_name,
                "temp": float(wdata['temperature_2m']),
                "dew": float(wdata['dew_point_2m']),
                "humidity": float(wdata['relative_humidity_2m']),
                "windspeed": float(wdata['wind_speed_10m']),
                "winddir": float(wdata['wind_direction_10m']),
                "cloudcover": float(wdata['cloud_cover']),
                "pressure": float(wdata['surface_pressure']),
                "conditions": cond_text,
                "hourly": hourly_data
            }
        except Exception:
            pass

    # Fallback to Visual Crossing API with explicit Karnataka suffix
    if VISUAL_CROSSING_API_KEY:
        try:
            vurl = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{urllib.parse.quote(location + ', Karnataka, India')}?unitGroup=metric&key={VISUAL_CROSSING_API_KEY}&contentType=json"
            vreq = urllib.request.Request(vurl, headers=headers)
            vresp = urllib.request.urlopen(vreq, timeout=6)
            vdata = json.loads(vresp.read().decode('utf-8'))

            resolved_name = vdata.get("resolvedAddress", f"{location}, Karnataka, India")
            curr = vdata.get("currentConditions", {})

            raw_cond = curr.get("conditions", "Partly Cloudy")
            precip = float(curr.get("precip") or 0.0)
            cloud_val = float(curr.get("cloudcover") or 50.0)
            temp_val = float(curr.get("temp") or 30.0)
            cond_text = map_dataset_weather_condition(cloud_val, precip, raw_condition=raw_cond)

            return {
                "resolved_address": resolved_name,
                "temp": temp_val,
                "dew": float(curr.get("dew", 20.0)),
                "humidity": float(curr.get("humidity", 70.0)),
                "windspeed": float(curr.get("windspeed", 15.0)),
                "winddir": float(curr.get("winddir", 180.0)),
                "cloudcover": cloud_val,
                "pressure": float(curr.get("pressure", 1012.0)),
                "conditions": cond_text
            }
        except Exception:
            pass

    raise ValueError(f"Could not retrieve live weather observations for '{location}'. Please check connection.")


# -----------------------------------------------------------------------------
# FEATURE PIPELINE & INFERENCE LOGIC
# -----------------------------------------------------------------------------

def load_model_and_schema():
    """Load serialized model and feature names."""
    model_path = MODELS_DIR / "best_convective_model.joblib"
    schema_path = MODELS_DIR / "feature_columns.json"

    if not model_path.exists() or not schema_path.exists():
        raise FileNotFoundError(
            "Trained model artifacts not found. Run 'python train_models.py' first."
        )

    model = joblib.load(model_path)
    with open(schema_path, "r") as f:
        feature_cols = json.load(f)

    return model, feature_cols


def build_full_feature_dict(
    temp_c: float,
    dew_c: float,
    humidity: float,
    windspeed_kmh: float,
    cloudcover: float,
    pressure_drop_1d: float = 0.0,
    winddir: float = 180.0,
    windgust_kmh: float = None,
    month: int = None,
    day_of_year: int = None,
    pressure_hpa: float = 1013.25,
    precip_accum_3d: float = None
) -> dict:
    """
    Construct a complete, fully synchronized 54-feature dictionary
    for live nowcasting inference.
    """
    if month is None or day_of_year is None:
        now = datetime.datetime.now()
        month = now.month if month is None else month
        day_of_year = now.timetuple().tm_yday if day_of_year is None else day_of_year

    if windgust_kmh is None:
        windgust_kmh = windspeed_kmh * 1.25 if windspeed_kmh > 15 else windspeed_kmh

    dpd = round(temp_c - dew_c, 2)
    vp = round(6.112 * np.exp((17.67 * dew_c) / (dew_c + 243.5)), 2)
    svp = round(6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5)), 2)
    vpd = round(svp - vp, 2)

    windspeed_ms = round(windspeed_kmh / 3.6, 2)
    wind_rad = np.radians(winddir)
    wind_u_kmh = round(-windspeed_kmh * np.sin(wind_rad), 2)
    wind_v_kmh = round(-windspeed_kmh * np.cos(wind_rad), 2)

    sin_doy = round(float(np.sin(2 * np.pi * day_of_year / 365.25)), 4)
    cos_doy = round(float(np.cos(2 * np.pi * day_of_year / 365.25)), 4)
    sin_m = round(float(np.sin(2 * np.pi * month / 12.0)), 4)
    cos_m = round(float(np.cos(2 * np.pi * month / 12.0)), 4)

    if precip_accum_3d is None:
        precip_accum_3d = 0.0

    precip_mm_lag1 = precip_accum_3d / 3.0 if precip_accum_3d > 0 else 0.0

    sample = {
        "humidity": humidity,
        "winddir": winddir,
        "cloudcover": cloudcover,
        "visibility": 10.0,
        "moonphase": 0.5,
        "temp_c": temp_c,
        "tempmax_c": temp_c + 2.5,
        "tempmin_c": max(temp_c - 7.5, dew_c),
        "feelslike_c": temp_c + (0.2 * vp) - (0.1 * windspeed_ms),
        "feelslikemax_c": temp_c + 3.0,
        "feelslikemin_c": max(temp_c - 7.5, dew_c),
        "dew_c": dew_c,
        "windspeed_kmh": windspeed_kmh,
        "windspeed_ms": windspeed_ms,
        "windgust_kmh": windgust_kmh,
        "has_recorded_gust": 1 if windgust_kmh > windspeed_kmh else 0,
        "dew_point_depression_c": dpd,
        "diurnal_temp_range_c": 10.0,
        "thermal_discomfort_delta_c": round(vp * 0.1, 2),
        "vapor_pressure_hpa": vp,
        "sat_vapor_pressure_hpa": svp,
        "vapor_pressure_deficit_hpa": vpd,
        "wind_u_kmh": wind_u_kmh,
        "wind_v_kmh": wind_v_kmh,
        "sin_day_of_year": sin_doy,
        "cos_day_of_year": cos_doy,
        "sin_month": sin_m,
        "cos_month": cos_m,
        "day_of_year": day_of_year,
        "month": month,
        "pressure_interpolated": pressure_hpa,
        "pressure_drop_1d": pressure_drop_1d,
        "temp_c_lag1": temp_c,
        "temp_c_lag2": temp_c,
        "temp_c_lag3": temp_c,
        "dew_c_lag1": dew_c,
        "dew_c_lag2": dew_c,
        "dew_c_lag3": dew_c,
        "humidity_lag1": humidity,
        "humidity_lag2": humidity,
        "humidity_lag3": humidity,
        "precip_mm_lag1": precip_mm_lag1,
        "precip_mm_lag2": precip_mm_lag1,
        "precip_mm_lag3": 0.0,
        "cloudcover_lag1": cloudcover,
        "cloudcover_lag2": cloudcover,
        "cloudcover_lag3": cloudcover,
        "pressure_interpolated_lag1": pressure_hpa - pressure_drop_1d,
        "pressure_interpolated_lag2": pressure_hpa - pressure_drop_1d,
        "pressure_interpolated_lag3": pressure_hpa - pressure_drop_1d,
        "precip_accum_3d": precip_accum_3d,
        "precip_accum_7d": precip_accum_3d * 1.5,
        "humidity_mean_3d": humidity,
        "temp_max_3d": temp_c + 2.5
    }
    return sample


def predict_convective_risk(model, feature_cols, input_features: dict) -> dict:
    """Run inference on input meteorological dictionary."""
    df_input = pd.DataFrame([input_features])

    for col in feature_cols:
        if col not in df_input.columns:
            df_input[col] = 0.0

    X_infer = df_input[feature_cols].fillna(0.0)

    prob = model.predict_proba(X_infer)[0, 1]
    prediction = int(prob >= 0.5)

    if prob < 0.25:
        risk_level = "LOW (Fair Weather / Minimal Convective Potential)"
        color_alert = "GREEN"
    elif prob < 0.50:
        risk_level = "MODERATE (Scattered Clouds / Low Probability)"
        color_alert = "YELLOW"
    elif prob < 0.75:
        risk_level = "HIGH (Strong Convective Cloud Formation / Rain Expected)"
        color_alert = "ORANGE"
    else:
        risk_level = "CRITICAL (Severe Thunderstorm / Heavy Rain Alert)"
        color_alert = "RED"

    return {
        "convective_probability": round(float(prob) * 100, 2),
        "binary_prediction": prediction,
        "risk_level": risk_level,
        "alert_code": color_alert
    }


def extract_pressure_drop_1d(data: dict) -> float:
    """Extract real barometric pressure drop (tendency) from hourly observation data."""
    if not data:
        return 0.0
    hourly = data.get("hourly", {})
    p_list = hourly.get("surface_pressure", [])
    if len(p_list) >= 2:
        return round(float(p_list[-1]) - float(p_list[0]), 2)
    return 0.0


def compute_nowcast_timeline(data: dict, model, feature_cols) -> list:
    """
    Computes short-term nowcast predictions for +30m, +60m, and +90m time horizons.
    """
    hourly = data.get("hourly")
    if not hourly or "temperature_2m" not in hourly or len(hourly.get("temperature_2m", [])) < 2:
        return []

    h_temps = hourly['temperature_2m']
    h_hums = hourly['relative_humidity_2m']
    h_dews = hourly['dew_point_2m']
    h_clouds = hourly['cloud_cover']
    h_winds = hourly['wind_speed_10m']
    h_dirs = hourly['wind_direction_10m']
    h_press = hourly['surface_pressure']
    h_codes = hourly['weather_code']

    p_drop = extract_pressure_drop_1d(data)
    now = datetime.datetime.now()

    offsets = [
        ("+30 Mins Later", 30, 0.5),
        ("+60 Mins Later", 60, 1.0),
        ("+90 Mins Later", 90, 1.5)
    ]

    timeline = []

    for label, mins, frac in offsets:
        target_time = now + datetime.timedelta(minutes=mins)
        idx1 = int(frac)
        idx2 = min(idx1 + 1, len(h_temps) - 1)
        w = frac - idx1

        t_val = round((1 - w) * h_temps[idx1] + w * h_temps[idx2], 1)
        d_val = round((1 - w) * h_dews[idx1] + w * h_dews[idx2], 1)
        h_val = round((1 - w) * h_hums[idx1] + w * h_hums[idx2], 1)
        c_val = round((1 - w) * h_clouds[idx1] + w * h_clouds[idx2], 1)
        w_val = round((1 - w) * h_winds[idx1] + w * h_winds[idx2], 1)
        wdir_val = round((1 - w) * h_dirs[idx1] + w * h_dirs[idx2], 1)
        p_val = round((1 - w) * h_press[idx1] + w * h_press[idx2], 1)
        wcode = h_codes[idx2] if w > 0.5 else h_codes[idx1]

        sample = build_full_feature_dict(
            temp_c=t_val,
            dew_c=d_val,
            humidity=h_val,
            windspeed_kmh=w_val,
            cloudcover=c_val,
            winddir=wdir_val,
            pressure_drop_1d=p_drop,
            month=target_time.month,
            day_of_year=target_time.timetuple().tm_yday,
            pressure_hpa=p_val
        )
        res = predict_convective_risk(model, feature_cols, sample)
        raw_cond = WMO_WEATHER_DESCRIPTIONS.get(wcode, f"Weather Code {wcode}")
        cond_text = map_dataset_weather_condition(c_val, 0.0, wcode, raw_cond)

        timeline.append({
            "label": label,
            "time_str": target_time.strftime("%I:%M %p"),
            "temp": t_val,
            "dew": d_val,
            "humidity": h_val,
            "cloudcover": c_val,
            "windspeed": w_val,
            "conditions": cond_text,
            "probability": res["convective_probability"],
            "risk_level": res["risk_level"],
            "alert_code": res["alert_code"]
        })

    return timeline


def fetch_live_weather_and_predict(location: str):
    """
    Fetch current live weather observations for a location in Karnataka,
    validate state boundary, and provide sub-area predictions for major cities.
    """
    print("=" * 75)
    print(f" FETCHING LIVE WEATHER & CONVECTIVE NOWCASTING FOR LOCATION: '{location}'")
    print("=" * 75)

    try:
        data = fetch_weather_data_accurate(location)
    except Exception as e:
        print(f"[ERROR] Could not fetch live weather data for '{location}': {e}")
        return

    resolved_addr = data["resolved_address"]

    # 1. ENFORCE KARNATAKA GEOGRAPHIC BOUNDARY
    if not is_location_in_karnataka(location, resolved_addr):
        print(f"\n [BLOCKED] OUT-OF-REGION LOCATION DETECTED: '{resolved_addr}'")
        print(" " + "=" * 73)
        print(" [WARNING] This AI Nowcasting Model is strictly trained on KARNATAKA atmospheric")
        print(" observations (Bangalore Observatory / Coastal KA / Western Ghats microclimates).")
        print("")
        print(" Predictions for regions outside Karnataka (other states or countries) are locked")
        print(" to prevent invalid or misleading model output.")
        print("")
        print(" Please select a location within Karnataka, such as:")
        print("  -> Mangalore, Bangalore, Mysore, Udupi, Hubli, Belgaum, Shimoga, Karwar, etc.")
        print(" " + "=" * 73 + "\n")
        return

    temp = data["temp"]
    dew = data["dew"]
    humidity = data["humidity"]
    windspeed = data["windspeed"]
    winddir = data["winddir"]
    cloudcover = data["cloudcover"]
    pressure = data["pressure"]
    conditions = data["conditions"]

    now = datetime.datetime.now()
    real_p_drop = extract_pressure_drop_1d(data)

    live_sample = build_full_feature_dict(
        temp_c=temp,
        dew_c=dew,
        humidity=humidity,
        windspeed_kmh=windspeed,
        cloudcover=cloudcover,
        pressure_drop_1d=real_p_drop,
        winddir=winddir,
        month=now.month,
        day_of_year=now.timetuple().tm_yday,
        pressure_hpa=pressure
    )

    model, feature_cols = load_model_and_schema()
    res = predict_convective_risk(model, feature_cols, live_sample)

    dpd = live_sample["dew_point_depression_c"]
    print(f" Resolved Address:  {resolved_addr}")
    print(f" Weather Condition: {conditions}")
    print(f" Temperature:       {temp}°C | Dew Point: {dew}°C | Humidity: {humidity}%")
    print(f" Cloud Cover:       {cloudcover}% | Wind Speed: {windspeed} km/h (Dir: {winddir}°)")
    print(f" Thermodynamic DPD: {dpd}°C (Dew Point Depression)")
    print("-" * 75)
    print(f" OVERALL CITY STORM PROBABILITY: {res['convective_probability']}%")
    print(f" OVERALL RISK ALERT CLASSIFICATION: [{res['alert_code']}] {res['risk_level']}")
    print("=" * 75)

    # 2. SHORT-TERM CONVECTIVE NOWCAST TIMELINE (+30m, +60m, +90m)
    timeline_items = compute_nowcast_timeline(data, model, feature_cols)
    if timeline_items:
        print("\n" + "=" * 75)
        print(" SHORT-TERM CONVECTIVE NOWCAST TIMELINE (+30m, +60m, +90m)")
        print("=" * 75)
        for item in timeline_items:
            t_label = item["label"]
            t_time = item["time_str"]
            t_cond = item["conditions"]
            t_temp = item["temp"]
            t_hum = item["humidity"]
            t_cloud = item["cloudcover"]
            t_prob = item["probability"]
            t_alert = item["alert_code"]
            print(f"  ⏱️ {t_label:<16} ({t_time}) : {t_cond:<18} | Temp: {t_temp:4.1f}°C | Hum: {t_hum:4.1f}% | Cloud: {t_cloud:3.0f}% | Storm Prob: {t_prob:5.1f}% | [{t_alert}]")
        print("=" * 75)

    # 3. CHECK IF LOCATION HAS SUB-AREA BREAKDOWN (E.G. MANGALORE, BANGALORE, MYSORE, PUTTUR)
    city_key = get_city_key_if_major(location, resolved_addr)
    if city_key in KARNATAKA_SUB_LOCATIONS:
        sub_list = KARNATAKA_SUB_LOCATIONS[city_key]
        print(f"\n" + "=" * 75)
        print(f" SUB-LOCATION NEIGHBORHOOD BREAKDOWN FOR {city_key.upper()} ({len(sub_list)} KEY ZONES)")
        print("=" * 75)
        print(f" {'Sub-Location / Zone':<35} | {'Condition':<20} | {'Temp':<6} | {'Cloud':<6} | {'Storm Prob':<10} | {'Alert'}")
        print("-" * 75)

        for sub in sub_list:
            sub_name = sub["name"]
            sub_query = sub["query"]
            try:
                sub_data = fetch_weather_data_accurate(sub_query)
                stemp = sub_data["temp"]
                sdew = sub_data["dew"]
                shum = sub_data["humidity"]
                swind = sub_data["windspeed"]
                swinddir = sub_data["winddir"]
                scloud = sub_data["cloudcover"]
                spress = sub_data["pressure"]
                scond = sub_data["conditions"]
                sub_p_drop = extract_pressure_drop_1d(sub_data)

                sub_sample = build_full_feature_dict(
                    temp_c=stemp, dew_c=sdew, humidity=shum, windspeed_kmh=swind,
                    cloudcover=scloud, pressure_drop_1d=sub_p_drop,
                    winddir=swinddir, month=now.month, day_of_year=now.timetuple().tm_yday,
                    pressure_hpa=spress
                )
                sub_res = predict_convective_risk(model, feature_cols, sub_sample)

                prob_str = f"{sub_res['convective_probability']:.1f}%"
                alert_tag = f"[{sub_res['alert_code']}]"
                cloud_str = f"{scloud:.0f}%"
                print(f" {sub_name:<35} | {scond:<20} | {stemp:4.1f}°C | {cloud_str:<6} | {prob_str:<10} | {alert_tag}")
            except Exception as se:
                print(f" {sub_name:<35} | [Weather Data Unavailable: {se}]")

        print("=" * 75 + "\n")


def demo_simulation():
    """Run simulated atmospheric scenarios to demonstrate nowcasting capability."""
    print("=" * 75)
    print(" AI THUNDERSTORM & CONVECTIVE NOWCASTING ENGINE - LIVE INFERENCE DEMO")
    print("=" * 75)

    model, feature_cols = load_model_and_schema()

    sample_a = build_full_feature_dict(
        temp_c=32.5, dew_c=23.5, humidity=76.0, windspeed_kmh=25.0,
        cloudcover=85.0, pressure_drop_1d=-3.5, month=5
    )

    sample_b = build_full_feature_dict(
        temp_c=21.0, dew_c=11.0, humidity=45.0, windspeed_kmh=8.0,
        cloudcover=15.0, pressure_drop_1d=0.5, month=1
    )

    print("\n--- TEST SCENARIO A: Pre-Monsoon Convective Storm (Warm, High Cloud/Wind, Falling Pressure) ---")
    res_a = predict_convective_risk(model, feature_cols, sample_a)
    print(f"  -> Convective Storm Probability: {res_a['convective_probability']}%")
    print(f"  -> Risk Classification:         [{res_a['alert_code']}] {res_a['risk_level']}")

    print("\n--- TEST SCENARIO B: Clear Fair-Weather Conditions (Dry, Low Cloud/Wind, Stable Pressure) ---")
    res_b = predict_convective_risk(model, feature_cols, sample_b)
    print(f"  -> Convective Storm Probability: {res_b['convective_probability']}%")
    print(f"  -> Risk Classification:         [{res_b['alert_code']}] {res_b['risk_level']}")


def run_interactive_mode():
    """Prompt user for custom weather inputs and run live nowcasting inference."""
    print("=" * 75)
    print(" INTERACTIVE WEATHER NOWCASTING TESTER (KARNATAKA DOMAIN)")
    print(" Enter current surface weather conditions below to evaluate storm risk:")
    print("=" * 75)

    try:
        temp_input = float(input("1. Temperature in deg C (e.g., 32.0): ") or "30.0")
        dew_input = float(input("2. Dew Point in deg C (e.g., 23.0): ") or "22.0")
        humidity_input = float(input("3. Relative Humidity % (e.g., 78.0): ") or "75.0")
        wind_input = float(input("4. Wind Speed in km/h (e.g., 25.0): ") or "15.0")
        cloudcover_input = float(input("5. Cloud Cover % (e.g., 85.0): ") or "70.0")
        pressure_drop_input = float(input("6. 24-hr Barometric Pressure Change in hPa (e.g., -3.0 for drop, 0.5 for stable): ") or "-2.0")
    except ValueError:
        print("[ERROR] Invalid numerical input. Using default pre-monsoon values.")
        temp_input, dew_input, humidity_input, wind_input, cloudcover_input, pressure_drop_input = 32.0, 23.0, 78.0, 20.0, 80.0, -3.0

    sample = build_full_feature_dict(
        temp_c=temp_input,
        dew_c=dew_input,
        humidity=humidity_input,
        windspeed_kmh=wind_input,
        cloudcover=cloudcover_input,
        pressure_drop_1d=pressure_drop_input
    )

    model, feature_cols = load_model_and_schema()
    res = predict_convective_risk(model, feature_cols, sample)

    dpd = sample["dew_point_depression_c"]
    print("\n" + "=" * 75)
    print(" LIVE PREDICTION RESULTS")
    print("=" * 75)
    print(f"  Input Summary: Temp={temp_input}°C | DewPoint={dew_input}°C (DPD={dpd}°C) | Humidity={humidity_input}%")
    print(f"                 Cloud Cover={cloudcover_input}% | Wind Speed={wind_input} km/h | PressDrop={pressure_drop_input} hPa")
    print("-" * 75)
    print(f"  -> Convective Storm Probability: {res['convective_probability']}%")
    print(f"  -> Risk Alert Classification:   [{res['alert_code']}] {res['risk_level']}")
    print("=" * 75 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for testing."""
    parser = argparse.ArgumentParser(description="Test Convective Nowcasting Model.")
    parser.add_argument(
        "--location",
        "-l",
        type=str,
        default=None,
        help="Karnataka Location or City name (e.g. 'Bangalore', 'Mysore', 'Shimoga', 'Mangalore', 'Udupi').",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run interactive test mode where you enter custom weather readings.",
    )
    parser.add_argument("--temp", type=float, default=None, help="Temperature in deg C")
    parser.add_argument("--dew", type=float, default=None, help="Dew point in deg C")
    parser.add_argument("--humidity", type=float, default=None, help="Relative Humidity percentage (0-100)")
    parser.add_argument("--wind", type=float, default=None, help="Wind speed in km/h")
    parser.add_argument("--cloud", type=float, default=None, help="Cloud Cover percentage (0-100)")
    parser.add_argument("--pressure-drop", type=float, default=None, help="24h barometric drop in hPa")
    parser.add_argument("--month", type=int, default=None, help="Month of year (1-12)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    if args.location:
        fetch_live_weather_and_predict(args.location)
    elif args.interactive:
        run_interactive_mode()
    elif args.temp is not None and args.humidity is not None:
        t = args.temp
        d = args.dew if args.dew is not None else (t - 10.0 if args.humidity < 50 else t - 3.0)
        h = args.humidity
        w = args.wind if args.wind is not None else (8.0 if h < 50 else 25.0)
        c = args.cloud if args.cloud is not None else (15.0 if h < 50 else 80.0)
        p = args.pressure_drop if args.pressure_drop is not None else (0.5 if h < 50 else -2.5)
        m = args.month if args.month is not None else (1 if h < 50 else 6)

        sample = build_full_feature_dict(
            temp_c=t,
            dew_c=d,
            humidity=h,
            windspeed_kmh=w,
            cloudcover=c,
            pressure_drop_1d=p,
            month=m
        )

        model, feature_cols = load_model_and_schema()
        res = predict_convective_risk(model, feature_cols, sample)
        print(f"\n[RESULT] Month: {m} | Temp: {t}°C | DewPoint: {d}°C | Humidity: {h}% | PressDrop: {p} hPa")
        print(f"         Storm Probability: {res['convective_probability']}% -> [{res['alert_code']}] {res['risk_level']}\n")
    else:
        demo_simulation()
