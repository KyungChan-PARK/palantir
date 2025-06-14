from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    OFFLINE_MODE: bool = False
    LLM_PROVIDER: str = "openai"
    SECRET_KEY: str = "development-secret-key"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    
    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 인증 설정
    AUTH_SECRET_KEY: str = "development-auth-secret-key"
    JWT_LIFETIME_SECONDS: int = 3600
    AUTH_DATABASE_URL: str = "sqlite+aiosqlite:///./users.db"

    # SMTP 설정 (개발 환경용)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = "test@example.com"
    SMTP_PASSWORD: str = "dummy-password"
    SMTP_FROM_EMAIL: str = "test@example.com"

    # 레이트 리미팅
    RATE_LIMIT_PER_MINUTE: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
