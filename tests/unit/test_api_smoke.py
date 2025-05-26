from fastapi.testclient import TestClient
from main import app
import pytest

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