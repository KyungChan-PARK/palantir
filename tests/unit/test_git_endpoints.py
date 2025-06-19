"""Git 워크플로우 관리 API 엔드포인트 테스트"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from palantir.api.git_endpoints import router
from palantir.core.git_manager import BranchInfo


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(router)


@pytest.fixture
def mock_git_manager():
    """GitManager 목업"""
    with patch("palantir.api.git_endpoints.git_manager") as mock:
        mock.create_branch = AsyncMock()
        mock.commit_changes = AsyncMock()
        mock.push_changes = AsyncMock()
        mock.get_branch_info = AsyncMock()
        mock.get_status = AsyncMock()
        yield mock


def test_create_branch(client, mock_git_manager):
    """브랜치 생성 엔드포인트 테스트"""
    # 성공 케이스
    mock_git_manager.create_branch.return_value = True
    response = client.post("/git/branch", json={
        "name": "feature/test",
        "base": "main"
    })
    assert response.status_code == 200
    assert response.json() is True
    mock_git_manager.create_branch.assert_called_once_with(
        "feature/test",
        "main"
    )

    # 실패 케이스
    mock_git_manager.create_branch.reset_mock()
    mock_git_manager.create_branch.return_value = False
    response = client.post("/git/branch", json={
        "name": "invalid..branch"
    })
    assert response.status_code == 200
    assert response.json() is False


def test_commit_changes(client, mock_git_manager):
    """커밋 엔드포인트 테스트"""
    # 성공 케이스
    mock_git_manager.commit_changes.return_value = True
    response = client.post("/git/commit", json={
        "message": "Add new feature",
        "type": "feat",
        "files": ["test.txt"]
    })
    assert response.status_code == 200
    assert response.json() is True
    mock_git_manager.commit_changes.assert_called_once_with(
        message="Add new feature",
        type="feat",
        files=["test.txt"]
    )

    # 실패 케이스
    mock_git_manager.commit_changes.reset_mock()
    mock_git_manager.commit_changes.return_value = False
    response = client.post("/git/commit", json={
        "message": "x" * 51  # 50자 초과
    })
    assert response.status_code == 200
    assert response.json() is False


def test_push_changes(client, mock_git_manager):
    """푸시 엔드포인트 테스트"""
    # 성공 케이스
    mock_git_manager.push_changes.return_value = True
    response = client.post("/git/push", json={
        "branch": "feature/test",
        "remote": "origin"
    })
    assert response.status_code == 200
    assert response.json() is True
    mock_git_manager.push_changes.assert_called_once_with(
        "feature/test",
        "origin"
    )

    # 실패 케이스
    mock_git_manager.push_changes.reset_mock()
    mock_git_manager.push_changes.return_value = False
    response = client.post("/git/push", json={})
    assert response.status_code == 200
    assert response.json() is False


def test_get_branch_info(client, mock_git_manager):
    """브랜치 정보 조회 엔드포인트 테스트"""
    # 성공 케이스
    mock_git_manager.get_branch_info.return_value = BranchInfo(
        name="feature/test",
        current=True,
        remote="origin/feature/test",
        commits=[]
    )
    response = client.get("/git/branch/feature/test")
    assert response.status_code == 200
    assert response.json()["name"] == "feature/test"
    assert response.json()["current"] is True
    assert response.json()["remote"] == "origin/feature/test"
    mock_git_manager.get_branch_info.assert_called_once_with("feature/test")

    # 실패 케이스
    mock_git_manager.get_branch_info.reset_mock()
    mock_git_manager.get_branch_info.return_value = BranchInfo(
        name="",
        current=False,
        remote=None,
        commits=[]
    )
    response = client.get("/git/branch/non-existent")
    assert response.status_code == 200
    assert response.json()["name"] == ""
    assert not response.json()["current"]
    assert response.json()["remote"] is None


def test_get_status(client, mock_git_manager):
    """저장소 상태 조회 엔드포인트 테스트"""
    # 성공 케이스
    mock_git_manager.get_status.return_value = {
        "branch": "main",
        "untracked": ["new.txt"],
        "modified": ["modified.txt"],
        "deleted": [],
        "is_dirty": True,
        "remotes": ["origin"]
    }
    response = client.get("/git/status")
    assert response.status_code == 200
    status = response.json()
    assert status["branch"] == "main"
    assert "new.txt" in status["untracked"]
    assert "modified.txt" in status["modified"]
    assert status["is_dirty"] is True
    assert "origin" in status["remotes"]
    mock_git_manager.get_status.assert_called_once()

    # 실패 케이스
    mock_git_manager.get_status.reset_mock()
    mock_git_manager.get_status.return_value = {"error": "Status check failed"}
    response = client.get("/git/status")
    assert response.status_code == 200
    assert "error" in response.json() 