"""사용자 관리 API 모듈."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .user import (
    UserCreate, UserUpdate, UserResponse, UserDB,
    get_db, create_user, get_user_by_username, get_user_by_email,
    update_user, delete_user, list_users
)
from .auth import get_password_hash, get_current_user

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """새로운 사용자를 생성합니다.
    
    Args:
        user: 생성할 사용자 정보
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        생성된 사용자 정보
        
    Raises:
        HTTPException: 권한이 없거나 사용자 이름/이메일이 이미 존재하는 경우
    """
    # 관리자 권한 확인
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 생성 권한이 없습니다"
        )
    
    # 사용자 이름 중복 확인
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자 이름입니다"
        )
    
    # 이메일 중복 확인
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user.password)
    
    # 사용자 생성
    db_user = create_user(db, user, hashed_password)
    return db_user

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    """현재 인증된 사용자의 정보를 조회합니다.
    
    Args:
        current_user: 현재 인증된 사용자
        
    Returns:
        사용자 정보
    """
    return current_user

@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """특정 사용자의 정보를 조회합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException: 권한이 없거나 사용자를 찾을 수 없는 경우
    """
    # 관리자 권한 또는 자신의 정보 조회인 경우만 허용
    if "admin" not in current_user.scopes and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 정보 조회 권한이 없습니다"
        )
    
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    return db_user

@router.get("/users/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    disabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """사용자 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수
        limit: 최대 레코드 수
        disabled: 비활성화 여부 필터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        사용자 목록
        
    Raises:
        HTTPException: 권한이 없는 경우
    """
    # 관리자 권한 확인
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 목록 조회 권한이 없습니다"
        )
    
    users = list_users(db, skip=skip, limit=limit, disabled=disabled)
    return users

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """사용자 정보를 업데이트합니다.
    
    Args:
        user_id: 사용자 ID
        user_update: 업데이트할 정보
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        업데이트된 사용자 정보
        
    Raises:
        HTTPException: 권한이 없거나 사용자를 찾을 수 없는 경우
    """
    # 관리자 권한 또는 자신의 정보 업데이트인 경우만 허용
    if "admin" not in current_user.scopes and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 정보 업데이트 권한이 없습니다"
        )
    
    # 비밀번호가 포함된 경우 해싱
    if user_update.password:
        user_update.password = get_password_hash(user_update.password)
    
    db_user = update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """사용자를 삭제합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Raises:
        HTTPException: 권한이 없거나 사용자를 찾을 수 없는 경우
    """
    # 관리자 권한 확인
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 삭제 권한이 없습니다"
        )
    
    if not delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        ) 