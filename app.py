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
import random
import datetime
from pathlib import Path
from functools import wraps
# pyrefly: ignore[missing-import]
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash

import db
from config import MODELS_DIR, GEMINI_API_KEY
import predict_live as pl
from gemini_nowcast import (
    predict_weather_with_gemini_and_dataset,
    generate_gemini_advisory,
    compute_dataset_physics_prior
)
from notifications import (
    dispatch_thunderstorm_alerts,
    dispatch_thunderstorm_alerts_async,
    get_notification_history,
    send_otp_email,
    send_sms_alert
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aerocast-ai-karnataka-convective-2026-secret-key-prod")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)

# Seed default evaluator demo account in MongoDB if missing
try:
    if not db.find_user_by_email("evaluator@aerocast.ai"):
        db.register_user(
            username="AeroCast Evaluator",
            mobile="9845012345",
            locality="Puttur, Dakshina Kannada",
            email="evaluator@aerocast.ai",
            password="aerocast2026"
        )
        print("[MongoDB] Default evaluator demo account ready: evaluator@aerocast.ai / aerocast2026")
except Exception as e:
    print(f"[MongoDB] Demo account verification notice: {e}")

# Load model and schema at startup
MODEL, FEATURE_COLS = pl.load_model_and_schema()

# Cache for recent queries to avoid hammering external weather APIs
PREDICTION_CACHE = {}
CACHE_TTL_SECONDS = 180


def login_required(f):
    """Decorator to protect authenticated pages and API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required. Please log in.", "authenticated": False}), 401
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_user_context():
    """Injects current_user into all templates seamlessly."""
    if session.get("user_id"):
        return {
            "current_user": {
                "user_id": session.get("user_id"),
                "username": session.get("username"),
                "email": session.get("email"),
                "locality": session.get("locality"),
                "mobile": session.get("mobile")
            }
        }
    return {"current_user": None}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/")
@login_required
def index():
    """Render the main Convective Nowcasting dashboard for authenticated users."""
    return render_template("index.html")


@app.route("/about")
def about():
    """Render the detailed About & Meteorological Concepts page."""
    return render_template("about.html")


@app.route("/history")
@login_required
def history_page():
    """Render the dedicated Search & Prediction History page."""
    user_id = session.get("user_id")
    history_items = db.get_user_search_history(user_id, limit=100)

    total_searches = len(history_items)
    critical_count = sum(1 for h in history_items if h.get("alert_code") == "RED" or (h.get("convective_probability") and h.get("convective_probability") >= 70))
    moderate_count = sum(1 for h in history_items if (h.get("convective_probability") and 35 <= h.get("convective_probability") < 70))
    low_count = sum(1 for h in history_items if (h.get("convective_probability") and h.get("convective_probability") < 35))
    unique_places = len(set((h.get("location") or "").lower() for h in history_items if h.get("location")))

    stats = {
        "total_searches": total_searches,
        "critical_count": critical_count,
        "moderate_count": moderate_count,
        "low_count": low_count,
        "unique_places": unique_places
    }
    return render_template("history.html", history_items=history_items, stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    """User Registration: Stores username, mobile, locality, email, and hashed password in MongoDB."""
    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("index"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        username = data.get("username", "")
        mobile = data.get("mobile", "")
        locality = data.get("locality", "")
        email = data.get("email", "")
        password = data.get("password", "")

        user, err = db.register_user(
            username=username,
            mobile=mobile,
            locality=locality,
            email=email,
            password=password
        )

        if err:
            if request.is_json:
                return jsonify({"success": False, "error": err}), 400
            flash(err, "error")
            return render_template("register.html", error=err)

        # Session-based authentication
        session.permanent = True
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["locality"] = user["locality"]
        session["mobile"] = user["mobile"]

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Account registered successfully!",
                "redirect_url": url_for("index")
            })
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User Login: Authenticates email and password against MongoDB secure hash."""
    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("index"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        email = data.get("email", "")
        password = data.get("password", "")

        user, err = db.authenticate_user(email=email, password=password)

        if err:
            if request.is_json:
                return jsonify({"success": False, "error": err}), 401
            flash(err, "error")
            return render_template("login.html", error=err)

        session.permanent = True
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["locality"] = user["locality"]
        session["mobile"] = user["mobile"]

        next_url = request.args.get("next") or url_for("index")

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Logged in successfully!",
                "redirect_url": next_url
            })
        return redirect(next_url)

    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Clears user session and logs out."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/auth/me")
