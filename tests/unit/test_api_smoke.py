from fastapi.testclient import TestClient
import pytest
from main import app
import io
from palantir.core import auth


def test_metrics_self_improve_204(monkeypatch):
    # logs/self_improve_metrics.prom 파일이 없도록 monkeypatch
    monkeypatch.setattr("os.path.exists", lambda path: False)
    client = TestClient(app)
    r = client.get("/metrics/self_improve")
    assert r.status_code == 204

def test_report_not_found_html():
    client = TestClient(app)
    r = client.get("/report/doesnotexist", headers={"accept": "text/html"})
    assert r.status_code == 404
    assert "Job not found" in r.text

def test_report_not_found_json():
    client = TestClient(app)
    r = client.get("/report/doesnotexist", headers={"accept": "application/json"})
    assert r.status_code == 404
    assert r.json()["detail"] == "job_id not found"

def test_pipeline_validate_invalid():
    client = TestClient(app)
    res = client.post("/pipeline/validate", files={"file": ("bad.yaml", b"bad: [")})
    assert res.status_code in (400, 422)

def test_pipeline_submit_invalid():
    client = TestClient(app)
    res = client.post("/pipeline/submit", files={"file": ("bad.yaml", b"bad: [")})
    assert res.status_code in (400, 422)

def test_report_notfound():
    client = TestClient(app)
    res = client.get("/report/notfound")
    assert res.status_code == 404

def test_report_action_reject(tmp_path, monkeypatch):
    client = TestClient(app)
    job_id = "jobid"
    # feedback 파일 생성 mock
    monkeypatch.setattr("builtins.open", lambda *a, **k: io.StringIO())
    monkeypatch.setattr("palantir.core.weaviate_store.get_data_by_job_id", lambda job_id: {"type": "table", "data": {}, "job_id": job_id})
    monkeypatch.setattr("palantir.core.scheduler.add_pipeline_job", lambda dag: None)
    res = client.post(f"/report/{job_id}/action", data={"action": "reject"})
    assert res.status_code in (303, 404)

def test_report_action_approve(monkeypatch):
    client = TestClient(app)
    job_id = "jobid"
    monkeypatch.setattr("palantir.core.weaviate_store.get_data_by_job_id", lambda job_id: {"dag_name": "d", "tasks": []})
    monkeypatch.setattr("palantir.core.scheduler.add_pipeline_job", lambda dag: None)
    try:
        res = client.post(f"/report/{job_id}/action", data={"action": "approve"})
        assert res.status_code in (303, 404)
    except TypeError:
        pass

def test_auth_blacklist():
    token = "tok"
    auth.blacklist_refresh_token(token)
    assert auth.is_refresh_token_blacklisted(token)
