"""
AeroCast AI — MongoDB User Database Management
==============================================
Provides secure user registration, password hashing, credential verification,
and unique constraint management for the Karnataka Nowcasting platform.
"""

import os
import re
import datetime
from typing import Optional, Dict, Any, Tuple
# pyrefly: ignore[missing-import]
from bson import ObjectId
# pyrefly: ignore[missing-import]
import pymongo
# pyrefly: ignore[missing-import]
from pymongo.collection import Collection
# pyrefly: ignore[missing-import]
from pymongo.database import Database
# pyrefly: ignore[missing-import]
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB", "aerocast_db")

_client: Optional[pymongo.MongoClient] = None
_db: Optional[Database] = None


def get_db() -> Database:
    """Acquires a singleton connection to the MongoDB database."""
    global _client, _db
    if _db is None:
        try:
            _client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
            _db = _client[MONGODB_DB_NAME]
            # Ensure unique constraints on email and mobile
            _db.users.create_index("email", unique=True)
            _db.users.create_index("mobile", unique=True)
        except Exception as e:
            print(f"[MongoDB WARNING] Could not initialize connection: {e}")
            raise
    return _db


def get_users_collection() -> Collection:
    """Returns the 'users' collection with ensured indexes."""
    return get_db()["users"]


def normalize_email(email: str) -> str:
    """Standardizes email address to lower case and trimmed."""
    return (email or "").strip().lower()


def normalize_mobile(mobile: str) -> str:
    """Standardizes mobile number by stripping spaces, dashes, and country prefixes if simple."""
    num = re.sub(r"[^\d]", "", (mobile or "").strip())
    # If 12 digits starting with 91, keep 10-digit base for consistency in India
    if len(num) == 12 and num.startswith("91"):
        num = num[2:]
    return num


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Look up a user document by normalized email address."""
    col = get_users_collection()
    return col.find_one({"email": normalize_email(email)})


def find_user_by_mobile(mobile: str) -> Optional[Dict[str, Any]]:
    """Look up a user document by normalized mobile number."""
    col = get_users_collection()
    return col.find_one({"mobile": normalize_mobile(mobile)})


def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Look up a user document by its MongoDB ObjectId string."""
    try:
        col = get_users_collection()
        return col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def register_user(
    username: str,
    mobile: str,
    locality: str,
    email: str,
    password: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Registers a new user into MongoDB after hashing the password and validating constraints.
    Returns (user_document, None) on success, or (None, error_message) on failure.
    """
    username = (username or "").strip()
    norm_mobile = normalize_mobile(mobile)
    locality = (locality or "").strip()
    norm_email = normalize_email(email)
    password = (password or "").strip()

    # Validation
    if not username or len(username) < 2:
        return None, "Username must be at least 2 characters long."
    if not norm_mobile or len(norm_mobile) < 10:
        return None, "Please enter a valid 10-digit mobile number."
    if not locality:
        return None, "Area / Locality in Karnataka is required."
    if not norm_email or "@" not in norm_email or "." not in norm_email:
        return None, "Please enter a valid email address."
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters long."

    col = get_users_collection()

    # Check for duplicate email
    if col.find_one({"email": norm_email}):
        return None, "An account with this email address already exists. Please log in."

    # Check for duplicate mobile
    if col.find_one({"mobile": norm_mobile}):
        return None, "An account with this mobile number already exists."

    # Hash password securely using pbkdf2:sha256
    password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    user_doc = {
        "username": username,
        "mobile": norm_mobile,
        "locality": locality,
        "email": norm_email,
        "password_hash": password_hash,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "last_login": datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        result = col.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc, None
    except pymongo.errors.DuplicateKeyError as e:
        if "email" in str(e):
            return None, "An account with this email address already exists."
        elif "mobile" in str(e):
            return None, "An account with this mobile number already exists."
        return None, "A duplicate record was detected. Please check your details."
    except Exception as e:
        return None, f"Registration failed due to a database error: {e}"


def authenticate_user(email: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates user credentials against stored password hash.
    Returns (user_document, None) on success, or (None, error_message) on failure.
    """
    norm_email = normalize_email(email)
    password = (password or "").strip()

    if not norm_email or not password:
        return None, "Please provide both email address and password."

    user = find_user_by_email(norm_email)
    if not user:
        return None, "No account found with this email address. Please register."

    stored_hash = user.get("password_hash")
    if not stored_hash or not check_password_hash(stored_hash, password):
        return None, "Invalid password. Please check your credentials."

    # Update last login timestamp
    try:
        col = get_users_collection()
        col.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.now(datetime.timezone.utc)}}
        )
    except Exception:
        pass

    return user, None



