"""
AeroCast AI — Alert Dispatch Coordinator
========================================
Coordinates targeting of registered users from MongoDB based on locality,
executes parallel or sequential Email & SMS transmissions, and logs delivery receipts.
"""

import datetime
import re
from typing import Dict, Any, List, Optional
from db import get_db, get_users_collection, register_global_thunderstorm_alert
from notifications.email_service import send_email_alert, get_smtp_connection
from notifications.sms_service import send_sms_alert, reset_sms_cache
from notifications.telegram_service import send_telegram_alert


# Karnataka locality name aliases & normalizations
ALIASES = {
    "bajipe": "bajpe",
    "mangaluru": "mangalore", "mangalore": "mangalore",
    "bengaluru": "bangalore", "bangalore": "bangalore",
    "hubballi": "hubli", "hubli": "hubli",
    "mysuru": "mysore", "mysore": "mysore",
    "belagavi": "belgaum", "belgaum": "belgaum",
    "kalaburagi": "gulbarga", "gulbarga": "gulbarga",
    "shivamogga": "shimoga", "shimoga": "shimoga",
    "vijayapura": "bijapur", "bijapur": "bijapur",
    "ballari": "bellary", "bellary": "bellary",
}

STOPWORDS = {
    "urban", "rural", "north", "south", "east", "west", "city", "district", "dist",
    "taluk", "dk", "karnataka", "india", "state", "dakshina", "kannada", "uttara"
}


def extract_primary_town(text: Optional[str]) -> str:
    """Extracts normalized town / taluk name (e.g. 'Puttur', 'Mangaluru', 'Bengaluru')."""
    if not text:
        return ""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", parts[0].lower()).strip()
    words = [w for w in cleaned.split() if w not in STOPWORDS]
    if words:
        canonical = [ALIASES.get(w, w) for w in words]
        return " ".join(canonical)
    return ALIASES.get(cleaned, cleaned)


def is_locality_match(user_locality: Optional[str], alert_location: Optional[str]) -> bool:
    """
    Checks if a user's registered monitoring locality matches the storm alert location.
    Ensures that an alert in Puttur is delivered ONLY to users from Puttur,
    and NOT to users from Mangaluru, Bengaluru, Hassan, or other regions.
    """
    if not user_locality or not alert_location:
        return False

    alert_clean = alert_location.strip().lower()
    if alert_clean in ["karnataka", "statewide", "all"]:
        return True

    u_town = extract_primary_town(user_locality)
    a_town = extract_primary_town(alert_location)
    if not u_town or not a_town:
        return False

    return u_town == a_town or u_town in a_town or a_town in u_town


