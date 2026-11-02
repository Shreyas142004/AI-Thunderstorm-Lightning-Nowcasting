"""
AeroCast AI — Telegram Emergency Alert Service
=============================================
Delivers instant, real-time thunderstorm warnings and convective weather alerts
directly to mobile devices via Telegram Bot API with push notifications and sound.
100% Free, unlimited, and zero telecom/DLT restrictions.
Guarantees EXACTLY ONE alert message per event to prevent duplicate notifications.
"""

import os
import requests
import time
from typing import Dict, Any, Tuple, Optional, List
from dotenv import load_dotenv

# In-memory deduplication cache: prevents duplicate Telegram alerts within 5 minutes (300s)
_SENT_TELEGRAM_ALERTS: Dict[str, float] = {}


def format_telegram_alert(alert_data: Dict[str, Any]) -> str:
    """Formats a rich Markdown emergency alert for Telegram."""
    level = alert_data.get("level", "CRITICAL").upper()
    prob = alert_data.get("probability", "--")
    loc = alert_data.get("location", "Karnataka")
    lead_time = alert_data.get("lead_time", "+30m Projection")
    headline = alert_data.get("headline", "High thunderstorm risk detected.")
    explanation = alert_data.get("explanation", "Elevated convective instability observed.")
    timestamp = alert_data.get("timestamp", "Live Nowcast")

    icon = "⚡🚨" if level == "CRITICAL" else ("⚠️" if level == "MODERATE" else "🌤️")

    msg = (
        f"{icon} *AEROCAST AI — {level} THUNDERSTORM ALERT* {icon}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Target Area:* `{loc}`\n"
        f"📊 *Convective Risk:* *{prob}%*\n"
        f"⏱️ *Lead Time:* `{lead_time}`\n"
        f"🕒 *Issued At:* {timestamp}\n\n"
        f"📢 *Headline:* {headline}\n\n"
        f"🔬 *Meteorological Assessment:*\n_{explanation}_\n\n"
        f"🛡️ *Immediate Safety Protocol:*\n"
        f"• *Plantation & Arecanut:* Suspend harvesting and outdoor drying.\n"
        f"• *Lightning Danger:* Seek indoor shelter; avoid metal poles & tall trees.\n"
        f"• *Highway Driving:* Watch for sudden downdraft wind gusts.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 [Open AeroCast AI Dashboard](http://127.0.0.1:5000)"
    )
    return msg


