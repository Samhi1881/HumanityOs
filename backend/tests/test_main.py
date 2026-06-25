from fastapi.testclient import TestClient

def test_health_check(client: TestClient) -> None:
    """Verifies that the /health endpoint is live and operational."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "HumanityOS"}

def test_status_endpoint(client: TestClient) -> None:
    """Verifies the system status endpoint structure and fields."""
    response = client.get("/api/v1/status", headers={"Authorization": "Bearer mock-admin"})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "cache" in data
