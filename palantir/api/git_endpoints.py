"""Git 워크플로우 관리 API 엔드포인트"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from palantir.core.git_manager import GitManager, BranchInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/git", tags=["git"])
git_manager = GitManager()


class CreateBranchRequest(BaseModel):
    """브랜치 생성 요청"""
    name: str
    base: Optional[str] = None


class CommitRequest(BaseModel):
    """커밋 요청"""
    message: str
    type: str = "feat"
    files: Optional[List[str]] = None


class PushRequest(BaseModel):
    """푸시 요청"""
    branch: Optional[str] = None
    remote: str = "origin"


@router.post("/branch", response_model=bool)
async def create_branch(request: CreateBranchRequest) -> bool:
    """새 브랜치 생성

    Args:
        request: 브랜치 생성 요청

    Returns:
        bool: 성공 여부
    """
    return await git_manager.create_branch(request.name, request.base)


@router.post("/commit", response_model=bool)
async def commit_changes(request: CommitRequest) -> bool:
    """변경사항 커밋

    Args:
        request: 커밋 요청

    Returns:
        bool: 성공 여부
    """
    return await git_manager.commit_changes(
        message=request.message,
        type=request.type,
        files=request.files
    )


@router.post("/push", response_model=bool)
async def push_changes(request: PushRequest) -> bool:
    """변경사항 푸시

    Args:
        request: 푸시 요청

    Returns:
        bool: 성공 여부
    """
    return await git_manager.push_changes(request.branch, request.remote)


@router.get("/branch/{name:path}", response_model=BranchInfo)
@router.get("/branch/", response_model=BranchInfo)
async def get_branch_info(name: Optional[str] = None) -> BranchInfo:
    """브랜치 정보 조회

    Args:
        name: 브랜치 이름 (기본값: 현재 브랜치)

    Returns:
        BranchInfo: 브랜치 정보
    """
    try:
        return await git_manager.get_branch_info(name)
    except Exception as e:
        logger.error(f"브랜치 정보 조회 실패: {str(e)}")
        return BranchInfo(name="", current=False, remote=None, commits=[])


@router.get("/status", response_model=Dict[str, Any])
async def get_status() -> Dict[str, Any]:
    """저장소 상태 조회

    Returns:
        Dict[str, Any]: 상태 정보
    """
    return await git_manager.get_status() 