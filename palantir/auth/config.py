import os
from pydantic_settings import BaseSettings
from typing import Optional
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from ..core.config import Settings

class AuthSettings(BaseSettings):
    SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "")
    JWT_LIFETIME_SECONDS: int = int(os.getenv("JWT_LIFETIME_SECONDS", "3600"))
    ALGORITHM: str = "HS256"
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv(
        "AUTH_DATABASE_URL",
        "sqlite:///./users.db"  # 개발 환경 기본값
    )
    
    # 비밀번호 정책
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_SPECIAL_CHAR: bool = True
    REQUIRE_NUMBER: bool = True
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    
    # 레이트 리미팅
    RATE_LIMIT_PER_MINUTE: int = 5
    
    class Config:
        env_file = ".env"

settings = AuthSettings()

bearer_transport = BearerTransport(tokenUrl="auth/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.AUTH_SECRET_KEY,
        lifetime_seconds=settings.JWT_LIFETIME_SECONDS
    )

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
) 