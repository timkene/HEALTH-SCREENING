from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.core.security import require_api_key
from api.core.database import get_db
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, DoctorBrief, UrgencyLevel
from api.services.klaire_service import (
    analyse_enrollee,
    stream_patient_narrative,
    generate_doctor_brief,
)

router = APIRouter()


def _get_enrollee_row(enrollee_id: str) -> EnrolleeRow:
    conn = get_db()
    result = conn.execute(
        "SELECT * FROM enrollees WHERE enrollee_id = ?", [enrollee_id]
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Enrollee {enrollee_id} not found")
    cols = [d[0] for d in conn.description]
    data = dict(zip(cols, result))
    return EnrolleeRow(**data)


@router.post("/klaire/analyse/{enrollee_id}", response_model=KlaireAnalysis)
async def analyse(enrollee_id: str, _: str = Depends(require_api_key)) -> KlaireAnalysis:
    row = _get_enrollee_row(enrollee_id)
    analysis = analyse_enrollee(row)
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO klaire_analyses
          (enrollee_id, health_score, urgency, klaire_flags, next_steps)
        VALUES (?, ?, ?, ?, ?)
    """, [
        analysis.enrollee_id,
        analysis.health_score,
        analysis.urgency.value,
        analysis.klaire_flags,
        json.dumps(analysis.next_steps),
    ])
    return analysis


@router.get("/klaire/stream/{enrollee_id}")
async def stream(enrollee_id: str, _: str = Depends(require_api_key)) -> StreamingResponse:
    row = _get_enrollee_row(enrollee_id)

    async def event_generator():
        async for chunk in stream_patient_narrative(row):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/enrollees/{enrollee_id}/doctor-brief", response_model=DoctorBrief)
async def doctor_brief(enrollee_id: str, _: str = Depends(require_api_key)) -> DoctorBrief:
    row = _get_enrollee_row(enrollee_id)
    conn = get_db()
    result = conn.execute(
        "SELECT health_score, urgency, klaire_flags FROM klaire_analyses WHERE enrollee_id = ?",
        [enrollee_id],
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="No analysis found. Run /klaire/analyse first.")
    health_score, urgency_str, klaire_flags = result
    analysis_stub = type("A", (), {
        "health_score": health_score,
        "urgency": UrgencyLevel(urgency_str),
        "klaire_flags": klaire_flags,
    })()
    brief_text = generate_doctor_brief(row, analysis_stub)
    return DoctorBrief(
        enrollee_id=enrollee_id,
        name=row.name,
        age=row.age,
        gender=row.gender,
        screening_date="",
        urgency=UrgencyLevel(urgency_str),
        health_score=health_score,
        vitals={
            "bp_systolic": row.systolic,
            "bp_diastolic": row.diastolic,
            "bmi": row.bmi,
            "glucose": row.blood_glucose,
        },
        klaire_flags=brief_text,
        recommended_focus=[],
    )