def auth_me():
    """API endpoint returning active user session details."""
    if session.get("user_id"):
        return jsonify({
            "authenticated": True,
            "user": {
                "user_id": session.get("user_id"),
                "username": session.get("username"),
                "email": session.get("email"),
                "locality": session.get("locality"),
                "mobile": session.get("mobile")
            }
        })
    return jsonify({"authenticated": False, "user": None}), 401




@app.route("/profile")
@login_required
def profile():
    """User Profile & Account Settings."""
    user = db.find_user_by_id(session.get("user_id"))
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


@app.route("/api/profile/update-details", methods=["POST"])
@login_required
def profile_update_details():
    """Updates basic profile details: username, locality."""
    data = request.get_json(silent=True) or request.form.to_dict()
    username = (data.get("username") or "").strip()
    locality = (data.get("locality") or "").strip()

    if not username or len(username) < 2:
        return jsonify({"success": False, "error": "Username must be at least 2 characters long."}), 400
    if not locality:
        return jsonify({"success": False, "error": "Locality cannot be empty."}), 400

    ok, err = db.update_user_profile(session["user_id"], username=username, locality=locality)
    if not ok:
        return jsonify({"success": False, "error": err or "Failed to update profile."}), 400

    session["username"] = username
    session["locality"] = locality
    return jsonify({
        "success": True,
        "message": "Profile details updated successfully!",
        "username": username,
        "locality": locality
    })


@app.route("/api/profile/send-mobile-otp", methods=["POST"])
@login_required
def profile_send_mobile_otp():
    """Generates and sends a 6-digit OTP to verify a new mobile number."""
    data = request.get_json(silent=True) or request.form.to_dict()
    new_mobile = db.normalize_mobile(data.get("new_mobile", ""))

    if not new_mobile or len(new_mobile) < 10:
        return jsonify({"success": False, "error": "Please enter a valid 10-digit Indian mobile number."}), 400

    if new_mobile == session.get("mobile"):
        return jsonify({"success": False, "error": "This is already your registered mobile number."}), 400

    # Check if number already registered to another account
    existing = db.find_user_by_mobile(new_mobile)
    if existing and str(existing["_id"]) != session.get("user_id"):
        return jsonify({"success": False, "error": "This mobile number is already in use by another account."}), 400

    otp = f"{random.randint(100000, 999999)}"
    db.save_otp(session["email"] + ":" + new_mobile, otp, purpose="mobile_change", expires_minutes=10)

    # Deliver OTP via registered email
    send_otp_email(
        recipient_email=session["email"],
        recipient_name=session.get("username", "Citizen"),
        otp_code=otp,
        purpose="Mobile Number Update"
    )

    # Also attempt SMS to new mobile
    send_sms_alert(
        recipient_mobile=new_mobile,
        recipient_name=session.get("username", "Citizen"),
        alert_data={"level": "OTP", "headline": f"Your AeroCast AI verification code is {otp}"}
    )

    return jsonify({
        "success": True,
        "message": f"Verification code has been sent to your registered email ({session['email']}) and mobile (+91 {new_mobile})."
    })


@app.route("/api/profile/verify-mobile-otp", methods=["POST"])
@login_required
def profile_verify_mobile_otp():
    """Verifies OTP and saves the new mobile number."""
    data = request.get_json(silent=True) or request.form.to_dict()
    new_mobile = db.normalize_mobile(data.get("new_mobile", ""))
    otp = (data.get("otp") or "").strip()

    if not new_mobile or len(new_mobile) < 10:
        return jsonify({"success": False, "error": "Invalid mobile number."}), 400
    if not otp or len(otp) != 6:
        return jsonify({"success": False, "error": "Please enter the 6-digit OTP code."}), 400

    ok, msg = db.verify_otp(session["email"] + ":" + new_mobile, otp, purpose="mobile_change")
    if not ok:
        return jsonify({"success": False, "error": msg}), 400

    update_ok, update_err = db.update_user_mobile(session["user_id"], new_mobile)
    if not update_ok:
        return jsonify({"success": False, "error": update_err or "Failed to update mobile number."}), 400

    session["mobile"] = new_mobile
    return jsonify({
        "success": True,
        "message": f"Mobile number successfully updated to +91 {new_mobile}!",
        "mobile": new_mobile
    })


