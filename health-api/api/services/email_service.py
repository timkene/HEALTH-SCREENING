from __future__ import annotations
import base64
import smtplib
import threading
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import httpx
from api.core.config import get_settings

_EMAIL_SUBJECT = "Your Clearline HMO Health Screening Report"
_EMAIL_BODY = """\
Dear {name},

Please find attached your personalised health screening report prepared by Klaire, \
your Clearline HMO health companion.

If you have any questions about your results, you can speak to one of our doctors \
through the Clearline mobile app.

Warm regards,
Clearline HMO
"""


class ZohoTokenCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(self, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.time()
            if not force_refresh and self._token and now < self._expires_at:
                return self._token
            return self._refresh()

    def _refresh(self) -> str:
        s = get_settings()
        resp = httpx.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                "refresh_token": s.zoho_refresh_token,
                "client_id": s.zoho_client_id,
                "client_secret": s.zoho_client_secret,
                "grant_type": "refresh_token",
            },
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Zoho token refresh failed: {data}")
        expires_in = int(data.get("expires_in", 3600))
        self._token = data["access_token"]
        self._expires_at = time.time() + max(60, expires_in - 300)
        return self._token


_token_cache = ZohoTokenCache()


def send_via_zoho(to_email: str, name: str, pdf_path: str) -> bool:
    import logging
    log = logging.getLogger(__name__)
    s = get_settings()
    try:
        token = _token_cache.get()
    except Exception as exc:
        log.error("Zoho token refresh failed: %s", exc)
        return False

    # Step 1: upload attachment and get token — Zoho rejects base64 inline
    with open(pdf_path, "rb") as f:
        up = httpx.post(
            f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}/messages/attachments",
            headers={"Authorization": f"Zoho-oauthtoken {token}"},
            files={"attachment": ("health_report.pdf", f, "application/pdf")},
            timeout=30,
        )
    if up.status_code != 200:
        log.error("Zoho attachment upload %s: %s", up.status_code, up.text[:500])
        return False
    up_data = up.json().get("data", {})
    attach_token = (
        up_data.get("attachmentToken")
        if isinstance(up_data, dict)
        else (up_data[0].get("attachmentToken") if up_data else None)
    )
    if not attach_token:
        log.error("Zoho attachment token missing: %s", up.text[:300])
        return False

    # Step 2: send with attachment token
    payload = {
        "fromAddress": s.zoho_from_email,
        "toAddress": to_email,
        "subject": _EMAIL_SUBJECT,
        "content": _EMAIL_BODY.format(name=name),
        "attachments": [{"attachmentToken": attach_token}],
    }
    resp = httpx.post(
        f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}/messages",
        json=payload,
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=30,
    )
    if resp.status_code != 200:
        log.error("Zoho send %s: %s", resp.status_code, resp.text[:500])
    return resp.status_code == 200


def send_via_smtp(to_email: str, name: str, pdf_path: str) -> bool:
    s = get_settings()
    msg = MIMEMultipart()
    msg["From"] = s.smtp_username
    msg["To"] = to_email
    msg["Subject"] = _EMAIL_SUBJECT
    msg.attach(MIMEText(_EMAIL_BODY.format(name=name), "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=health_report.pdf")
    msg.attach(part)

    with smtplib.SMTP(s.smtp_server, s.smtp_port) as server:
        server.starttls()
        server.login(s.smtp_username, s.smtp_password)
        server.sendmail(s.smtp_username, to_email, msg.as_string())
    return True


def send_alert_to_tele_team(enrollee_name: str, enrollee_id: str, urgency: str) -> bool:
    s = get_settings()
    subject = f"[CRITICAL] Health screening alert — {enrollee_name}"
    body = (
        f"Enrollee {enrollee_name} (ID: {enrollee_id}) has a CRITICAL health screening result.\n\n"
        f"Urgency level: {urgency}\n\n"
        "Please contact this enrollee within 24 hours via the telemedicine system."
    )
    try:
        with smtplib.SMTP(s.smtp_server, s.smtp_port) as server:
            server.starttls()
            server.login(s.smtp_username, s.smtp_password)
            msg = MIMEText(body)
            msg["From"] = s.smtp_username
            msg["To"] = s.tele_alert_email
            msg["Subject"] = subject
            server.sendmail(s.smtp_username, s.tele_alert_email, msg.as_string())
        return True
    except Exception:
        return False
