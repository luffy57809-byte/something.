import datetime
import os
import threading

import requests

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
DAILY_LIMIT = 200  # stay under the free plan's daily cap

_lock = threading.Lock()
_sent_today = {"day": None, "count": 0}


def email_enabled() -> bool:
    return bool(os.environ.get("BREVO_API_KEY") and os.environ.get("BREVO_SENDER_EMAIL"))


def _under_daily_limit() -> bool:
    today = datetime.datetime.utcnow().date()
    with _lock:
        if _sent_today["day"] != today:
            _sent_today["day"] = today
            _sent_today["count"] = 0
        if _sent_today["count"] >= DAILY_LIMIT:
            return False
        _sent_today["count"] += 1
        return True


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send one transactional email through Brevo. Never raises."""
    if not email_enabled():
        print(f"[email disabled] not sending '{subject}'")
        return False
    if not _under_daily_limit():
        print("[email] daily limit reached, not sending")
        return False
    try:
        resp = requests.post(
            BREVO_URL,
            headers={
                "api-key": os.environ["BREVO_API_KEY"],
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={
                "sender": {"name": "Chesslytic", "email": os.environ["BREVO_SENDER_EMAIL"]},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content,
            },
            timeout=10,
        )
        if resp.status_code >= 300:
            print(f"[email] send failed: HTTP {resp.status_code} {resp.text[:200]}")
            return False
        return True
    except requests.RequestException as e:
        print(f"[email] send error: {e}")
        return False
