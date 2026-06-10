"""
Integration tests for the Clearline HMO Health Screening API.

Covers all router endpoints and low-coverage service paths to bring overall
coverage to >= 80%.  All external dependencies (DB, Claude, B2, email, Celery)
are mocked.
"""
from __future__ import annotations

import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from api.models.responses import DoctorBrief, KlaireAnalysis, UrgencyLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADERS = {"X-API-Key": "test-key"}


def _csv_bytes(enrollee_id: str = "INT_001") -> bytes:
    df = pd.DataFrame([{
        "ENROLLEE ID": enrollee_id,
        "NAME": "Test Person",
        "AGE": 40,
        "GENDER": "M",
        "SYSTOLIC": 130,
        "DIASTOLIC": 85,
        "BLOOD GLUCOSE": 100,
        "BMI": 24.0,
        "EMAIL": "test@example.com",
    }])
    return df.to_csv(index=False).encode()


def _mock_conn(rows=None, cols=None):
    """Return a MagicMock that behaves like a DuckDB connection."""
    conn = MagicMock()
    conn.execute.return_value = conn
    conn.fetchone.return_value = None
    conn.fetchall.return_value = rows or []
    conn.description = [(c,) for c in (cols or [])]
    return conn


def _make_analysis(
    enrollee_id: str = "INT_001",
    urgency: UrgencyLevel = UrgencyLevel.routine,
    health_score: int = 80,
) -> KlaireAnalysis:
    return KlaireAnalysis(
        enrollee_id=enrollee_id,
        health_score=health_score,
        urgency=urgency,
        metric_scores=[],
        next_steps=["Step 1", "Step 2", "Step 3"],
        klaire_flags="Normal readings.",
    )


# ---------------------------------------------------------------------------
# /health  (public)
# ---------------------------------------------------------------------------

def test_health_check_is_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /api/reports/upload
# ---------------------------------------------------------------------------

