"""
AeroCast AI — Email Alert Dispatch Service
==========================================
Delivers structured convective thunderstorm warnings and synoptic advisories
to registered Karnataka citizens, farmers, and evaluators via SMTP (e.g. Gmail / Outlook).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv


def build_email_html(recipient_name: str, alert_data: Dict[str, Any]) -> str:
    """Generates a responsive HTML email bulletin for thunderstorm alerts."""
    level = alert_data.get("level", "CRITICAL").upper()
    prob = alert_data.get("probability", "--")
    loc = alert_data.get("location", "Karnataka")
    lead_time = alert_data.get("lead_time", "+30m Projection")
    headline = alert_data.get("headline", "High thunderstorm risk detected.")
    explanation = alert_data.get("explanation", "Critical convective atmospheric instability observed.")
    timestamp = alert_data.get("timestamp", "Live Nowcast")

    accent_color = "#c62828" if level == "CRITICAL" else ("#e65100" if level == "MODERATE" else "#2e7d32")
    accent_bg = "rgba(200, 109, 81, 0.12)" if level == "CRITICAL" else ("rgba(201, 136, 56, 0.12)" if level == "MODERATE" else "rgba(94, 140, 104, 0.12)")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AeroCast AI — Convective Weather Warning</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f3ee; color: #1f1b18; margin: 0; padding: 24px; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 18px; border: 1px solid #e5ded4; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.06); }}
    .header {{ background: #1f1b18; color: #ffffff; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; }}
    .brand {{ font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; color: #ffffff; }}
    .badge {{ background: #c98838; color: #ffffff; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }}
    .content {{ padding: 28px 24px; }}
    .severity-banner {{ background: {accent_bg}; border-left: 4px solid {accent_color}; padding: 14px 18px; border-radius: 8px; margin-bottom: 22px; }}
    .severity-title {{ color: {accent_color}; font-weight: 800; font-size: 0.92rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 4px; }}
    .headline {{ font-size: 1.15rem; font-weight: 800; line-height: 1.4; color: #1f1b18; margin: 0; }}
    .metrics-grid {{ display: table; width: 100%; margin: 20px 0; background: #faf7f2; border: 1px solid #eee8df; border-radius: 12px; }}
    .metric-col {{ display: table-cell; width: 33.33%; padding: 14px 16px; text-align: center; border-right: 1px solid #eee8df; }}
    .metric-col:last-child {{ border-right: none; }}
    .metric-label {{ font-size: 0.72rem; color: #82786f; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }}
    .metric-value {{ font-size: 1.15rem; font-weight: 800; color: #1f1b18; }}
    .explanation {{ font-size: 0.92rem; line-height: 1.6; color: #4b443d; background: #faf8f5; padding: 14px 18px; border-radius: 10px; margin-bottom: 22px; }}
    .safety-box {{ background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px; padding: 16px 20px; margin-bottom: 22px; }}
    .safety-title {{ font-size: 0.88rem; font-weight: 800; color: #f57f17; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .safety-list {{ margin: 0; padding-left: 18px; font-size: 0.86rem; color: #4b443d; line-height: 1.5; }}
    .footer {{ background: #faf7f2; padding: 16px 24px; font-size: 0.75rem; color: #82786f; text-align: center; border-top: 1px solid #eee8df; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="brand">AeroCast AI</div>
      <div class="badge">Karnataka Convective Weather Warning</div>
    </div>
    <div class="content">
      <div class="severity-banner">
        <div class="severity-title">{level} THUNDERSTORM ALERT</div>
        <h2 class="headline">{headline}</h2>
      </div>

      <p style="margin-top: 0; font-size: 0.95rem; color: #1f1b18;">
        Dear <strong>{recipient_name}</strong>, atmospheric convective instability has reached alert threshold across your monitoring area.
      </p>

      <div class="metrics-grid">
        <div class="metric-col">
          <div class="metric-label">Predicted Risk</div>
          <div class="metric-value" style="color: {accent_color};">{prob}%</div>
        </div>
        <div class="metric-col">
          <div class="metric-label">Affected Area</div>
          <div class="metric-value">{loc}</div>
        </div>
        <div class="metric-col">
          <div class="metric-label">Lead Time</div>
          <div class="metric-value">{lead_time}</div>
        </div>
      </div>

      <div class="explanation">
        <strong>Meteorological Assessment:</strong> {explanation}
      </div>

      <div class="safety-box">
        <div class="safety-title">⚠️ Priority Advisory Protocol</div>
        <ul class="safety-list">
          <li><strong>Arecanut & Plantation Growers:</strong> Suspend open-field harvesting, spraying, and copra drying immediately. Secure plastic covers.</li>
          <li><strong>Lightning Hazard:</strong> Stay indoors. Avoid seeking shelter under isolated tall trees, metal utility poles, or open ridge lines.</li>
          <li><strong>Highway Travel:</strong> Sudden downdraft wind gusts and slick road surfaces may reduce traction. Drive cautiously.</li>
        </ul>
      </div>

      <p style="font-size: 0.82rem; color: #82786f; margin: 0;">
        Continuous S-band Doppler radar telemetry and 62-feature GBDT model updates are streaming at 
        <a href="http://127.0.0.1:5000" style="color: #c86d51; font-weight: 700; text-decoration: none;">AeroCast AI Dashboard</a>.
      </p>
    </div>
    <div class="footer">
      Issued at {timestamp} &bull; AeroCast AI Convective Weather Nowcasting System &bull; Karnataka, India
    </div>
  </div>
</body>
</html>"""


