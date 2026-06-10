import os
import pytest
from api.models.health_data import EnrolleeRow
from api.models.responses import KlaireAnalysis, UrgencyLevel
from api.services.report_service import generate_individual_pdf, generate_company_pdf


SAMPLE_ROW = EnrolleeRow(
    enrollee_id="CL_001", name="Ada Obi", age=35, gender="F",
    systolic=118, diastolic=76, blood_glucose=90, bmi=22.1,
    email="ada@test.com", company_name="Arik Air",
)

SAMPLE_ANALYSIS = KlaireAnalysis(
    enrollee_id="CL_001",
    health_score=82,
    urgency=UrgencyLevel.routine,
    metric_scores=[],
    next_steps=["Walk daily", "Drink water", "Sleep 8hrs"],
    klaire_flags="All readings normal for age and gender.",
)


def test_generate_individual_pdf_creates_file(tmp_path):
    out_path = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    assert os.path.exists(out_path)
    assert out_path.endswith(".pdf")
    assert os.path.getsize(out_path) > 1000


def test_generate_individual_pdf_uses_unique_path(tmp_path):
    path1 = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    path2 = generate_individual_pdf(SAMPLE_ROW, SAMPLE_ANALYSIS, str(tmp_path))
    assert path1 != path2  # UUID-keyed — no collision


def test_generate_company_pdf_creates_file(tmp_path):
    rows = [SAMPLE_ROW]
    analyses = [SAMPLE_ANALYSIS]
    out_path = generate_company_pdf("Arik Air", rows, analyses, str(tmp_path))
    assert os.path.exists(out_path)
    assert out_path.endswith(".pdf")
