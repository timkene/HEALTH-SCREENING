from __future__ import annotations
import json
import os
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from api.core.security import require_api_key
from api.core.database import get_db
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel
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


@router.get("/batch/{batch_id}/enrollees")
async def list_batch_enrollees(batch_id: str, _: str = Depends(require_api_key)) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT
            e.enrollee_id, e.name, e.age, e.gender, e.company_name, e.email, e.phone,
            e.systolic, e.diastolic, e.blood_glucose, e.bmi, e.cholesterol,
            ka.health_score, ka.urgency,
            CASE WHEN rm.pdf_path IS NOT NULL THEN TRUE ELSE FALSE END AS has_pdf,
            COALESCE(rm.email_sent, FALSE) AS email_sent
        FROM enrollees e
        LEFT JOIN klaire_analyses ka ON e.enrollee_id = ka.enrollee_id
        LEFT JOIN report_meta rm ON e.enrollee_id = rm.enrollee_id
        WHERE e.batch_id = ?
        ORDER BY e.name
    """, [batch_id]).fetchall()
    cols = [d[0] for d in conn.description]
    return [dict(zip(cols, r)) for r in rows]


@router.get("/{enrollee_id:path}/pdf")
async def download_pdf(enrollee_id: str, _: str = Depends(require_api_key)) -> FileResponse:
    from urllib.parse import unquote
    enrollee_id = unquote(enrollee_id)
    conn = get_db()
    result = conn.execute(
        "SELECT pdf_path FROM report_meta WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result or not result[0] or not os.path.exists(result[0]):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(result[0], media_type="application/pdf",
                        filename=f"{enrollee_id}_report.pdf")


@router.post("/{enrollee_id:path}/generate-sync")
async def generate_pdf_sync(
    enrollee_id: str,
    _: str = Depends(require_api_key),
) -> FileResponse:
    """Generate a PDF report for one enrollee synchronously (no Celery required).
    Runs Klaire analysis if not already stored, then generates the PDF."""
    from urllib.parse import unquote
    from api.services.klaire_service import analyse_enrollee, generate_metric_explanations
    from api.services.report_service import generate_individual_pdf

    enrollee_id = unquote(enrollee_id)
    conn = get_db()
    result = conn.execute(
        "SELECT * FROM enrollees WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Enrollee not found")
    cols = [d[0] for d in conn.description]
    row = EnrolleeRow(**dict(zip(cols, result)))

    # Use existing analysis or run a fresh one
    existing = conn.execute(
        "SELECT health_score, urgency, klaire_flags, next_steps FROM klaire_analyses WHERE enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if existing:
        health_score, urgency_str, klaire_flags, next_steps_json = existing
        analysis = KlaireAnalysis(
            enrollee_id=enrollee_id,
            health_score=health_score,
            urgency=UrgencyLevel(urgency_str),
            metric_scores=[],
            dominant_risk=None,
            next_steps=json.loads(next_steps_json) if next_steps_json else [],
            klaire_flags=klaire_flags or "",
        )
    else:
        analysis = analyse_enrollee(row)
        conn.execute("""
            INSERT OR REPLACE INTO klaire_analyses
              (enrollee_id, health_score, urgency, klaire_flags, next_steps)
            VALUES (?, ?, ?, ?, ?)
        """, [
            enrollee_id, analysis.health_score, analysis.urgency.value,
            analysis.klaire_flags, json.dumps(analysis.next_steps),
        ])

    narratives = generate_metric_explanations(row)
    batch_id = conn.execute(
        "SELECT batch_id FROM enrollees WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()[0]
    out_dir = tempfile.mkdtemp(prefix=f"report_{enrollee_id[:8]}_")
    pdf_path = generate_individual_pdf(row, analysis, out_dir, narratives)

    conn.execute("""
        INSERT OR REPLACE INTO report_meta (enrollee_id, batch_id, pdf_path)
        VALUES (?, ?, ?)
    """, [enrollee_id, batch_id, pdf_path])

    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"{enrollee_id}_report.pdf")