def get_smtp_connection() -> Optional[smtplib.SMTP]:
    """Establishes an active SMTP TLS connection for batch sending."""
    load_dotenv(override=True)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()

    if not (smtp_user and smtp_pass and "your_" not in smtp_user and "your_" not in smtp_pass):
        return None

    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        return server
    except Exception as e:
        print(f"[SMTP CONNECTION ERROR] {e}")
        return None


def send_email_alert(
    recipient_email: str,
    recipient_name: str,
    alert_data: Dict[str, Any],
    server: Optional[smtplib.SMTP] = None
) -> Tuple[bool, str, str]:
    """
    Dispatches a convective thunderstorm warning email.
    Can reuse an existing `server` connection for high throughput batch delivery.
    """
    recipient_email = (recipient_email or "").strip()
    if not recipient_email or "@" not in recipient_email:
        return False, "failed", f"Invalid recipient email: {recipient_email}"

    level = alert_data.get("level", "CRITICAL")
    loc = alert_data.get("location", "Karnataka")
    prob = alert_data.get("probability", "--")
    subject = f"AeroCast AI Alert: {level} Thunderstorm Warning for {loc} ({prob}% Risk)"

    html_content = build_email_html(recipient_name or "Citizen", alert_data)
    text_content = (
        f"AEROCAST AI THUNDERSTORM ALERT\n"
        f"Level: {level}\n"
        f"Location: {loc}\n"
        f"Risk: {prob}%\n"
        f"Lead Time: {alert_data.get('lead_time', '+30m')}\n\n"
        f"{alert_data.get('headline')}\n\n"
        f"Details: {alert_data.get('explanation')}\n\n"
        f"Issued at {alert_data.get('timestamp')}"
    )
    load_dotenv(override=True)
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "AeroCast AI Weather Warning")

    is_live_configured = bool(smtp_user and smtp_pass and "your_" not in smtp_user and "your_" not in smtp_pass)

    if not is_live_configured:
        safe_subject = subject.encode('ascii', errors='replace').decode('ascii')
        print(f"[EMAIL DISPATCH SIMULATION] To: {recipient_name} <{recipient_email}> | Subject: {safe_subject}")
        return True, "simulated", f"Simulated email prepared and logged for {recipient_email}."

    # For synthetic demo / test users with non-routable domains, log realistically without choking Gmail SMTP
    is_dummy_domain = any(recipient_email.lower().endswith(dom) for dom in ["@aerocast.ai", "@example.com", "@test.com"])
    if is_dummy_domain:
        print(f"[EMAIL DISPATCH SIMULATION] Demo account <{recipient_email}> logged.")
        return True, "simulated", f"Simulated delivery logged for demo account {recipient_email}."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp_from_name} <{smtp_user}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Reuse provided open connection
    if server:
        try:
            server.sendmail(smtp_user, [recipient_email], msg.as_string())
            print(f"[EMAIL DISPATCH SUCCESS] Delivered email to {recipient_email}")
            return True, "sent", f"Email alert successfully sent to {recipient_email}."
        except Exception as e:
            print(f"[EMAIL DISPATCH RETRY] Single send retry for {recipient_email}: {e}")

    # Fallback to single standalone connection
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, [recipient_email], msg.as_string())

        print(f"[EMAIL DISPATCH SUCCESS] Delivered email to {recipient_email}")
        return True, "sent", f"Email alert successfully sent to {recipient_email}."
    except Exception as e:
        print(f"[EMAIL DISPATCH ERROR] Failed to send email to {recipient_email}: {e}")
        return False, "failed", f"SMTP delivery failed: {str(e)}"


