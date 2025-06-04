"""API 엔드포인트 모듈."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from datetime import datetime

from .auth import create_access_token, get_current_user
from .user import UserDB, UserCreate, UserUpdate, UserResponse
from .database import get_db
from .monitoring import monitor_request, monitor_db_operation
from .queue import async_task

router = APIRouter()

# 사용자 관리 API
@router.post("/users/", response_model=UserResponse, tags=["users"])
@monitor_request("POST", "/users/")
async def create_user(
    user: UserCreate,
    db = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    새로운 사용자를 생성합니다.
    
    - **username**: 사용자 이름 (고유)
    - **email**: 이메일 주소 (고유)
    - **password**: 비밀번호
    - **full_name**: 전체 이름
    - **scopes**: 권한 범위
    
    관리자 권한이 필요합니다.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    # 사용자 생성 작업을 비동기로 처리
    task_id = await async_task(create_user_task, user, db)
    return {"task_id": task_id, "message": "사용자 생성이 시작되었습니다."}

@router.get("/users/me", response_model=UserResponse, tags=["users"])
@monitor_request("GET", "/users/me")
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    
    - **Authorization**: Bearer 토큰 필요
    """
    return current_user

@router.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
@monitor_request("GET", "/users/{user_id}")
async def read_user(
    user_id: str,
    db = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    특정 사용자의 정보를 조회합니다.
    
    - **user_id**: 사용자 ID
    - **Authorization**: Bearer 토큰 필요
    
    자신의 정보이거나 관리자 권한이 필요합니다.
    """
    if str(current_user.id) != user_id and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
@monitor_request("PUT", "/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    사용자 정보를 업데이트합니다.
    
    - **user_id**: 사용자 ID
    - **user_update**: 업데이트할 정보
    - **Authorization**: Bearer 토큰 필요
    
    자신의 정보이거나 관리자 권한이 필요합니다.
    """
    if str(current_user.id) != user_id and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    # 사용자 업데이트 작업을 비동기로 처리
    task_id = await async_task(update_user_task, user_id, user_update, db)
    return {"task_id": task_id, "message": "사용자 정보 업데이트가 시작되었습니다."}

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
@monitor_request("DELETE", "/users/{user_id}")
async def delete_user(
    user_id: str,
    db = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    사용자를 삭제합니다.
    
    - **user_id**: 사용자 ID
    - **Authorization**: Bearer 토큰 필요
    
    관리자 권한이 필요합니다.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    # 사용자 삭제 작업을 비동기로 처리
    task_id = await async_task(delete_user_task, user_id, db)
    return {"task_id": task_id, "message": "사용자 삭제가 시작되었습니다."}

# 인증 API
@router.post("/auth/token", tags=["auth"])
@monitor_request("POST", "/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    사용자 로그인을 처리합니다.
    
    - **username**: 사용자 이름
    - **password**: 비밀번호
    
    성공 시 액세스 토큰과 리프레시 토큰을 반환합니다.
    """
    # 로그인 작업을 비동기로 처리
    task_id = await async_task(login_task, form_data)
    return {"task_id": task_id, "message": "로그인이 처리 중입니다."}

@router.post("/auth/refresh", tags=["auth"])
@monitor_request("POST", "/auth/refresh")
async def refresh_token(refresh_token: str):
    """
    액세스 토큰을 갱신합니다.
    
    - **refresh_token**: 리프레시 토큰
    
    성공 시 새로운 액세스 토큰을 반환합니다.
    """
    # 토큰 갱신 작업을 비동기로 처리
    task_id = await async_task(refresh_token_task, refresh_token)
    return {"task_id": task_id, "message": "토큰 갱신이 처리 중입니다."}

@router.post("/auth/logout", tags=["auth"])
@monitor_request("POST", "/auth/logout")
async def logout(refresh_token: str):
    """
    사용자 로그아웃을 처리합니다.
    
    - **refresh_token**: 리프레시 토큰
    
    리프레시 토큰을 블랙리스트에 추가합니다.
    """
    # 로그아웃 작업을 비동기로 처리
    task_id = await async_task(logout_task, refresh_token)
    return {"task_id": task_id, "message": "로그아웃이 처리되었습니다."}

# 모니터링 API
@router.get("/monitoring/stats", tags=["monitoring"])
@monitor_request("GET", "/monitoring/stats")
async def get_stats(current_user: UserDB = Depends(get_current_user)):
    """
    시스템 통계를 조회합니다.
    
    - **Authorization**: Bearer 토큰 필요
    
    관리자 권한이 필요합니다.
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    from .monitoring import get_metrics
    return get_metrics() 