@app.route("/api/profile/send-password-otp", methods=["POST"])
@login_required
def profile_send_password_otp():
    """Generates and sends a 6-digit OTP to the user's email for password change."""
    otp = f"{random.randint(100000, 999999)}"
    db.save_otp(session["email"], otp, purpose="password_change", expires_minutes=10)

    send_otp_email(
        recipient_email=session["email"],
        recipient_name=session.get("username", "Citizen"),
        otp_code=otp,
        purpose="Password Change"
    )

    return jsonify({
        "success": True,
        "message": f"Verification code sent to your registered email ({session['email']})."
    })


@app.route("/api/profile/verify-password-otp", methods=["POST"])
@login_required
def profile_verify_password_otp():
    """Verifies OTP and updates user's password."""
    data = request.get_json(silent=True) or request.form.to_dict()
    otp = (data.get("otp") or "").strip()
    new_password = (data.get("new_password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not otp or len(otp) != 6:
        return jsonify({"success": False, "error": "Please enter the 6-digit OTP code."}), 400
    if not new_password or len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters long."}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match."}), 400

    ok, msg = db.verify_otp(session["email"], otp, purpose="password_change")
    if not ok:
        return jsonify({"success": False, "error": msg}), 400

    update_ok, update_err = db.update_user_password(session["user_id"], new_password)
    if not update_ok:
        return jsonify({"success": False, "error": update_err or "Failed to update password."}), 400

    return jsonify({"success": True, "message": "Password changed successfully!"})


@app.route("/forgot-password")
def forgot_password():
    """Forgot Password page: allows resetting password using email OTP."""
    if session.get("user_id"):
        return redirect(url_for("index"))
    return render_template("forgot_password.html")


@app.route("/api/auth/forgot-password/send-otp", methods=["POST"])
def auth_forgot_password_send_otp():
    """Validates email and sends password reset OTP."""
    data = request.get_json(silent=True) or request.form.to_dict()
    email = db.normalize_email(data.get("email", ""))

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Please enter a valid email address."}), 400

    user = db.find_user_by_email(email)
    if not user:
        return jsonify({"success": False, "error": "No account found with this email address. Please check and try again."}), 404

    otp = f"{random.randint(100000, 999999)}"
    db.save_otp(email, otp, purpose="forgot_password", expires_minutes=10)

    send_otp_email(
        recipient_email=email,
        recipient_name=user.get("username", "Citizen"),
        otp_code=otp,
        purpose="Password Reset"
    )

    return jsonify({
        "success": True,
        "message": f"Verification code sent to {email}. Please check your inbox (and spam folder)."
    })


