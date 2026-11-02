"""
AeroCast AI Notification Package
"""
from notifications.email_service import send_email_alert, send_otp_email
from notifications.sms_service import send_sms_alert
from notifications.telegram_service import send_telegram_alert, get_latest_chat_id
from notifications.dispatcher import dispatch_thunderstorm_alerts, dispatch_thunderstorm_alerts_async, get_notification_history

__all__ = [
    "send_email_alert",
    "send_otp_email",
    "send_sms_alert",
    "send_telegram_alert",
    "get_latest_chat_id",
    "dispatch_thunderstorm_alerts",
    "dispatch_thunderstorm_alerts_async",
    "get_notification_history"
]

