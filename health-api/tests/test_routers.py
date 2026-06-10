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
    response = client.get(
        "/api/reports/batch/test-batch",
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200