@app.route("/api/auth/forgot-password/reset-password", methods=["POST"])
def auth_forgot_password_reset_password():
    """Verifies OTP and resets user password."""
    data = request.get_json(silent=True) or request.form.to_dict()
    email = db.normalize_email(data.get("email", ""))
    otp = (data.get("otp") or "").strip()
    new_password = (data.get("new_password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Please enter a valid email address."}), 400
    if not otp or len(otp) != 6:
        return jsonify({"success": False, "error": "Please enter the 6-digit OTP code."}), 400
    if not new_password or len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters long."}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match."}), 400

    ok, msg = db.verify_otp(email, otp, purpose="forgot_password")
    if not ok:
        return jsonify({"success": False, "error": msg}), 400

    update_ok, update_err = db.update_user_password_by_email(email, new_password)
    if not update_ok:
        return jsonify({"success": False, "error": update_err or "Failed to reset password."}), 400

    return jsonify({
        "success": True,
        "message": "Password reset successfully! Please sign in with your new password.",
        "redirect_url": url_for("login")
    })


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
@login_required
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
            current_uid = session.get("user_id")
            if current_uid:
                try:
                    db.save_search_history(
                        user_id=current_uid,
                        location=location,
                        resolved_address=cached_data.get("resolved_address", location),
                        latitude=cached_data.get("latitude"),
                        longitude=cached_data.get("longitude"),
                        is_karnataka=cached_data.get("is_karnataka", True),
                        prediction=cached_data.get("prediction", {}),
                        telemetry=cached_data.get("telemetry", {}),
                        thunderstorm_alert=cached_data.get("thunderstorm_alert"),
                        warning=cached_data.get("warning")
                    )
                except Exception as ex_hist:
                    print(f"[Search History Cache Notice] {ex_hist}")
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
                elif "lat" in sub and "lon" in sub:
                    sub_lat = sub["lat"]
                    sub_lon = sub["lon"]
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

        # Compute In-Dashboard Thunderstorm Alert Message
        if is_ka and prediction.get("is_available") and prediction.get("convective_probability") is not None:
            prob = float(prediction["convective_probability"])
            loc_label = resolved_addr.split(",")[0].strip() if resolved_addr else location

            # Determine earliest lead time from timeline (+30m, +60m, +90m)
            lead_time = "+30 to +90 Mins"
            if timeline and isinstance(timeline, list) and len(timeline) > 0:
                for step in timeline:
                    sprob = step.get("probability")
                    if sprob is not None:
                        if sprob >= 70.0:
                            lead_time = step.get("label") or step.get("time_label") or "+30 Mins"
                            break
                        elif sprob >= 35.0:
                            lead_time = step.get("label") or step.get("time_label") or "+60 Mins"

            if prob < 35.0:
                alert_level = "LOW"
                alert_headline = "Low thunderstorm risk. Calm and stable weather expected across the region."
                alert_explanation = f"Boundary-layer thermodynamic energy over {loc_label} is stable. Convective storm initiation is not expected within the forecast window."
            elif prob < 70.0:
                alert_level = "MODERATE"
                alert_headline = "Thunderstorm conditions may develop. Please monitor weather updates."
                alert_explanation = f"Elevated moisture and convective instability detected over {loc_label}. Towering cumulus development and sudden passing showers possible within {lead_time}."
            else:
                alert_level = "CRITICAL"
                alert_headline = "High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings."
                alert_explanation = f"Critical convective atmospheric instability observed across {loc_label}. Intense lightning, heavy downbursts, and gusty winds anticipated within {lead_time}."

            thunderstorm_alert = {
                "status": "active",
                "level": alert_level,
                "probability": prob,
                "location": loc_label,
                "lead_time": lead_time,
                "headline": alert_headline,
                "explanation": alert_explanation,
                "timestamp": now.strftime("%I:%M %p IST")
            }
        else:
            thunderstorm_alert = {
                "status": "unavailable",
                "level": "NONE",
                "probability": None,
                "location": location,
                "lead_time": "N/A",
                "headline": "No current thunderstorm alert data available",
                "explanation": warning_msg or "Select or search any Karnataka location to evaluate live convective storm conditions.",
                "timestamp": now.strftime("%I:%M %p IST")
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
            "gemini_advisory": gemini_advisory,
            "thunderstorm_alert": thunderstorm_alert
        }

        # Store in cache
        PREDICTION_CACHE[cache_key] = (response_data, now_ts)

        # Store in search history for authenticated user
        current_uid = session.get("user_id")
        if current_uid:
            try:
                db.save_search_history(
                    user_id=current_uid,
                    location=location,
                    resolved_address=resolved_addr,
                    latitude=lat,
                    longitude=lon,
                    is_karnataka=is_ka,
                    prediction=prediction,
                    telemetry=telemetry_pack,
                    thunderstorm_alert=thunderstorm_alert,
                    warning=warning_msg
                )
            except Exception as ex_hist:
                print(f"[Search History Fresh Notice] {ex_hist}")

        # Automated Thunderstorm Alert Dispatch for high/moderate convective risk (Broadcast to ALL users)
        if thunderstorm_alert.get("status") == "active" and thunderstorm_alert.get("level") in ["CRITICAL", "MODERATE"]:
            current_uid = session.get("user_id")
            try:
                db.register_global_thunderstorm_alert(
                    thunderstorm_alert,
                    reported_by_id=current_uid,
                    reported_by_name=session.get("username")
                )
            except Exception as e_reg:
                print(f"[ACTIVE ALERT REGISTER WARNING] {e_reg}")
            dispatch_thunderstorm_alerts_async(thunderstorm_alert, target_user_id=current_uid, force=False)

        return jsonify(response_data)

    except Exception as e:
        print(f"[ERROR] /api/nowcast failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/demo/thunderstorm")