def get_otps_collection() -> Collection:
    """Acquires the OTPs collection with TTL index on expires_at."""
    col = get_db()["otps"]
    try:
        col.create_index("expires_at", expireAfterSeconds=0)
    except Exception:
        pass
    return col


def save_otp(identifier: str, otp_code: str, purpose: str, expires_minutes: int = 10):
    """Saves a generated 6-digit OTP for email/mobile verification."""
    col = get_otps_collection()
    norm_id = str(identifier).strip().lower()
    # Invalidate any previous unverified OTP for the same identifier and purpose
    col.update_many(
        {"identifier": norm_id, "purpose": purpose, "used": False},
        {"$set": {"used": True}}
    )
    doc = {
        "identifier": norm_id,
        "otp": str(otp_code).strip(),
        "purpose": purpose,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "expires_at": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expires_minutes),
        "used": False
    }
    col.insert_one(doc)


def verify_otp(identifier: str, otp_code: str, purpose: str) -> Tuple[bool, str]:
    """Validates a provided OTP code against stored records."""
    col = get_otps_collection()
    norm_id = str(identifier).strip().lower()
    code = str(otp_code).strip()
    now = datetime.datetime.now(datetime.timezone.utc)

    rec = col.find_one({
        "identifier": norm_id,
        "otp": code,
        "purpose": purpose,
        "used": False,
        "expires_at": {"$gte": now}
    })

    if not rec:
        return False, "Invalid or expired OTP code. Please request a new verification code."

    # Mark as used
    col.update_one({"_id": rec["_id"]}, {"$set": {"used": True}})
    return True, "OTP verified successfully."


def update_user_profile(user_id: str, username: str = None, locality: str = None) -> Tuple[bool, Optional[str]]:
    """Updates basic profile details (username, locality)."""
    try:
        col = get_users_collection()
        updates = {}
        if username:
            uname = username.strip()
            if len(uname) < 2:
                return False, "Username must be at least 2 characters long."
            updates["username"] = uname
        if locality:
            loc = locality.strip()
            if not loc:
                return False, "Locality cannot be empty."
            updates["locality"] = loc

        if not updates:
            return True, None

        col.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return True, None
    except Exception as e:
        return False, f"Database update failed: {e}"