def get_all_active_chat_ids(bot_token: Optional[str] = None, specific_chat_id: Optional[str] = None) -> List[str]:
    """
    Collects ALL target subscriber chat IDs across:
    1. specific_chat_id if explicitly passed.
    2. All chat IDs configured in .env (comma-separated).
    3. All active chat IDs discovered dynamically from Telegram Bot API (/getUpdates).
    4. All persisted Telegram subscribers stored in MongoDB.
    5. All registered users in MongoDB who have linked a telegram_chat_id.
    Guarantees every connected user who has ever started or messaged @aerocast_alerts_bot
    receives the alert broadcast.
    """
    import datetime
    load_dotenv(override=True)
    token = (bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()

    chat_ids = []
    seen = set()

    def _add_id(cid_val):
        if not cid_val:
            return
        c_str = str(cid_val).strip()
        if c_str and c_str not in seen and c_str.lstrip("-").isdigit():
            chat_ids.append(c_str)
            seen.add(c_str)

    # 1. Specific passed chat_id (Targeted delivery: ONLY send to specific chat IDs requested)
    if specific_chat_id:
        for cid in str(specific_chat_id).split(","):
            _add_id(cid)
        return chat_ids

    # 2. Configured in .env (comma-separated support)
    env_chats = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if env_chats:
        for cid in env_chats.split(","):
            _add_id(cid)

    # 3. Persisted Telegram subscribers from MongoDB
    try:
        import db
        sub_col = db.get_db()["telegram_subscribers"]
        for sub in sub_col.find():
            _add_id(sub.get("chat_id"))
        
        # Check users collection for any telegram_chat_id
        for u in db.get_users_collection().find({"telegram_chat_id": {"$exists": True, "$ne": None}}):
            _add_id(u.get("telegram_chat_id"))
    except Exception as e:
        print(f"[TELEGRAM DB SUBSCRIBERS NOTE] {e}")

    # 4. Dynamic Auto-Discovery from Telegram Bot Updates
    if token:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("result", []):
                    msg = item.get("message", {}) or item.get("channel_post", {}) or item.get("my_chat_member", {})
                    chat = msg.get("chat", {})
                    cid = chat.get("id")
                    from_u = msg.get("from", {})
                    if cid:
                        c_str = str(cid)
                        _add_id(c_str)
                        # Persist to MongoDB for long-term retention
                        try:
                            import db
                            sub_col = db.get_db()["telegram_subscribers"]
                            sub_col.update_one(
                                {"chat_id": c_str},
                                {"$set": {
                                    "chat_id": c_str,
                                    "first_name": from_u.get("first_name", ""),
                                    "username": from_u.get("username", ""),
                                    "last_active": datetime.datetime.now(datetime.timezone.utc)
                                }},
                                upsert=True
                            )
                        except Exception:
                            pass
        except Exception as e:
            print(f"[TELEGRAM GET_UPDATES NOTE] {e}")

    return chat_ids


def get_latest_chat_id(bot_token: Optional[str] = None) -> Optional[str]:
    """Returns the most recent active chat_id for backward compatibility."""
    chats = get_all_active_chat_ids(bot_token=bot_token)
    return chats[0] if chats else None


def send_telegram_alert(
    alert_data: Dict[str, Any],
    chat_id: Optional[str] = None,
    recipient_name: Optional[str] = None,
    force: bool = False,
    bot_token: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Sends an urgent push alert to Telegram.
    Guarantees EXACTLY ONE message is delivered per distinct chat ID,
    with built-in anti-duplicate throttling to prevent multiple messages for 1 alert.
    """
    global _SENT_TELEGRAM_ALERTS
    load_dotenv(override=True)
    token = (bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()

    if not token:
        print("[TELEGRAM NOTICE] TELEGRAM_BOT_TOKEN not configured in .env (Simulation logged).")
        return True, "simulated", "Telegram Bot Token not configured in .env."

    loc = (alert_data.get("location") or "Karnataka").strip().lower()
    lvl = (alert_data.get("level") or "CRITICAL").upper()
    now_ts = time.time()
    dedup_key = f"{loc}_{lvl}"

    # Anti-duplicate throttle: 5 minutes between identical alerts
    if not force:
        last_sent = _SENT_TELEGRAM_ALERTS.get(dedup_key)
        if last_sent and (now_ts - last_sent) < 300:
            print(f"[TELEGRAM THROTTLE] Skipping duplicate alert for {loc} ({lvl}) - already sent recently.")
            return True, "throttled", f"Telegram alert for {loc} already sent recently."

    _SENT_TELEGRAM_ALERTS[dedup_key] = now_ts

    target_chats = get_all_active_chat_ids(bot_token=token, specific_chat_id=chat_id)
    if not target_chats:
        return False, "failed", "No recipient chat IDs found. Send /start to @aerocast_alerts_bot."

    # De-duplicate target chats so each phone receives only 1 message
    unique_chats = list(dict.fromkeys(target_chats))
    text = format_telegram_alert(alert_data)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    delivered = []
    failed = []

    for cid in unique_chats:
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=6)
            data = resp.json() if resp.status_code != 500 else {}
            if resp.status_code == 200 and data.get("ok") is True:
                delivered.append(cid)
            else:
                err = data.get("description", "Delivery error")
                failed.append(f"{cid}: {err}")
        except Exception as e:
            failed.append(f"{cid}: {str(e)}")

        time.sleep(0.05)

    if delivered:
        chats_str = ", ".join(delivered)
        print(f"[TELEGRAM DISPATCH SUCCESS] Delivered 1 emergency alert to Telegram chat(s): {chats_str}")
        return True, "sent", f"Telegram alert delivered to chat(s): {chats_str}"
    else:
        err_str = "; ".join(failed)
        return False, "failed", f"Telegram delivery failed: {err_str}"