def demo_thunderstorm():
    """
    Presentation and evaluator demonstration endpoint.
    Simulates severe, moderate, or calm thunderstorm conditions on demand.
    Query params: scenario ('critical', 'moderate', 'low'), location (default 'Puttur')
    """
    scenario = request.args.get("scenario", "critical").lower()
    location = request.args.get("location", "Puttur").strip()
    now = datetime.datetime.now()
    now_ts = now.strftime("%I:%M:%S %p IST")

    if scenario == "critical":
        prob = 88.5
        level = "CRITICAL"
        headline = "High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings."
        explanation = f"Critical convective atmospheric instability observed across {location}. Intense lightning, heavy downbursts, and gusty winds anticipated within +30m Projection."
        lead_time = "+30m Projection"
        temp, humidity, dew, dpd, vpd, pressure, pressure_drop, wind = 28.8, 94.0, 27.6, 1.2, 0.3, 1001.2, -3.8, 38.5
        cond = "Severe Thunderstorm with Downdraft Gusts"
    elif scenario == "moderate":
        prob = 54.2
        level = "MODERATE"
        headline = "Thunderstorm conditions may develop. Please monitor weather updates."
        explanation = f"Elevated moisture and convective instability detected over {location}. Towering cumulus development and sudden passing showers possible within +60m Projection."
        lead_time = "+60m Projection"
        temp, humidity, dew, dpd, vpd, pressure, pressure_drop, wind = 30.2, 82.0, 25.8, 4.4, 0.9, 1005.1, -1.6, 18.0
        cond = "Towering Cumulus / Developing Thunderstorm Cell"
    else:
        prob = 16.5
        level = "LOW"
        headline = "Low thunderstorm risk. Calm and stable weather expected across the region."
        explanation = f"Boundary-layer thermodynamic energy over {location} is stable. Convective storm initiation is not expected within the forecast window."
        lead_time = "+30 to +90 Mins"
        temp, humidity, dew, dpd, vpd, pressure, pressure_drop, wind = 27.5, 62.0, 19.5, 8.0, 1.8, 1012.0, 0.2, 8.5
        cond = "Clear & Stable Atmosphere"

    coords = pl.resolve_karnataka_coordinates(location)
    demo_lat = coords.get("lat", 12.7667)
    demo_lon = coords.get("lon", 75.2016)

    loc_low = location.lower()
    if "mangalore" in loc_low or "mangaluru" in loc_low:
        demo_zones = [
            {"name": "Hampankatta (City Centre & Taluk Hub)", "lat": 12.8700, "lon": 74.8430, "probability": prob, "temp": temp, "humidity": humidity, "is_center": True},
            {"name": "Kadri Hills & Mallikatte Zone", "lat": 12.8830, "lon": 74.8620, "probability": round(prob - 2.5, 1), "temp": round(temp + 0.3, 1), "humidity": round(humidity - 2, 1)},
            {"name": "Surathkal & NITK Coastal Sector", "lat": 13.0070, "lon": 74.7940, "probability": round(prob + 2.0, 1), "temp": round(temp - 0.5, 1), "humidity": round(humidity + 3, 1)},
            {"name": "Panambur Port & Industrial Sector", "lat": 12.9460, "lon": 74.8120, "probability": round(prob + 1.2, 1), "temp": round(temp - 0.2, 1), "humidity": round(humidity + 2, 1)},
            {"name": "Ullal Coastal Belt & Estuary", "lat": 12.8050, "lon": 74.8520, "probability": round(prob - 3.5, 1), "temp": round(temp + 0.2, 1), "humidity": round(humidity - 1, 1)},
            {"name": "Bajpe (Airport Zone & North Taluk)", "lat": 12.9803, "lon": 74.8832, "probability": round(prob + 0.8, 1), "temp": round(temp + 0.1, 1), "humidity": round(humidity + 1, 1)}
        ]
    elif "puttur" in loc_low:
        demo_zones = [
            {"name": "Puttur Town & Bus Stand (Taluk Centre)", "lat": 12.7667, "lon": 75.2016, "probability": prob, "temp": temp, "humidity": humidity, "is_center": True},
            {"name": "Darbe & Bedrala Commercial Sector", "lat": 12.7580, "lon": 75.2050, "probability": round(prob - 1.5, 1), "temp": round(temp + 0.2, 1), "humidity": round(humidity - 1, 1)},
            {"name": "Kabaka & Polya Agricultural Zone", "lat": 12.7880, "lon": 75.1850, "probability": round(prob + 2.0, 1), "temp": round(temp - 0.4, 1), "humidity": round(humidity + 2, 1)},
            {"name": "Bannur & Kemminje Green Corridor", "lat": 12.7520, "lon": 75.2210, "probability": round(prob - 2.0, 1), "temp": round(temp + 0.1, 1), "humidity": round(humidity - 1, 1)},
            {"name": "Aryapu & Balnadu Rural Valley", "lat": 12.7350, "lon": 75.1750, "probability": round(prob + 1.0, 1), "temp": round(temp - 0.3, 1), "humidity": round(humidity + 1, 1)},
            {"name": "Bettampady & Ariyadka Foothills", "lat": 12.7150, "lon": 75.2280, "probability": round(prob - 3.5, 1), "temp": round(temp - 0.6, 1), "humidity": round(humidity + 2, 1)}
        ]
    else:
        demo_zones = [
            {"name": f"{location} Taluk Centre", "lat": demo_lat, "lon": demo_lon, "probability": prob, "temp": temp, "humidity": humidity, "is_center": True},
            {"name": f"{location} North Agro Sector", "lat": round(demo_lat + 0.035, 4), "lon": round(demo_lon + 0.015, 4), "probability": round(prob - 1.0, 1), "temp": temp, "humidity": humidity},
            {"name": f"{location} South Valley Sector", "lat": round(demo_lat - 0.035, 4), "lon": round(demo_lon - 0.015, 4), "probability": round(prob + 1.5, 1), "temp": temp, "humidity": humidity},
            {"name": f"{location} East Highland Ridge", "lat": round(demo_lat + 0.015, 4), "lon": round(demo_lon + 0.038, 4), "probability": round(prob + 2.5, 1), "temp": temp, "humidity": humidity},
            {"name": f"{location} West Commercial Belt", "lat": round(demo_lat - 0.015, 4), "lon": round(demo_lon - 0.038, 4), "probability": round(prob - 2.0, 1), "temp": temp, "humidity": humidity}
        ]

    demo_response = {
        "scenario": scenario,
        "location": location,
        "resolved_address": f"{location} Taluk Observatory, Karnataka (Evaluation Demo Mode)",
        "latitude": demo_lat,
        "longitude": demo_lon,
        "micro_zones": demo_zones,
        "is_karnataka": True,
        "timestamp": now_ts + " (Demo)",
        "telemetry": {
            "temp": temp, "humidity": humidity, "dew": dew, "dpd": dpd, "vpd": vpd,
            "pressure": pressure, "pressure_drop": pressure_drop, "windspeed": wind,
            "cloudcover": 98.0 if scenario == "critical" else (72.0 if scenario == "moderate" else 15.0),
            "conditions": cond
        },
        "prediction": {
            "convective_probability": prob,
            "binary_prediction": 1 if prob >= 50 else 0,
            "risk_level": f"{level} (Thunderstorm Evaluation Simulation)",
            "alert_code": "RED" if level == "CRITICAL" else ("YELLOW" if level == "MODERATE" else "GREEN"),
            "weather_condition": cond,
            "is_available": True
        },
        "thunderstorm_alert": {
            "status": "active",
            "level": level,
            "probability": prob,
            "location": location,
            "lead_time": lead_time,
            "headline": headline,
            "explanation": explanation,
            "timestamp": now.strftime("%I:%M %p IST") + " (Simulation)"
        }
    }
    if level in ["CRITICAL", "MODERATE"]:
        current_uid = session.get("user_id")
        try:
            db.register_global_thunderstorm_alert(
                demo_response["thunderstorm_alert"],
                reported_by_id=current_uid,
                reported_by_name=session.get("username")
            )
        except Exception as e_reg:
            print(f"[ACTIVE ALERT REGISTER WARNING] {e_reg}")
        dispatch_thunderstorm_alerts_async(demo_response["thunderstorm_alert"], target_user_id=current_uid, force=True)

    return jsonify(demo_response)


