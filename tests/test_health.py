from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_readiness_check():
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