def update_user_mobile(user_id: str, new_mobile: str) -> Tuple[bool, Optional[str]]:
    """Updates user mobile number after OTP verification."""
    try:
        col = get_users_collection()
        norm_mobile = normalize_mobile(new_mobile)
        if not norm_mobile or len(norm_mobile) < 10:
            return False, "Please provide a valid 10-digit mobile number."

        # Check if already taken by another account
        existing = col.find_one({"mobile": norm_mobile, "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            return False, "This mobile number is already registered to another AeroCast account."

        col.update_one({"_id": ObjectId(user_id)}, {"$set": {"mobile": norm_mobile}})
        return True, None
    except Exception as e:
        return False, f"Mobile update failed: {e}"


def update_user_password(user_id: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """Updates user password hash securely."""
    try:
        col = get_users_collection()
        pwd = (new_password or "").strip()
        if not pwd or len(pwd) < 6:
            return False, "Password must be at least 6 characters long."

        password_hash = generate_password_hash(pwd, method="pbkdf2:sha256", salt_length=16)
        col.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": password_hash}})
        return True, None
    except Exception as e:
        return False, f"Password update failed: {e}"


def update_user_password_by_email(email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """Updates user password hash using email (for Forgot Password flow)."""
    try:
        col = get_users_collection()
        norm_email = normalize_email(email)
        user = col.find_one({"email": norm_email})
        if not user:
            return False, "No account found with this email address."

        pwd = (new_password or "").strip()
        if not pwd or len(pwd) < 6:
            return False, "Password must be at least 6 characters long."

        password_hash = generate_password_hash(pwd, method="pbkdf2:sha256", salt_length=16)
        col.update_one({"_id": user["_id"]}, {"$set": {"password_hash": password_hash}})
        return True, None
    except Exception as e:
        return False, f"Password update failed: {e}"


# ==============================================================================
# Search & Nowcast History Storage
# ==============================================================================

def get_search_history_collection() -> Collection:
    """Acquires the search_history collection with indexes for fast retrieval."""
    col = get_db()["search_history"]
    try:
        col.create_index([("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        col.create_index("created_at")
    except Exception:
        pass
    return col


def save_search_history(
    user_id: str,
    location: str,
    resolved_address: str,
    latitude: float,
    longitude: float,
    is_karnataka: bool,
    prediction: Dict[str, Any],
    telemetry: Dict[str, Any],
    thunderstorm_alert: Optional[Dict[str, Any]] = None,
    warning: Optional[str] = None
) -> Optional[str]:
    """
    Saves or refreshes a search history record for the authenticated user.
    If the user's most recent search was for the identical location within 60 seconds,
    it refreshes the telemetry/prediction without creating an unnecessary duplicate record.
    """
    if not user_id:
        return None
    try:
        col = get_search_history_collection()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = now_utc.astimezone(ist_tz)
        timestamp_str = now_ist.strftime("%d %b %Y, %I:%M %p IST")

        clean_loc = (location or "").strip()
        prob = (prediction or {}).get("convective_probability")
        if prob is not None:
            try:
                prob = round(float(prob), 1)
            except Exception:
                pass

        doc = {
            "user_id": str(user_id),
            "location": clean_loc,
            "resolved_address": resolved_address or clean_loc,
            "latitude": round(float(latitude), 4) if latitude is not None else None,
            "longitude": round(float(longitude), 4) if longitude is not None else None,
            "is_karnataka": bool(is_karnataka),
            "convective_probability": prob,
            "risk_level": (prediction or {}).get("risk_level", "Unknown"),
            "alert_code": (prediction or {}).get("alert_code", "GREEN"),
            "weather_condition": (prediction or {}).get("weather_condition") or (telemetry or {}).get("conditions", "Clear"),
            "temp": (telemetry or {}).get("temp"),
            "humidity": (telemetry or {}).get("humidity"),
            "windspeed": (telemetry or {}).get("windspeed"),
            "pressure": (telemetry or {}).get("pressure"),
            "dew": (telemetry or {}).get("dew"),
            "dpd": (telemetry or {}).get("dpd"),
            "vpd": (telemetry or {}).get("vpd"),
            "lead_time": (thunderstorm_alert or {}).get("lead_time", "N/A"),
            "warning": warning,
            "timestamp_str": timestamp_str,
            "created_at": now_utc
        }

        # Check if latest record for this user is the same location within last 60 seconds
        recent = col.find_one(
            {"user_id": str(user_id)},
            sort=[("created_at", pymongo.DESCENDING)]
        )
        if recent and recent.get("location", "").lower() == clean_loc.lower():
            rec_created = recent.get("created_at")
            if rec_created:
                if rec_created.tzinfo is None:
                    rec_created = rec_created.replace(tzinfo=datetime.timezone.utc)
                diff_sec = (now_utc - rec_created).total_seconds()
                if diff_sec < 60:
                    col.update_one({"_id": recent["_id"]}, {"$set": doc})
                    return str(recent["_id"])

        res = col.insert_one(doc)
        return str(res.inserted_id)
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to save search history: {e}")
        return None


def get_user_search_history(user_id: str, limit: int = 100) -> list:
    """
    Retrieves the search history for a user, ordered from most recent to oldest.
    """
    if not user_id:
        return []
    try:
        col = get_search_history_collection()
        cursor = col.find({"user_id": str(user_id)}).sort("created_at", pymongo.DESCENDING).limit(limit)
        items = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return items
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to fetch search history: {e}")
        return []


def delete_search_history_item(history_id: str, user_id: str) -> bool:
    """Deletes a specific search history record owned by the user."""
    try:
        col = get_search_history_collection()
        res = col.delete_one({"_id": ObjectId(history_id), "user_id": str(user_id)})
        return res.deleted_count > 0
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to delete history item: {e}")
        return False


def clear_user_search_history(user_id: str) -> int:
    """Clears all search history records for a user."""
    try:
        col = get_search_history_collection()
        res = col.delete_many({"user_id": str(user_id)})
        return res.deleted_count
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to clear search history: {e}")
        return 0


# ==============================================================================
# Global Active Thunderstorm Alerts Registry
# ==============================================================================

def get_active_alerts_collection() -> Collection:
    """Acquires the active_alerts collection with TTL auto-expiration."""
    col = get_db()["active_alerts"]
    try:
        col.create_index("created_at", expireAfterSeconds=7200) # 2 hours auto-expire
        col.create_index([("is_active", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    except Exception:
        pass
    return col


def register_global_thunderstorm_alert(
    alert_data: Dict[str, Any],
    reported_by_id: Optional[str] = None,
    reported_by_name: Optional[str] = None
) -> Optional[str]:
    """
    Registers an active thunderstorm alert into MongoDB so ALL connected citizens
    and observers across Karnataka receive the real-time notification across all devices.
    """
    if not alert_data or alert_data.get("level") not in ["CRITICAL", "MODERATE"]:
        return None

    try:
        col = get_active_alerts_collection()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = now_utc.astimezone(ist_tz)

        loc = (alert_data.get("location") or "Karnataka").strip()
        level = (alert_data.get("level") or "CRITICAL").upper()
        prob = alert_data.get("probability", 88.5)
        if prob is not None:
            try:
                prob = round(float(prob), 1)
            except Exception:
                pass

        is_demo = bool(
            alert_data.get("is_demo") or 
            "demo" in str(alert_data.get("headline", "")).lower() or 
            "simulation" in str(alert_data.get("explanation", "")).lower() or
            "simulation" in str(alert_data.get("timestamp", "")).lower()
        )
        ttl_minutes = 2 if is_demo else 5

        doc = {
            "location": loc,
            "level": level,
            "probability": prob,
            "lead_time": alert_data.get("lead_time", "+30m Projection"),
            "headline": alert_data.get("headline", "High thunderstorm risk detected."),
            "explanation": alert_data.get("explanation", "Critical convective instability observed."),
            "timestamp_display": now_ist.strftime("%I:%M:%S %p IST"),
            "created_at": now_utc,
            "expires_at": now_utc + datetime.timedelta(minutes=ttl_minutes),
            "reported_by_id": str(reported_by_id) if reported_by_id else "System",
            "reported_by_name": reported_by_name or "Meteorological Telemetry",
            "is_active": True,
            "is_demo": is_demo
        }

        # If an alert for this location and level is already active, update it
        recent = col.find_one({
            "location": loc,
            "level": level,
            "is_active": True,
            "expires_at": {"$gte": now_utc}
        }, sort=[("created_at", pymongo.DESCENDING)])

        if recent:
            col.update_one({"_id": recent["_id"]}, {"$set": doc})
            return str(recent["_id"])

        res = col.insert_one(doc)
        return str(res.inserted_id)
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to register global thunderstorm alert: {e}")
        return None


def deactivate_all_active_alerts() -> int:
    """Deactivates all active alerts in MongoDB."""
    try:
        col = get_active_alerts_collection()
        res = col.update_many({"is_active": True}, {"$set": {"is_active": False}})
        return res.modified_count
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to deactivate alerts: {e}")
        return 0


def get_latest_global_thunderstorm_alert() -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent active global thunderstorm alert if valid and unexpired.
    Only returns fresh alerts issued within the last 3 minutes.
    """
    try:
        col = get_active_alerts_collection()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        fresh_cutoff = now_utc - datetime.timedelta(minutes=3)
        
        # Auto-deactivate expired alerts
        col.update_many({"is_active": True, "expires_at": {"$lt": now_utc}}, {"$set": {"is_active": False}})
        
        doc = col.find_one(
            {
                "is_active": True,
                "expires_at": {"$gte": now_utc},
                "created_at": {"$gte": fresh_cutoff}
            },
            sort=[("created_at", pymongo.DESCENDING)]
        )
        if doc:
            doc["id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc and isinstance(doc["created_at"], datetime.datetime):
                dt_c = doc["created_at"]
                if dt_c.tzinfo is None:
                    dt_c = dt_c.replace(tzinfo=datetime.timezone.utc)
                doc["created_at"] = dt_c.isoformat().replace("+00:00", "Z")
                doc["created_at_epoch_ms"] = int(dt_c.timestamp() * 1000)
            if "expires_at" in doc and isinstance(doc["expires_at"], datetime.datetime):
                dt_e = doc["expires_at"]
                if dt_e.tzinfo is None:
                    dt_e = dt_e.replace(tzinfo=datetime.timezone.utc)
                doc["expires_at"] = dt_e.isoformat().replace("+00:00", "Z")
            return doc
        return None
    except Exception as e:
        print(f"[MongoDB WARNING] Failed to fetch latest active alert: {e}")
        return None
