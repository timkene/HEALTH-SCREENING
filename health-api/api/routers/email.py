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


@router.get("/zoho-debug")
async def zoho_debug(_: str = Depends(require_api_key)) -> dict:
    """Temporary: test Zoho token refresh + a no-op API call to surface the real error."""
    import httpx
    from api.core.config import get_settings
    s = get_settings()
    # Step 1: token refresh
    tr = httpx.post(
        "https://accounts.zoho.com/oauth/v2/token",
        data={
            "refresh_token": s.zoho_refresh_token,
            "client_id": s.zoho_client_id,
            "client_secret": s.zoho_client_secret,
            "grant_type": "refresh_token",
        },
    )
    if tr.status_code != 200 or "access_token" not in tr.json():
        return {"step": "token_refresh", "status": tr.status_code, "body": tr.text[:400]}
    token = tr.json()["access_token"]
    # Step 2: probe the accounts endpoint (read-only, no email sent)
    ar = httpx.get(
        f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=15,
    )
    # Step 3: attempt a real send to surface the exact error
    # find any existing PDF on disk to attach
    conn = get_db()
    row = conn.execute("SELECT e.name, e.email, rm.pdf_path FROM enrollees e JOIN report_meta rm USING (enrollee_id) WHERE rm.pdf_path IS NOT NULL LIMIT 1").fetchone()
    if not row:
        return {"token_ok": True, "account_probe_status": ar.status_code, "note": "no PDF on disk to test send"}
    name, email, pdf_path = row
    # Attempt: single multipart/form-data POST with PDF attached inline
    with open(pdf_path, "rb") as f:
        sr = httpx.post(
            f"https://mail.zoho.com/api/accounts/{s.zoho_account_id}/messages",
            data={
                "fromAddress": s.zoho_from_email,
                "toAddress": email,
                "subject": "Clearline Health API — debug test",
                "content": f"Debug test send to {name}.",
                "mailFormat": "plaintext",
            },
            files={"attachment": ("report.pdf", f, "application/pdf")},
            headers={"Authorization": f"Zoho-oauthtoken {token}"},
            timeout=30,
        )
    return {
        "v": "multipart",
        "token_ok": True,
        "account_probe_status": ar.status_code,
        "send_status": sr.status_code,
        "send_body": sr.text[:600],
        "to_email": email,
    }
