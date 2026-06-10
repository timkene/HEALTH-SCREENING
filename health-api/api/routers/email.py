from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.email_service import send_via_zoho, send_via_smtp

router = APIRouter()


@router.post("/send/{enrollee_id}")
async def send_email(
    enrollee_id: str,
    method: str = "zoho",
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

    ok = send_via_zoho(email, name, pdf_path) if method == "zoho" else send_via_smtp(email, name, pdf_path)
    if ok:
        conn.execute("UPDATE report_meta SET email_sent = TRUE WHERE enrollee_id = ?", [enrollee_id])
    return {"enrollee_id": enrollee_id, "sent": ok, "method": method}


@router.post("/bulk/{batch_id}")
async def bulk_send(
    batch_id: str,
    method: str = "zoho",
    _: str = Depends(require_api_key),
) -> dict:
    from workers.tasks import bulk_email_task
    task = bulk_email_task.delay(batch_id, method)
    return {"job_id": task.id, "status": "queued"}


@router.get("/methods")
async def list_methods(_: str = Depends(require_api_key)) -> dict:
    return {"methods": ["zoho", "smtp"]}
