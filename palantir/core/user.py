"""사용자 관리 시스템 모듈."""

import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    """사용자 데이터베이스 모델."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    scopes = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserCreate(BaseModel):
    """사용자 생성 모델."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 모델."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    disabled: Optional[bool] = None
    scopes: Optional[List[str]] = None

class UserResponse(BaseModel):
    """사용자 응답 모델."""
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str]
    disabled: bool
    scopes: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

def get_db():
    """데이터베이스 세션을 가져옵니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: SessionLocal, user: UserCreate, hashed_password: str) -> UserDB:
    """새로운 사용자를 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        user: 생성할 사용자 정보
        hashed_password: 해시된 비밀번호
        
    Returns:
        생성된 사용자 정보
    """
    db_user = UserDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        scopes=user.scopes
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"새로운 사용자 생성: {user.username}")
    return db_user

def get_user_by_username(db: SessionLocal, username: str) -> Optional[UserDB]:
    """사용자 이름으로 사용자를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        username: 사용자 이름
        
    Returns:
        사용자 정보 또는 None
    """
    return db.query(UserDB).filter(UserDB.username == username).first()

def get_user_by_email(db: SessionLocal, email: str) -> Optional[UserDB]:
    """이메일로 사용자를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        email: 이메일 주소
        
    Returns:
        사용자 정보 또는 None
    """
    return db.query(UserDB).filter(UserDB.email == email).first()

def update_user(db: SessionLocal, user_id: str, user_update: UserUpdate) -> Optional[UserDB]:
    """사용자 정보를 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        user_update: 업데이트할 정보
        
    Returns:
        업데이트된 사용자 정보 또는 None
    """
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    logger.info(f"사용자 정보 업데이트: {db_user.username}")
    return db_user

def delete_user(db: SessionLocal, user_id: str) -> bool:
    """사용자를 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        
    Returns:
        삭제 성공 여부
    """
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    logger.info(f"사용자 삭제: {db_user.username}")
    return True

def list_users(
    db: SessionLocal,
    skip: int = 0,
    limit: int = 100,
    disabled: Optional[bool] = None
) -> List[UserDB]:
    """사용자 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수
        limit: 최대 레코드 수
        disabled: 비활성화 여부 필터
        
    Returns:
        사용자 목록
    """
    query = db.query(UserDB)
    if disabled is not None:
        query = query.filter(UserDB.disabled == disabled)
    return query.offset(skip).limit(limit).all()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine) 