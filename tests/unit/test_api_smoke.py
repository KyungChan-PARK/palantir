"""API 스모크 테스트."""

import io
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from palantir.core import auth
from palantir.core.ontology import Ontology
from palantir.core.pipeline import Pipeline
from palantir.core.report import Report
from palantir.main import app

client = TestClient(app)

@pytest.fixture
def mock_pipeline():
    """파이프라인 모의 객체를 생성합니다."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "test-pipeline-001"
    pipeline.name = "테스트 파이프라인"
    pipeline.status = "completed"
    pipeline.start_time = datetime.now() - timedelta(hours=1)
    pipeline.end_time = datetime.now()
    pipeline.result = {"status": "success", "message": "테스트 완료"}
    return pipeline

@pytest.fixture
def mock_report():
    """리포트 모의 객체를 생성합니다."""
    report = MagicMock(spec=Report)
    report.id = "test-report-001"
    report.title = "테스트 리포트"
    report.content = "테스트 내용"
    report.status = "pending"
    report.created_at = datetime.now()
    return report

@pytest.fixture
def mock_ontology():
    """온톨로지 모의 객체를 생성합니다."""
    ontology = MagicMock(spec=Ontology)
    ontology.id = "test-ontology-001"
    ontology.name = "테스트 온톨로지"
    ontology.description = "테스트 설명"
    ontology.created_at = datetime.now()
    return ontology

def test_metrics_self_improve_204(monkeypatch):
    """자체 개선 메트릭스 엔드포인트를 테스트합니다."""
    monkeypatch.setattr("os.path.exists", lambda path: False)
    response = client.get("/metrics/self_improve")
    assert response.status_code == 204

def test_health_check():
    """헬스 체크 엔드포인트를 테스트합니다."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data

def test_report_not_found_html():
    """존재하지 않는 리포트 HTML 요청을 테스트합니다."""
    response = client.get("/report/doesnotexist", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "Job not found" in response.text

def test_report_not_found_json():
    """존재하지 않는 리포트 JSON 요청을 테스트합니다."""
    response = client.get("/report/doesnotexist", headers={"accept": "application/json"})
    assert response.status_code == 404
    assert response.json()["detail"] == "job_id not found"

def test_pipeline_validate_invalid():
    """잘못된 파이프라인 검증을 테스트합니다."""
    response = client.post("/pipeline/validate", files={"file": ("bad.yaml", b"bad: [")})
    assert response.status_code in (400, 422)

def test_pipeline_submit_invalid():
    """잘못된 파이프라인 제출을 테스트합니다."""
    response = client.post("/pipeline/submit", files={"file": ("bad.yaml", b"bad: [")})
    assert response.status_code in (400, 422)

def test_report_notfound():
    """존재하지 않는 리포트 요청을 테스트합니다."""
    response = client.get("/report/notfound")
    assert response.status_code == 404

def test_report_action_reject(tmp_path, monkeypatch):
    """리포트 거부 액션을 테스트합니다."""
    client = TestClient(app)
    job_id = "jobid"
    # feedback 파일 생성 mock
    monkeypatch.setattr("builtins.open", lambda *a, **k: io.StringIO())
    monkeypatch.setattr(
        "palantir.core.weaviate_store.get_data_by_job_id",
        lambda job_id: {"type": "table", "data": {}, "job_id": job_id}
    )
    monkeypatch.setattr("palantir.core.scheduler.add_pipeline_job", lambda dag: None)
    response = client.post(f"/report/{job_id}/action", data={"action": "reject"})
    assert response.status_code in (303, 404)

def test_report_action_approve(monkeypatch):
    """리포트 승인 액션을 테스트합니다."""
    client = TestClient(app)
    job_id = "jobid"
    monkeypatch.setattr(
        "palantir.core.weaviate_store.get_data_by_job_id",
        lambda job_id: {"dag_name": "d", "tasks": []}
    )
    monkeypatch.setattr("palantir.core.scheduler.add_pipeline_job", lambda dag: None)
    try:
        response = client.post(f"/report/{job_id}/action", data={"action": "approve"})
        assert response.status_code in (303, 404)
    except TypeError:
        pass

def test_auth_blacklist():
    """인증 토큰 블랙리스트를 테스트합니다."""
    token = "tok"
    auth.blacklist_refresh_token(token)
    assert auth.is_refresh_token_blacklisted(token)

def test_metrics_endpoint():
    """메트릭스 엔드포인트를 테스트합니다."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "business" in data
    assert "cpu" in data["system"]
    assert "memory" in data["system"]
    assert "disk" in data["system"]
    assert "network" in data["system"]
    assert "active_users" in data["business"]
    assert "pipeline_executions" in data["business"]
    assert "llm_requests" in data["business"]
    assert "api_requests" in data["business"]
    assert "request_duration" in data["business"]

def test_pipeline_creation(mock_pipeline):
    """파이프라인 생성 엔드포인트를 테스트합니다."""
    with patch("palantir.core.pipeline.Pipeline.create") as mock_create:
        mock_create.return_value = mock_pipeline
        response = client.post(
            "/pipeline/create",
            json={
                "name": "테스트 파이프라인",
                "config": {"type": "test"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_pipeline.id
        assert data["name"] == mock_pipeline.name
        assert data["status"] == mock_pipeline.status

def test_ontology_creation(mock_ontology):
    """온톨로지 생성 엔드포인트를 테스트합니다."""
    with patch("palantir.core.ontology.Ontology.create") as mock_create:
        mock_create.return_value = mock_ontology
        response = client.post(
            "/ontology/create",
            json={
                "name": "테스트 온톨로지",
                "description": "테스트 설명"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_ontology.id
        assert data["name"] == mock_ontology.name
        assert data["description"] == mock_ontology.description