@app.route("/api/notifications/dispatch", methods=["POST"])
@login_required
def api_dispatch_notifications():
    """
    Dispatches automated SMS and Email thunderstorm alerts to registered citizens.
    Payload: {
        location: str,
        probability: float,
        level: str,
        lead_time: str,
        headline: str,
        explanation: str,
        channels: ['email', 'sms'] (optional, default both),
        target_user_id: str (optional)
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        alert_data = {
            "location": data.get("location", "Puttur"),
            "probability": data.get("probability", 88.5),
            "level": data.get("level", "CRITICAL"),
            "lead_time": data.get("lead_time", "+30m Projection"),
            "headline": data.get("headline", "High thunderstorm risk detected. Avoid exposed outdoor areas."),
            "explanation": data.get("explanation", "Critical convective atmospheric instability observed across Karnataka."),
            "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p IST")
        }
        channels = data.get("channels", ["email", "sms", "telegram"])
        target_user_id = data.get("target_user_id") or session.get("user_id")
        force = bool(data.get("force", True))

        try:
            db.register_global_thunderstorm_alert(
                alert_data,
                reported_by_id=target_user_id,
                reported_by_name=session.get("username")
            )
        except Exception as e_reg:
            print(f"[ACTIVE ALERT REGISTER WARNING] {e_reg}")

        result = dispatch_thunderstorm_alerts(alert_data, target_user_id=target_user_id, channels=channels, force=force)
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] /api/notifications/dispatch failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/notifications/history", methods=["GET"])
@login_required
def api_notification_history():
    """Returns recent alert notification records from MongoDB."""
    try:
        limit = int(request.args.get("limit", 20))
        history = get_notification_history(limit=limit)
        return jsonify({"success": True, "history": history, "count": len(history)})
    except Exception as e:
        print(f"[ERROR] /api/notifications/history failed: {e}")
        return jsonify({"success": False, "error": str(e), "history": []}), 500


@app.route("/api/history", methods=["GET"])
@login_required
def api_get_search_history():
    """Returns the current user's search history as JSON."""
    try:
        user_id = session.get("user_id")
        limit = min(100, max(1, int(request.args.get("limit", 50))))
        items = db.get_user_search_history(user_id, limit=limit)
        return jsonify({"success": True, "history": items, "count": len(items)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "history": []}), 500


