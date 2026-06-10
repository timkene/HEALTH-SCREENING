def test_health_check_no_auth_required(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_protected_endpoint_rejects_missing_key(client):
    response = client.get("/api/reports/batch/test-batch")
    assert response.status_code == 403


def test_protected_endpoint_rejects_wrong_key(client):
    response = client.get(
        "/api/reports/batch/test-batch",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_protected_endpoint_accepts_valid_key(client):
    from unittest.mock import patch, MagicMock
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = []
    mock_conn.description = []
    with patch("api.routers.reports.get_db", return_value=mock_conn):
        response = client.get(
            "/api/reports/batch/test-batch",
            headers={"X-API-Key": "test-key"},
        )
    assert response.status_code == 200


from unittest.mock import patch, MagicMock
from api.models.responses import KlaireAnalysis, UrgencyLevel, MetricScore


def test_analyse_endpoint_returns_analysis(client):
    mock_analysis = KlaireAnalysis(
        enrollee_id="CL_001",
        health_score=74,
        urgency=UrgencyLevel.watch,
        metric_scores=[],
        next_steps=["a", "b", "c"],
        klaire_flags="BP elevated.",
    )
    mock_row = MagicMock()
    with patch("api.routers.klaire.analyse_enrollee", return_value=mock_analysis), \
         patch("api.routers.klaire._get_enrollee_row", return_value=mock_row), \
         patch("api.routers.klaire.get_db"):
        resp = client.post(
            "/api/klaire/analyse/CL_001",
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 200
    assert resp.json()["health_score"] == 74
    assert resp.json()["urgency"] == "watch"


def test_analyse_endpoint_requires_auth(client):
    resp = client.post("/api/klaire/analyse/CL_001")
    assert resp.status_code == 403
