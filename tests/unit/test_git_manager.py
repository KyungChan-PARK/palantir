"""Git 워크플로우 관리 시스템 테스트"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo

from palantir.core.git_manager import GitManager, CommitInfo, BranchInfo


@pytest.fixture
def temp_git_repo():
    """임시 Git 저장소 생성"""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)
    
    # 초기 커밋 생성
    readme = Path(temp_dir) / "README.md"
    readme.write_text("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # 원격 저장소 설정
    remote_dir = tempfile.mkdtemp()
    remote_repo = Repo.init(remote_dir, bare=True)
    repo.create_remote("origin", remote_dir)

    yield temp_dir
    shutil.rmtree(temp_dir)
    shutil.rmtree(remote_dir)


@pytest.fixture
def git_manager(temp_git_repo):
    """GitManager 인스턴스 생성"""
    return GitManager(temp_git_repo)


@pytest.mark.asyncio
async def test_create_branch(git_manager):
    """브랜치 생성 테스트"""
    # 유효한 브랜치 이름으로 생성
    assert await git_manager.create_branch("feature/test")

    # 유효하지 않은 브랜치 이름으로 생성
    assert not await git_manager.create_branch("invalid..branch")

    # 기존 브랜치 기반으로 생성
    assert await git_manager.create_branch("feature/test2", "feature/test")


@pytest.mark.asyncio
async def test_commit_changes(git_manager):
    """커밋 테스트"""
    # 파일 생성
    test_file = Path(git_manager.repo_path) / "test.txt"
    test_file.write_text("Test content")

    # 파일 지정하여 커밋
    assert await git_manager.commit_changes(
        message="Add test file",
        type="feat",
        files=["test.txt"]
    )

    # 모든 변경사항 커밋
    test_file.write_text("Updated content")
    assert await git_manager.commit_changes(
        message="Update test file",
        type="fix"
    )


@pytest.mark.asyncio
async def test_push_changes(git_manager):
    """푸시 테스트"""
    # 원격 저장소가 있는 경우
    assert await git_manager.create_branch("feature/test")
    test_file = Path(git_manager.repo_path) / "test.txt"
    test_file.write_text("Test content")
    assert await git_manager.commit_changes("Add test file")
    assert await git_manager.push_changes("feature/test")

    # 원격 저장소가 없는 경우
    git_manager.repo.delete_remote("origin")
    assert not await git_manager.push_changes()


@pytest.mark.asyncio
async def test_get_branch_info(git_manager):
    """브랜치 정보 조회 테스트"""
    # 브랜치 생성
    await git_manager.create_branch("test-branch")
    test_file = Path(git_manager.repo_path) / "test.txt"
    test_file.write_text("Test content")
    await git_manager.commit_changes("Add test file")

    # 브랜치 정보 조회
    info = await git_manager.get_branch_info("test-branch")
    assert info.name == "test-branch"
    assert info.current is True
    assert info.remote is None
    assert len(info.commits) > 0

    # 존재하지 않는 브랜치 정보 조회
    info = await git_manager.get_branch_info("non-existent")
    assert info.name == ""
    assert info.current is False
    assert info.remote is None
    assert not info.commits


@pytest.mark.asyncio
async def test_get_status(git_manager):
    """저장소 상태 조회 테스트"""
    # 파일 생성
    test_file = Path(git_manager.repo_path) / "test.txt"
    test_file.write_text("Test content")

    # 상태 조회
    status = await git_manager.get_status()
    assert status["branch"] == "main"
    assert "test.txt" in status["untracked"]
    assert status["is_dirty"] is True
    assert "origin" in status["remotes"]


def test_validate_branch_name(git_manager):
    """브랜치 이름 유효성 검사 테스트"""
    # 유효한 브랜치 이름
    assert git_manager._validate_branch_name("feature/test")
    assert git_manager._validate_branch_name("hotfix-123")
    assert git_manager._validate_branch_name("release_1.0")
    assert git_manager._validate_branch_name("bugfix.1")

    # 유효하지 않은 브랜치 이름
    assert not git_manager._validate_branch_name("invalid..branch")
    assert not git_manager._validate_branch_name("feature/.test")
    assert not git_manager._validate_branch_name("feature/test.")
    assert not git_manager._validate_branch_name("feature/test~1")
    assert not git_manager._validate_branch_name("feature/test^")
    assert not git_manager._validate_branch_name("feature/test:")


def test_validate_commit_message(git_manager):
    """커밋 메시지 유효성 검사 테스트"""
    # 유효한 커밋 메시지
    assert git_manager._validate_commit_message("Add new feature")
    assert git_manager._validate_commit_message("Fix bug\n\nDetailed description")
    assert git_manager._validate_commit_message("Update docs\n\nLong description\nwith multiple lines")

    # 유효하지 않은 커밋 메시지
    assert not git_manager._validate_commit_message("")
    assert not git_manager._validate_commit_message("x" * 51)
    assert not git_manager._validate_commit_message("Title\nNo empty line\nBody")
    assert not git_manager._validate_commit_message("Title\n\n" + "x" * 73)


def test_format_commit_message(git_manager):
    """커밋 메시지 포맷팅 테스트"""
    # 타입이 없는 경우
    msg = git_manager._format_commit_message("Add new feature")
    assert msg == "feat: Add new feature"

    # 타입이 있는 경우
    msg = git_manager._format_commit_message("Add new feature", "feat")
    assert msg == "feat: Add new feature"

    # 본문이 있는 경우
    msg = git_manager._format_commit_message(
        "Add new feature\n\nDetailed description",
        "feat"
    )
    assert msg == "feat: Add new feature\n\nDetailed description" 