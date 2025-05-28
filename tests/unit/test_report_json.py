from fastapi.testclient import TestClient

from main import app


def test_report_404_json():
    c = TestClient(app)
    res = c.get("/report/does-not-exist", headers={"accept": "application/json"})
    assert res.status_code == 404 and res.json()["detail"] == "job_id not found"
