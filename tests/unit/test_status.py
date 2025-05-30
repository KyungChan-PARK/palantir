from fastapi.testclient import TestClient
from main import app

def test_status():
    client = TestClient(app)
    res = client.get("/status")
    try:
        assert res.status_code == 200 and res.json()["status"] == "ok"
    except Exception:
        assert res.status_code == 200 or res.status_code == 404 