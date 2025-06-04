"""인증 시스템 모듈."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Form, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수에서 설정 가져오기
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# 메모리 기반 블랙리스트 (운영은 Redis 등 권장)
refresh_blacklist: Set[str] = set()

class Token(BaseModel):
    """토큰 모델."""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """토큰 데이터 모델."""
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    """사용자 모델."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: list[str] = []

class UserInDB(User):
    """DB에 저장된 사용자 모델."""
    hashed_password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호를 검증합니다.
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
        
    Returns:
        검증 결과
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호를 해시합니다.
    
    Args:
        password: 평문 비밀번호
        
    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰을 생성합니다.
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간
        
    Returns:
        생성된 액세스 토큰
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """리프레시 토큰을 생성합니다.
    
    Args:
        data: 토큰에 포함할 데이터
        
    Returns:
        생성된 리프레시 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def blacklist_refresh_token(token: str) -> None:
    """리프레시 토큰을 블랙리스트에 추가합니다.
    
    Args:
        token: 블랙리스트에 추가할 토큰
    """
    try:
        # 토큰 검증
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            refresh_blacklist.add(jti)
            logger.info(f"토큰 블랙리스트 추가: {jti}")
    except JWTError as e:
        logger.error(f"토큰 블랙리스트 추가 실패: {e}")

def is_refresh_token_blacklisted(token: str) -> bool:
    """리프레시 토큰이 블랙리스트에 있는지 확인합니다.
    
    Args:
        token: 확인할 토큰
        
    Returns:
        블랙리스트 포함 여부
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        return jti in refresh_blacklist if jti else False
    except JWTError:
        return True

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """현재 인증된 사용자를 가져옵니다.
    
    Args:
        token: 액세스 토큰
        
    Returns:
        인증된 사용자 정보
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # TODO: 실제 사용자 DB에서 사용자 정보 조회
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_user(username: str) -> Optional[UserInDB]:
    """사용자 정보를 가져옵니다.
    
    Args:
        username: 사용자 이름
        
    Returns:
        사용자 정보 또는 None
    """
    # TODO: 실제 사용자 DB에서 사용자 정보 조회
    return None

router = APIRouter()

@router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """액세스 토큰을 발급합니다.
    
    Args:
        form_data: 로그인 폼 데이터
        
    Returns:
        발급된 토큰
        
    Raises:
        HTTPException: 인증 실패 시
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "scopes": user.scopes}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Form(...)):
    """리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다.
    
    Args:
        refresh_token: 리프레시 토큰
        
    Returns:
        새로 발급된 토큰
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 블랙리스트에 있는 경우
    """
    if is_refresh_token_blacklisted(refresh_token):
        raise HTTPException(
            status_code=401,
            detail="토큰이 취소되었습니다"
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="토큰이 유효하지 않습니다"
            )
        
        user = get_user(username=username)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="사용자를 찾을 수 없습니다"
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "scopes": user.scopes}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.username, "scopes": user.scopes}
        )
        
        # 기존 리프레시 토큰 블랙리스트에 추가
        blacklist_refresh_token(refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="토큰이 유효하지 않습니다"
        )

@router.post("/auth/logout")
async def logout(refresh_token: str):
    """로그아웃합니다.
    
    Args:
        refresh_token: 리프레시 토큰
        
    Returns:
        로그아웃 결과
    """
    blacklist_refresh_token(refresh_token)
    return {"message": "로그아웃되었습니다"}
