from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.email_service import send_via_zoho, send_via_smtp
from api.services.storage_service import upload_pdf, get_signed_url

router = APIRouter()

_LINK_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days


class SendEmailRequest(BaseModel):
    method: str = "smtp"  # "smtp" | "zohoapi"


@router.post("/send/{enrollee_id}")
async def send_email(
    enrollee_id: str,
    body: SendEmailRequest,
    _: str = Depends(require_api_key),
) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT e.name, e.email, rm.pdf_path FROM enrollees e "
        "JOIN report_meta rm USING (enrollee_id) WHERE e.enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Enrollee or PDF not found")
    name, email, pdf_path = result
    if not email:
        raise HTTPException(status_code=422, detail="No email address on record")
    if not pdf_path:
        raise HTTPException(status_code=422, detail="PDF not generated yet")

    if body.method == "zohoapi":
        ok = send_via_zoho(email, name, pdf_path)
    else:
        ok = send_via_smtp(email, name, pdf_path)

    if ok:
        conn.execute(
            "UPDATE report_meta SET email_sent = TRUE WHERE enrollee_id = ?",
            [enrollee_id],
        )
    return {"enrollee_id": enrollee_id, "sent": ok, "method": body.method}


@router.post("/backblaze/{enrollee_id}")
async def backblaze_link(
    enrollee_id: str,
    _: str = Depends(require_api_key),
) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT e.company_name, rm.pdf_path, rm.b2_url "
        "FROM enrollees e "
        "JOIN report_meta rm USING (enrollee_id) "
        "WHERE e.enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Enrollee or PDF not found")
    company_name, pdf_path, stored_key = result
    if not pdf_path:
        raise HTTPException(status_code=422, detail="PDF not generated yet — generate it first")

    # Upload only once; reuse the stored object key on repeat calls
    if stored_key:
        key = stored_key
    else:
        key = upload_pdf(pdf_path, enrollee_id, company_name or "unknown")
        conn.execute(
            "UPDATE report_meta SET b2_url = ? WHERE enrollee_id = ?",
            [key, enrollee_id],
        )

    download_url = get_signed_url(key, expiry_seconds=_LINK_EXPIRY_SECONDS)
    expires_at = (
        datetime.utcnow() + timedelta(seconds=_LINK_EXPIRY_SECONDS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "enrollee_id": enrollee_id,
        "download_url": download_url,
        "expires_at": expires_at,
    }


@router.post("/bulk/{batch_id}")
async def bulk_send(
    batch_id: str,
    method: str = "smtp",
    _: str = Depends(require_api_key),
) -> dict:
    from workers.tasks import bulk_email_task
    task = bulk_email_task.delay(batch_id, method)
    return {"job_id": task.id, "status": "queued"}


@router.get("/methods")
async def list_methods(_: str = Depends(require_api_key)) -> dict:
    return {"methods": ["smtp", "zohoapi", "backblaze"]}


@router.get("/zoho-health")
async def zoho_health(_: str = Depends(require_api_key)) -> dict:
    """Verify Zoho OAuth credentials are valid (token refresh + account probe). No email sent."""
    import httpx
    from api.core.config import get_settings
    s = get_settings()
    tr = httpx.post(
        "https://accounts.zoho.com/oauth/v2/token",
        data={
            "refresh_token": s.zoho_refresh_token,
            "client_id": s.zoho_client_id,
            "client_secret": s.zoho_client_secret,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    if tr.status_code != 200 or "access_token" not in tr.json():
        return {"ok": False, "step": "token_refresh", "status": tr.status_code}
    token = tr.json()["access_token"]
    ar = httpx.get(
        f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=15,
    )
    return {
        "ok": ar.status_code == 200,
        "account_probe_status": ar.status_code,
        "from_email": s.zoho_from_email,
    }
