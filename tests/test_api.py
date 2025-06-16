import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Agent API is running"}


def test_status_unauthorized():
    """인증되지 않은 상태 확인 요청 테스트"""
    response = client.get("/status")
    assert response.status_code == 403


def test_status_authorized():
    """인증된 상태 확인 요청 테스트"""
    headers = {"X-API-Key": "your-api-key"}
    response = client.get("/status", headers=headers)
    assert response.status_code == 200


def test_execute_command():
    """명령어 실행 테스트"""
    headers = {"X-API-Key": "your-api-key"}
    data = {"command": "test_command", "parameters": {"param1": "value1"}}
    response = client.post("/execute", json=data, headers=headers)
    assert response.status_code == 200


def test_register_agent():
    """에이전트 등록 테스트"""
    headers = {"X-API-Key": "your-api-key"}
    data = {
        "config": {
            "name": "test_agent",
            "description": "Test agent",
            "model": "gpt-4",
            "system_prompt": "You are a test agent.",
        }
    }
    response = client.post("/agents", json=data, headers=headers)
    assert response.status_code == 200


def test_list_agents():
    """에이전트 목록 조회 테스트"""
    headers = {"X-API-Key": "your-api-key"}
    response = client.get("/agents", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