def test_upload_parses_and_stores(client):
    conn = _mock_conn()
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.post(
            "/api/reports/upload",
            headers=HEADERS,
            files={"file": ("test.csv", _csv_bytes(), "text/csv")},
            data={"company_name": "Test Corp"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["preview"][0]["enrollee_id"] == "INT_001"
    assert data["company_name"] == "Test Corp"


def test_upload_rejects_missing_auth(client):
    resp = client.post(
        "/api/reports/upload",
        files={"file": ("test.csv", _csv_bytes(), "text/csv")},
        data={"company_name": "Test Corp"},
    )
    assert resp.status_code == 403


def test_upload_rejects_bad_csv(client):
    bad_csv = b"COL_A,COL_B\n1,2\n"
    conn = _mock_conn()
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.post(
            "/api/reports/upload",
            headers=HEADERS,
            files={"file": ("test.csv", bad_csv, "text/csv")},
            data={"company_name": "Test Corp"},
        )
    assert resp.status_code == 422


def test_upload_multiple_rows(client):
    df = pd.DataFrame([
        {"ENROLLEE ID": "INT_001", "NAME": "Alice", "AGE": 30, "GENDER": "F",
         "SYSTOLIC": 120, "DIASTOLIC": 80, "BLOOD GLUCOSE": 90, "BMI": 22.0,
         "EMAIL": "alice@example.com"},
        {"ENROLLEE ID": "INT_002", "NAME": "Bob", "AGE": 45, "GENDER": "M",
         "SYSTOLIC": 140, "DIASTOLIC": 90, "BLOOD GLUCOSE": 110, "BMI": 27.0,
         "EMAIL": "bob@example.com"},
    ])
    csv_bytes = df.to_csv(index=False).encode()
    conn = _mock_conn()
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.post(
            "/api/reports/upload",
            headers=HEADERS,
            files={"file": ("multi.csv", csv_bytes, "text/csv")},
            data={"company_name": "Multi Corp"},
        )
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


# ---------------------------------------------------------------------------
# /api/reports/batch/{batch_id}
# ---------------------------------------------------------------------------

def test_batch_report_endpoint_returns_empty_list(client):
    conn = _mock_conn(rows=[], cols=["enrollee_id", "batch_id", "pdf_path"])
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/batch/some-batch-id", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["batch_id"] == "some-batch-id"
    assert body["reports"] == []


def test_batch_report_endpoint_returns_rows(client):
    cols = ["enrollee_id", "batch_id", "pdf_path"]
    rows = [("INT_001", "batch-abc", "/tmp/report.pdf")]
    conn = _mock_conn(rows=rows, cols=cols)
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/batch/batch-abc", headers=HEADERS)
    assert resp.status_code == 200
    reports = resp.json()["reports"]
    assert len(reports) == 1
    assert reports[0]["enrollee_id"] == "INT_001"


def test_batch_report_rejects_no_auth(client):
    resp = client.get("/api/reports/batch/some-batch-id")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/reports/{enrollee_id}/pdf  — download individual PDF
# ---------------------------------------------------------------------------

def test_download_pdf_404_when_no_record(client):
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/INT_999/pdf", headers=HEADERS)
    assert resp.status_code == 404


def test_download_pdf_404_when_file_missing(client):
    conn = _mock_conn()
    conn.fetchone.return_value = ("/nonexistent/path.pdf",)
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/INT_001/pdf", headers=HEADERS)
    assert resp.status_code == 404


def test_download_pdf_returns_file(client):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake content")
        tmp_path = f.name
    try:
        conn = _mock_conn()
        conn.fetchone.return_value = (tmp_path,)
        with patch("api.routers.reports.get_db", return_value=conn):
            resp = client.get("/api/reports/INT_001/pdf", headers=HEADERS)
        assert resp.status_code == 200
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# /api/reports/company/{batch_id}/pdf  — download company PDF
# ---------------------------------------------------------------------------

def test_download_company_pdf_404_when_no_record(client):
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/company/batch-xyz/pdf", headers=HEADERS)
    assert resp.status_code == 404


def test_download_company_pdf_404_when_file_missing(client):
    conn = _mock_conn()
    conn.fetchone.return_value = ("/no/such/file.pdf",)
    with patch("api.routers.reports.get_db", return_value=conn):
        resp = client.get("/api/reports/company/batch-xyz/pdf", headers=HEADERS)
    assert resp.status_code == 404


def test_download_company_pdf_returns_file(client):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake content")
        tmp_path = f.name
    try:
        conn = _mock_conn()
        conn.fetchone.return_value = (tmp_path,)
        with patch("api.routers.reports.get_db", return_value=conn):
            resp = client.get("/api/reports/company/batch-xyz/pdf", headers=HEADERS)
        assert resp.status_code == 200
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# /api/klaire/analyse/{enrollee_id}
# ---------------------------------------------------------------------------

def test_klaire_analyse_endpoint_routine(client):
    analysis = _make_analysis()
    mock_row = MagicMock()
    with patch("api.routers.klaire.analyse_enrollee", return_value=analysis), \
         patch("api.routers.klaire._get_enrollee_row", return_value=mock_row), \
         patch("api.routers.klaire.get_db"):
        resp = client.post("/api/klaire/analyse/INT_001", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["health_score"] == 80
    assert resp.json()["urgency"] == "routine"


def test_klaire_analyse_endpoint_critical(client):
    analysis = _make_analysis(urgency=UrgencyLevel.critical, health_score=20)
    mock_row = MagicMock()
    with patch("api.routers.klaire.analyse_enrollee", return_value=analysis), \
         patch("api.routers.klaire._get_enrollee_row", return_value=mock_row), \
         patch("api.routers.klaire.get_db"):
        resp = client.post("/api/klaire/analyse/INT_001", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["urgency"] == "critical"


def test_klaire_analyse_requires_auth(client):
    resp = client.post("/api/klaire/analyse/INT_001")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /enrollees/{enrollee_id}/doctor-brief
# ---------------------------------------------------------------------------

def test_doctor_brief_returns_brief(client):
    from api.models.health_data import EnrolleeRow
    mock_row = EnrolleeRow(
        enrollee_id="INT_001",
        name="Test Person",
        age=40,
        gender="M",
        systolic=130,
        diastolic=85,
        blood_glucose=100,
        bmi=24.0,
        company_name="Test Corp",
    )
    conn = _mock_conn()
    conn.fetchone.return_value = (75, "routine", "BP is fine.")
    with patch("api.routers.klaire._get_enrollee_row", return_value=mock_row), \
         patch("api.routers.klaire.get_db", return_value=conn), \
         patch("api.routers.klaire.generate_doctor_brief", return_value="Clinical brief text."):
        resp = client.get("/api/enrollees/INT_001/doctor-brief", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["enrollee_id"] == "INT_001"
    assert data["health_score"] == 75


def test_doctor_brief_404_when_no_analysis(client):
    from api.models.health_data import EnrolleeRow
    mock_row = EnrolleeRow(
        enrollee_id="INT_999",
        name="No Analysis",
        age=35,
        gender="F",
        systolic=120,
        diastolic=80,
        blood_glucose=90,
        bmi=23.0,
    )
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.klaire._get_enrollee_row", return_value=mock_row), \
         patch("api.routers.klaire.get_db", return_value=conn):
        resp = client.get("/api/enrollees/INT_999/doctor-brief", headers=HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/email/methods
# ---------------------------------------------------------------------------

def test_email_methods_endpoint(client):
    resp = client.get("/api/email/methods", headers=HEADERS)
    assert resp.status_code == 200
    assert "zoho" in resp.json()["methods"]
    assert "smtp" in resp.json()["methods"]


def test_email_methods_requires_auth(client):
    resp = client.get("/api/email/methods")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/email/send/{enrollee_id}
# ---------------------------------------------------------------------------

def test_email_send_via_zoho(client):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 content")
        tmp_path = f.name
    try:
        conn = _mock_conn()
        conn.fetchone.return_value = ("Test Person", "user@example.com", tmp_path)
        with patch("api.routers.email.get_db", return_value=conn), \
             patch("api.routers.email.send_via_zoho", return_value=True):
            resp = client.post("/api/email/send/INT_001?method=zoho", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sent"] is True
        assert data["method"] == "zoho"
    finally:
        os.unlink(tmp_path)


def test_email_send_via_smtp(client):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 content")
        tmp_path = f.name
    try:
        conn = _mock_conn()
        conn.fetchone.return_value = ("Test Person", "user@example.com", tmp_path)
        with patch("api.routers.email.get_db", return_value=conn), \
             patch("api.routers.email.send_via_smtp", return_value=True):
            resp = client.post("/api/email/send/INT_001?method=smtp", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sent"] is True
        assert data["method"] == "smtp"
    finally:
        os.unlink(tmp_path)


def test_email_send_404_when_no_enrollee(client):
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.email.get_db", return_value=conn):
        resp = client.post("/api/email/send/MISSING_001?method=zoho", headers=HEADERS)
    assert resp.status_code == 404


def test_email_send_422_when_no_email(client):
    conn = _mock_conn()
    conn.fetchone.return_value = ("Test Person", None, "/some/path.pdf")
    with patch("api.routers.email.get_db", return_value=conn):
        resp = client.post("/api/email/send/INT_001?method=zoho", headers=HEADERS)
    assert resp.status_code == 422


def test_email_send_422_when_no_pdf(client):
    conn = _mock_conn()
    conn.fetchone.return_value = ("Test Person", "user@example.com", None)
    with patch("api.routers.email.get_db", return_value=conn):
        resp = client.post("/api/email/send/INT_001?method=zoho", headers=HEADERS)
    assert resp.status_code == 422


def test_email_send_requires_auth(client):
    resp = client.post("/api/email/send/INT_001?method=zoho")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/email/bulk/{batch_id}  — Celery task queued
# ---------------------------------------------------------------------------

def test_bulk_email_queues_task(client):
    mock_task = MagicMock()
    mock_task.id = "task-abc-123"
    # bulk_email_task is imported inside the route function body from workers.tasks
    with patch("workers.tasks.bulk_email_task") as mock_bulk:
        mock_bulk.delay.return_value = mock_task
        resp = client.post("/api/email/bulk/batch-xyz", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "task-abc-123"
    assert data["status"] == "queued"


# ---------------------------------------------------------------------------
# /api/storage/upload/{enrollee_id}
# ---------------------------------------------------------------------------

def test_storage_upload_returns_key_and_url(client):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 content")
        tmp_path = f.name
    try:
        conn = _mock_conn()
        conn.fetchone.return_value = (tmp_path, "Test Corp")
        with patch("api.routers.storage.get_db", return_value=conn), \
             patch("api.routers.storage.upload_pdf", return_value="reports/Test_Corp/INT_001/file.pdf"), \
             patch("api.routers.storage.get_signed_url", return_value="https://s3.test.com/signed"):
            resp = client.post("/api/storage/upload/INT_001", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data
        assert "url" in data
    finally:
        os.unlink(tmp_path)


def test_storage_upload_404_when_no_pdf(client):
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.storage.get_db", return_value=conn):
        resp = client.post("/api/storage/upload/INT_999", headers=HEADERS)
    assert resp.status_code == 404


def test_storage_upload_requires_auth(client):
    resp = client.post("/api/storage/upload/INT_001")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/storage/url/{enrollee_id}
# ---------------------------------------------------------------------------

def test_storage_get_url_returns_url(client):
    conn = _mock_conn()
    conn.fetchone.return_value = ("https://s3.test.com/signed-url",)
    with patch("api.routers.storage.get_db", return_value=conn):
        resp = client.get("/api/storage/url/INT_001", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://s3.test.com/signed-url"


def test_storage_get_url_404_when_no_url(client):
    conn = _mock_conn()
    conn.fetchone.return_value = None
    with patch("api.routers.storage.get_db", return_value=conn):
        resp = client.get("/api/storage/url/INT_999", headers=HEADERS)
    assert resp.status_code == 404


def test_storage_get_url_requires_auth(client):
    resp = client.get("/api/storage/url/INT_001")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/jobs/{job_id}  — Celery job status
# ---------------------------------------------------------------------------

def test_job_status_returns_pending(client):
    mock_result = MagicMock()
    mock_result.state = "PENDING"
    mock_result.info = {}
    # celery_app is imported inside the route function body from workers.tasks
    with patch("workers.tasks.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = client.get("/api/jobs/job-abc-123", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "job-abc-123"
    assert data["status"] == "pending"


def test_job_status_returns_progress_info(client):
    mock_result = MagicMock()
    mock_result.state = "PROGRESS"
    mock_result.info = {"total": 10, "completed": 5, "failed_ids": []}
    with patch("workers.tasks.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = client.get("/api/jobs/job-abc-456", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert data["completed"] == 5


def test_job_progress_endpoint(client):
    mock_result = MagicMock()
    mock_result.state = "PROGRESS"
    mock_result.info = {"total": 20, "completed": 12}
    with patch("workers.tasks.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = client.get("/api/jobs/job-xyz/progress", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 20
    assert data["completed"] == 12
    assert data["state"] == "PROGRESS"


def test_job_status_requires_auth(client):
    resp = client.get("/api/jobs/some-job-id")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# email_service — send_via_smtp
# ---------------------------------------------------------------------------

def test_send_via_smtp_success():
    from api.services.email_service import send_via_smtp
    import smtplib

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 content")
        tmp_path = f.name
    try:
        mock_server = MagicMock()
        mock_smtp_cls = MagicMock(return_value=mock_server)
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        with patch("api.services.email_service.smtplib.SMTP", mock_smtp_cls):
            result = send_via_smtp("user@example.com", "Test User", tmp_path)
        assert result is True
        mock_server.starttls.assert_called_once()
    finally:
        os.unlink(tmp_path)


def test_send_via_smtp_sends_correct_fields():
    from api.services.email_service import send_via_smtp

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 content")
        tmp_path = f.name
    try:
        mock_server = MagicMock()
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        with patch("api.services.email_service.smtplib.SMTP", return_value=mock_server):
            send_via_smtp("recipient@test.com", "Alice", tmp_path)
        mock_server.sendmail.assert_called_once()
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# email_service — send_alert_to_tele_team
# ---------------------------------------------------------------------------

def test_send_alert_to_tele_team_returns_true():
    from api.services.email_service import send_alert_to_tele_team

    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)
    with patch("api.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = send_alert_to_tele_team("Test Person", "INT_001", "critical")
    assert result is True
    mock_server.sendmail.assert_called_once()


def test_send_alert_to_tele_team_returns_false_on_error():
    from api.services.email_service import send_alert_to_tele_team

    with patch("api.services.email_service.smtplib.SMTP", side_effect=Exception("SMTP error")):
        result = send_alert_to_tele_team("Test Person", "INT_001", "critical")
    assert result is False


# ---------------------------------------------------------------------------
# report_service — urgency branch coverage (critical, watch, urgent)
# ---------------------------------------------------------------------------

def test_generate_pdf_critical_urgency(tmp_path):
    from api.services.report_service import generate_individual_pdf
    from api.models.health_data import EnrolleeRow

    row = EnrolleeRow(
        enrollee_id="INT_CRIT",
        name="Critical Patient",
        age=55,
        gender="M",
        systolic=190,
        diastolic=125,
        blood_glucose=450,
        bmi=42.0,
        company_name="Corp",
    )
    analysis = _make_analysis("INT_CRIT", UrgencyLevel.critical, health_score=15)
    out_path = generate_individual_pdf(row, analysis, str(tmp_path))
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_generate_pdf_urgent_urgency(tmp_path):
    from api.services.report_service import generate_individual_pdf
    from api.models.health_data import EnrolleeRow

    row = EnrolleeRow(
        enrollee_id="INT_URG",
        name="Urgent Patient",
        age=50,
        gender="F",
        systolic=160,
        diastolic=100,
        blood_glucose=200,
        bmi=30.0,
        company_name="Corp",
    )
    analysis = _make_analysis("INT_URG", UrgencyLevel.urgent, health_score=40)
    out_path = generate_individual_pdf(row, analysis, str(tmp_path))
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_generate_pdf_watch_urgency(tmp_path):
    from api.services.report_service import generate_individual_pdf
    from api.models.health_data import EnrolleeRow

    row = EnrolleeRow(
        enrollee_id="INT_WATCH",
        name="Watch Patient",
        age=45,
        gender="M",
        systolic=145,
        diastolic=92,
        blood_glucose=130,
        bmi=28.0,
        company_name="Corp",
    )
    analysis = _make_analysis("INT_WATCH", UrgencyLevel.watch, health_score=60)
    out_path = generate_individual_pdf(row, analysis, str(tmp_path))
    assert os.path.exists(out_path)


# ---------------------------------------------------------------------------
# klaire_service — analyse_enrollee and generate_doctor_brief
# ---------------------------------------------------------------------------

def test_analyse_enrollee_calls_anthropic():
    from api.services.klaire_service import analyse_enrollee
    from api.models.health_data import EnrolleeRow

    row = EnrolleeRow(
        enrollee_id="INT_001",
        name="Test Person",
        age=40,
        gender="M",
        systolic=130,
        diastolic=85,
        blood_glucose=100,
        bmi=24.0,
    )
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = '{"health_score": 75, "urgency": "routine", "metric_scores": [], "next_steps": ["a","b","c"], "klaire_flags": "Normal."}'

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("api.services.klaire_service._get_client", return_value=mock_client):
        result = analyse_enrollee(row)

    assert result.health_score == 75
    assert result.urgency == UrgencyLevel.routine
    assert len(result.next_steps) == 3


def test_generate_doctor_brief_calls_anthropic():
    from api.services.klaire_service import generate_doctor_brief
    from api.models.health_data import EnrolleeRow

    row = EnrolleeRow(
        enrollee_id="INT_001",
        name="Test Person",
        age=40,
        gender="M",
        systolic=130,
        diastolic=85,
        blood_glucose=100,
        bmi=24.0,
    )
    analysis = _make_analysis()

    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "40M with elevated BP. Routine follow-up."

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("api.services.klaire_service._get_client", return_value=mock_client):
        result = generate_doctor_brief(row, analysis)

    assert "40M" in result or "elevated" in result or len(result) > 0


# ---------------------------------------------------------------------------
# storage_service — _get_s3_client coverage
# ---------------------------------------------------------------------------

def test_storage_service_get_s3_client():
    from api.services.storage_service import _get_s3_client

    mock_s3 = MagicMock()
    with patch("api.services.storage_service.boto3.client", return_value=mock_s3):
        client = _get_s3_client()
    assert client is mock_s3
