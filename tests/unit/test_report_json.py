from fastapi.testclient import TestClient

from main import app
from palantir.core.weaviate_store import _memory_store, store_to_weaviate


def test_report_404_json():
    c = TestClient(app)
    res = c.get("/report/does-not-exist", headers={"accept": "application/json"})
    assert res.status_code == 404 and res.json()["detail"] == "job_id not found"


def test_report_json():
    client = TestClient(app)
    job_id = "jobid"
    obj = {"type": "json", "data": {"a": 1}, "job_id": job_id}
    _memory_store[job_id] = obj  # 메모리 저장 보장
    store_to_weaviate(obj)
    r = client.get(f"/report/{job_id}", headers={"accept": "application/json"})
    assert r.status_code == 200
    assert r.json()["type"] == "json"
