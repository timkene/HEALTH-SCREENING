from __future__ import annotations
import os
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from api.core.security import require_api_key
from api.core.database import get_db
from api.services.analysis_service import parse_upload, ParseError

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    _: str = Depends(require_api_key),
) -> dict:
    contents = await file.read()
    try:
        batch = parse_upload(contents, file.filename or "upload.csv", company_name)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    conn = get_db()
    for row in batch.rows:
        conn.execute("""
            INSERT OR REPLACE INTO enrollees
              (enrollee_id, batch_id, name, age, gender, systolic, diastolic,
               blood_glucose, bmi, cholesterol, email, phone, company_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            row.enrollee_id, batch.batch_id, row.name, row.age, row.gender,
            row.systolic, row.diastolic, row.blood_glucose, row.bmi,
            row.cholesterol, row.email, row.phone, row.company_name,
        ])

    return {
        "batch_id": batch.batch_id,
        "company_name": batch.company_name,
        "count": len(batch.rows),
        "preview": [r.model_dump() for r in batch.rows[:5]],
    }


@router.post("/generate/{batch_id}")
async def generate_batch(
    batch_id: str,
    _: str = Depends(require_api_key),
) -> dict:
    from workers.tasks import generate_batch_task
    task = generate_batch_task.delay(batch_id)
    return {"job_id": task.id, "status": "queued"}


@router.get("/batch/{batch_id}")
async def get_batch(batch_id: str, _: str = Depends(require_api_key)) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM report_meta WHERE batch_id = ?", [batch_id]
    ).fetchall()
    cols = [d[0] for d in conn.description]
    return {"batch_id": batch_id, "reports": [dict(zip(cols, r)) for r in rows]}


@router.get("/{enrollee_id}/pdf")
async def download_pdf(enrollee_id: str, _: str = Depends(require_api_key)) -> FileResponse:
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path FROM report_meta WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result or not result[0] or not os.path.exists(result[0]):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(result[0], media_type="application/pdf",
                        filename=f"{enrollee_id}_report.pdf")


@router.get("/company/{batch_id}/pdf")
async def download_company_pdf(batch_id: str, _: str = Depends(require_api_key)) -> FileResponse:
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path FROM report_meta WHERE batch_id = ? AND enrollee_id = 'COMPANY'",
        [batch_id],
    ).fetchone()
    if not result or not result[0] or not os.path.exists(result[0]):
        raise HTTPException(status_code=404, detail="Company PDF not found")
    return FileResponse(result[0], media_type="application/pdf",
                        filename=f"company_report_{batch_id}.pdf")
