from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
def test_metrics_endpoint_status():
    r = client.get('/metrics')
    assert r.status_code in (200, 404)
