from fastapi import APIRouter, Depends, HTTPException
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.storage_service import upload_pdf, get_signed_url

router = APIRouter()


@router.post("/upload/{enrollee_id}")
async def upload(enrollee_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT rm.pdf_path, e.company_name FROM report_meta rm "
        "JOIN enrollees e USING (enrollee_id) WHERE rm.enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result or not result[0]:
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")
    pdf_path, company_name = result
    key = upload_pdf(pdf_path, enrollee_id, company_name or "Unknown")
    url = get_signed_url(key)
    conn.execute(
        "UPDATE report_meta SET b2_url = ? WHERE enrollee_id = ?", [url, enrollee_id]
    )
    return {"enrollee_id": enrollee_id, "key": key, "url": url}


@router.get("/url/{enrollee_id}")
async def get_url(enrollee_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    result = conn.execute(
        "SELECT b2_url FROM report_meta WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result or not result[0]:
        raise HTTPException(status_code=404, detail="No B2 URL found.")
    return {"enrollee_id": enrollee_id, "url": result[0]}