def get_target_users(location: str = None, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Finds registered recipients in MongoDB:
    ONLY users whose registered locality matches the storm alert location receive the alert.
    Users residing in other cities/taluks do NOT receive this alert.
    """
    col = get_users_collection()
    recipients = []
    seen_ids = set()

    # 1. Prioritize currently active user if their locality matches
    if current_user_id:
        try:
            # pyrefly: ignore[missing-import]
            from bson import ObjectId
            user = col.find_one({"_id": ObjectId(current_user_id)})
            if user:
                u_loc = user.get("locality") or ""
                if not location or is_locality_match(u_loc, location):
                    recipients.append(user)
                    seen_ids.add(str(user["_id"]))
        except Exception:
            pass

    # 2. Add all registered users from MongoDB whose registered locality matches the alert location
    all_users = list(col.find())
    for u in all_users:
        uid = str(u["_id"])
        if uid in seen_ids:
            continue
        u_loc = u.get("locality") or ""
        if not location or is_locality_match(u_loc, location):
            recipients.append(u)
            seen_ids.add(uid)

    return recipients


_DISPATCH_THROTTLE = {}


def dispatch_thunderstorm_alerts_async(
    alert_data: Dict[str, Any],
    target_user_id: Optional[str] = None,
    channels: Optional[List[str]] = None,
    force: bool = False
):
    """Fires alert dispatch in a background thread without blocking the HTTP request."""
    import threading
    t = threading.Thread(
        target=dispatch_thunderstorm_alerts,
        args=(alert_data, target_user_id, channels, force),
        daemon=False
    )
    t.start()
    return t


def dispatch_thunderstorm_alerts(
    alert_data: Dict[str, Any],
    target_user_id: Optional[str] = None,
    channels: Optional[List[str]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Dispatches Email and SMS alerts to target users and saves dispatch history.
    channels defaults to ['email', 'sms'].
    """
    global _DISPATCH_THROTTLE

    location = (alert_data.get("location") or "Karnataka").strip()
    level = (alert_data.get("level") or "CRITICAL").upper()

    now = datetime.datetime.now(datetime.timezone.utc)
    throttle_key = (location.lower(), level)

    if not force:
        last_sent = _DISPATCH_THROTTLE.get(throttle_key)
        if last_sent and (now - last_sent).total_seconds() < 600:
            print(f"[AUTO-ALERT THROTTLED] Alert for {location} ({level}) was already sent recently. Skipping duplicate.")
            return {
                "success": True,
                "throttled": True,
                "message": f"Alert already dispatched for {location} recently.",
                "recipients_count": 0,
                "dispatches": []
            }

    _DISPATCH_THROTTLE[throttle_key] = now

    # Register in active global alerts database so all connected client dashboards show the warning
    try:
        register_global_thunderstorm_alert(alert_data, reported_by_id=target_user_id)
    except Exception as e_reg:
        print(f"[ACTIVE ALERT REGISTRATION WARNING] {e_reg}")

    if channels is None:
        channels = ["email", "sms", "telegram"]
    reset_sms_cache()

    recipients = get_target_users(location, target_user_id)
    print(f"[AEROCAST LOCALITY DISPATCH] Targeting {len(recipients)} registered user(s) matching '{location}'")

    if not recipients:
        print(f"[AEROCAST LOCALITY DISPATCH] No registered users found for '{location}'. Alert will NOT be sent to users in other areas.")
        return {
            "success": True,
            "message": f"No registered users found in {location} to alert.",
            "recipients_count": 0,
            "dispatches": []
        }

    db = get_db()
    notif_col = db["notifications"]

    dispatches = []
    email_success_count = 0
    sms_success_count = 0
    has_live_delivery = False

    # Establish shared SMTP connection for the batch (prevents connection thrashing)
    smtp_conn = None
    if "email" in channels:
        try:
            smtp_conn = get_smtp_connection()
        except Exception as e:
            print(f"[SMTP BATCH NOTE] Standalone fallback: {e}")
            smtp_conn = None

    # Dispatch Telegram push alert ONLY to matching users in this locality who have linked Telegram
    telegram_status = "skipped"
    telegram_note = ""
    matching_chat_ids = [str(u["telegram_chat_id"]).strip() for u in recipients if u.get("telegram_chat_id") and str(u["telegram_chat_id"]).strip().lstrip("-").isdigit()]

    if ("telegram" in channels or "sms" in channels) and matching_chat_ids:
        try:
            t_ok, t_stat, t_msg = send_telegram_alert(alert_data, chat_id=",".join(matching_chat_ids), force=force)
            telegram_status = t_stat
            telegram_note = t_msg
            if t_stat == "sent":
                has_live_delivery = True
        except Exception as e:
            telegram_status = "failed"
            telegram_note = str(e)
    elif not matching_chat_ids:
        telegram_status = "skipped"
        telegram_note = f"No Telegram chat IDs registered for users in {location}."

    try:
        for user in recipients:
            username = user.get("username", "Citizen")
            email = user.get("email", "")
            mobile = user.get("mobile", "")
            locality = user.get("locality", location)

            email_status = "skipped"
            email_note = ""
            sms_status = "skipped"
            sms_note = ""

            # Dispatch Email
            if "email" in channels and email:
                e_ok, e_stat, e_msg = send_email_alert(email, username, alert_data, server=smtp_conn)
                email_status = e_stat
                email_note = e_msg
                if e_ok:
                    email_success_count += 1
                if e_stat == "sent":
                    has_live_delivery = True

            # Dispatch SMS
            if "sms" in channels and mobile:
                s_ok, s_stat, s_msg = send_sms_alert(mobile, username, alert_data)
                sms_status = s_stat
                sms_note = s_msg
                if s_ok:
                    sms_success_count += 1
                if s_stat == "sent":
                    has_live_delivery = True

            # Telegram alert already broadcasted once for this event

            record = {
                "user_id": str(user["_id"]),
                "username": username,
                "email": email,
                "mobile": mobile,
                "locality": locality,
                "alert_location": location,
                "alert_level": alert_data.get("level", "CRITICAL"),
                "probability": alert_data.get("probability"),
                "lead_time": alert_data.get("lead_time", "+30m"),
                "headline": alert_data.get("headline"),
                "email_status": email_status,
                "email_message": email_note,
                "sms_status": sms_status,
                "sms_message": sms_note,
                "telegram_status": telegram_status,
                "telegram_message": telegram_note,
                "dispatched_at": datetime.datetime.now(datetime.timezone.utc),
                "timestamp_display": datetime.datetime.now().strftime("%I:%M:%S %p IST")
            }

            try:
                notif_col.insert_one(record)
                record["_id"] = str(record["_id"])
            except Exception as e:
                print(f"[MongoDB WARNING] Could not log notification receipt: {e}")

            dispatches.append(record)

    finally:
        if smtp_conn:
            try:
                smtp_conn.quit()
            except Exception:
                pass

    return {
        "success": True,
        "mode": "live" if has_live_delivery else "simulated",
        "recipients_count": len(recipients),
        "email_count": email_success_count,
        "sms_count": sms_success_count,
        "alert_level": alert_data.get("level", "CRITICAL"),
        "location": location,
        "dispatches": dispatches
    }


def get_notification_history(limit: int = 15) -> List[Dict[str, Any]]:
    """Returns recent alert notifications from MongoDB."""
    try:
        col = get_db()["notifications"]
        docs = list(col.find().sort("dispatched_at", -1).limit(limit))
        for d in docs:
            d["_id"] = str(d["_id"])
            if "dispatched_at" in d and isinstance(d["dispatched_at"], datetime.datetime):
                d["dispatched_at"] = d["dispatched_at"].isoformat()
        return docs
    except Exception as e:
        print(f"[MongoDB ERROR] get_notification_history failed: {e}")
        return []
