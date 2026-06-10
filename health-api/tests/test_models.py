import pytest
from pydantic import ValidationError
from api.models.health_data import EnrolleeRow, BatchUpload
from api.models.responses import (
    KlaireAnalysis, UrgencyLevel, MetricScore, DoctorBrief, JobStatus, ReportMeta
)


def test_enrollee_row_requires_core_fields():
    row = EnrolleeRow(
        enrollee_id="CL_ARIK_003",
        name="Chukwuemeka Obi",
        age=44,
        gender="M",
        systolic=142,
        diastolic=88,
    )
    assert row.enrollee_id == "CL_ARIK_003"
    assert row.bmi is None  # optional fields default to None


def test_enrollee_row_rejects_negative_age():
    with pytest.raises(ValidationError):
        EnrolleeRow(
            enrollee_id="X",
            name="Test",
            age=-1,
            gender="M",
            systolic=120,
            diastolic=80,
        )


def test_batch_upload_holds_multiple_rows():
    rows = [
        EnrolleeRow(enrollee_id=f"ID_{i}", name=f"Person {i}", age=30, gender="F",
                    systolic=120, diastolic=80)
        for i in range(3)
    ]
    batch = BatchUpload(batch_id="batch-001", company_name="Arik Air", rows=rows)
    assert len(batch.rows) == 3


def test_klaire_analysis_urgency_enum():
    analysis = KlaireAnalysis(
        enrollee_id="CL_ARIK_003",
        health_score=72,
        urgency=UrgencyLevel.watch,
        metric_scores=[MetricScore(metric="Blood Pressure", score=65, flag="Stage 1 HTN")],
        next_steps=["Step 1", "Step 2", "Step 3"],
        klaire_flags="Patient shows early hypertension markers.",
    )
    assert analysis.urgency == UrgencyLevel.watch
    assert analysis.dominant_risk is None


def test_job_status_defaults():
    job = JobStatus(job_id="j1", status="pending")
    assert job.total == 0
    assert job.failed_ids == []
