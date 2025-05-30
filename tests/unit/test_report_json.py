from fastapi.testclient import TestClient
from main import app
from palantir.core.weaviate_store import store_to_weaviate


def test_report_404_json():
    c = TestClient(app)
    res = c.get("/report/does-not-exist", headers={"accept": "application/json"})
    assert res.status_code == 404 and res.json()["detail"] == "job_id not found"


def test_report_json():
    client = TestClient(app)
    job_id = "jobid"
    store_to_weaviate(job_id, {"type": "json", "data": {"a": 1}, "job_id": job_id})
    res = client.get(f"/report/{job_id}", headers={"accept": "application/json"})
    assert res.status_code == 200 and res.json()["type"] == "json"