def send_otp_email(
    recipient_email: str,
    recipient_name: str,
    otp_code: str,
    purpose: str = "Verification"
) -> Tuple[bool, str, str]:
    """
    Sends a 6-digit OTP code to the recipient's email address using SMTP (Gmail).
    Returns (success_boolean, status, message).
    """
    recipient_email = (recipient_email or "").strip()
    if not recipient_email or "@" not in recipient_email:
        return False, "failed", f"Invalid recipient email: {recipient_email}"

    subject = f"AeroCast AI — Your Verification Code: {otp_code} ({purpose})"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AeroCast AI — Verification Code</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f3ee; color: #1f1b18; margin: 0; padding: 24px; }}
    .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 18px; border: 1px solid #e5ded4; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.06); }}
    .header {{ background: #1f1b18; color: #ffffff; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; }}
    .brand {{ font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; color: #ffffff; }}
    .badge {{ background: #c86d51; color: #ffffff; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }}
    .content {{ padding: 28px 24px; text-align: center; }}
    .headline {{ font-size: 1.2rem; font-weight: 800; color: #1f1b18; margin: 0 0 12px; }}
    .subtext {{ font-size: 0.92rem; color: #4b443d; line-height: 1.5; margin: 0 0 24px; }}
    .otp-box {{ background: #faf4f0; border: 2px dashed #c86d51; border-radius: 14px; padding: 18px 24px; display: inline-block; margin-bottom: 24px; }}
    .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #c86d51; font-family: 'Space Grotesk', monospace; margin: 0; }}
    .notice {{ background: #fff8e1; border: 1px solid #ffe082; border-radius: 10px; padding: 12px 16px; font-size: 0.82rem; color: #795548; line-height: 1.5; text-align: left; margin-bottom: 20px; }}
    .footer {{ background: #faf7f2; padding: 14px 24px; font-size: 0.74rem; color: #82786f; text-align: center; border-top: 1px solid #eee8df; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="brand">⚡ AeroCast AI</div>
      <div class="badge">{purpose}</div>
    </div>
    <div class="content">
      <h2 class="headline">One-Time Verification Code</h2>
      <p class="subtext">
        Hello <strong>{recipient_name}</strong>, use the 6-digit code below to complete your {purpose.lower()}.
      </p>

      <div class="otp-box">
        <div class="otp-code">{otp_code}</div>
      </div>

      <div class="notice">
        <strong>Security Notice:</strong> This OTP is valid for <strong>10 minutes</strong>. Do not disclose this code to anyone. If you did not initiate this request, you can safely disregard this email.
      </div>
    </div>
    <div class="footer">
      AeroCast AI Convective Weather & Nowcasting System &bull; Karnataka, India
    </div>
  </div>
</body>
</html>"""

    text_content = f"AEROCAST AI VERIFICATION CODE\nPurpose: {purpose}\n\nYour 6-digit OTP code is: {otp_code}\n\nThis code expires in 10 minutes. Do not share this code with anyone."
    load_dotenv(override=True)
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "AeroCast AI Security")

    is_live_configured = bool(smtp_user and smtp_pass and "your_" not in smtp_user and "your_" not in smtp_pass)

    if not is_live_configured:
        print(f"[OTP EMAIL SIMULATION] To: {recipient_email} | OTP: {otp_code} ({purpose})")
        return True, "simulated", f"Simulated OTP {otp_code} logged for {recipient_email}."

    # For synthetic demo / test users with non-routable domains, log realistically without choking Gmail SMTP
    is_dummy_domain = any(recipient_email.lower().endswith(dom) for dom in ["@aerocast.ai", "@example.com", "@test.com"])
    if is_dummy_domain:
        print(f"[OTP EMAIL SIMULATION] Demo account <{recipient_email}> logged with OTP: {otp_code} ({purpose})")
        return True, "simulated", f"Simulated OTP {otp_code} logged for demo account {recipient_email}."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp_from_name} <{smtp_user}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, [recipient_email], msg.as_string())

        print(f"[OTP EMAIL SUCCESS] Delivered OTP code to {recipient_email}")
        return True, "sent", f"Verification code successfully sent to {recipient_email}."
    except Exception as e:
        print(f"[OTP EMAIL ERROR] Failed to send OTP to {recipient_email}: {e}")
        return False, "failed", f"Failed to send email OTP: {str(e)}"