@app.route("/api/history/<history_id>", methods=["DELETE"])
@login_required
def api_delete_search_history(history_id: str):
    """Deletes a specific search history entry for the logged-in user."""
    try:
        user_id = session.get("user_id")
        deleted = db.delete_search_history_item(history_id, user_id)
        if deleted:
            return jsonify({"success": True, "message": "Search history entry removed."})
        return jsonify({"success": False, "error": "History entry not found or unauthorized."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/clear", methods=["POST"])
@login_required
def api_clear_search_history():
    """Clears all search history entries for the logged-in user."""
    try:
        user_id = session.get("user_id")
        count = db.clear_user_search_history(user_id)
        return jsonify({"success": True, "message": f"Cleared {count} search history records.", "deleted_count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts/active", methods=["GET"])
def api_get_active_alert():
    """
    Returns the latest active thunderstorm alert across Karnataka.
    Polled every few seconds by all client browsers so EVERY connected user
    receives real-time broadcast toast notifications, regardless of who checked.
    """
    try:
        alert = db.get_latest_global_thunderstorm_alert()
        if alert:
            return jsonify({"active": True, "alert": alert})
        return jsonify({"active": False, "alert": None})
    except Exception as e:
        return jsonify({"active": False, "error": str(e), "alert": None}), 500


@app.route("/api/alerts/deactivate", methods=["POST"])
def api_deactivate_alerts():
    """
    Deactivates any active global alerts in MongoDB (e.g. when user clicks Reset to Live).
    """
    try:
        count = db.deactivate_all_active_alerts()
        return jsonify({"success": True, "deactivated": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" ⚡ AeroCast AI — Karnataka Convective Weather Nowcasting Server")
    print(" Model: Soft Voting Ensemble (LightGBM + XGBoost + HistGradientBoosting)")
    print(" AI Advisory: Google Gemini API (gemini-flash-lite / gemini-3.5-flash-lite)")
    print(" Dashboard URL: http://127.0.0.1:5000")
    print("=" * 70 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
