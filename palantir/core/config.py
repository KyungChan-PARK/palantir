"""애플리케이션 설정 모듈."""

import os
import secrets
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정 클래스."""
    
    # 보안 설정
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./users.db"
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    # API 설정
    API_PREFIX: str = "/api"
    API_TITLE: str = "Palantir API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Palantir API 서버"
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Rate Limiting 설정
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    class Config:
        """설정 클래스 설정."""
        env_file = ".env"
        case_sensitive = True

# 설정 인스턴스 생성
settings = Settings()
