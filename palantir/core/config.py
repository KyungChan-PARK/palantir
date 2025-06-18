"""시스템 설정 관리"""

from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """시스템 설정"""
    
    # 기본 설정
    OFFLINE_MODE: bool = False
    LLM_PROVIDER: str = "openai"
    SECRET_KEY: str = "development-secret-key"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600

    # LLM 설정
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-4"
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 성능 설정
    PERFORMANCE_THRESHOLD: float = 0.8
    MAX_CONCURRENT_TASKS: int = 5
    TASK_TIMEOUT: int = 300

    # 모니터링 설정
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000

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

    # MCP 설정
    mcp_api_key: str = "test-mcp-key"
    mcp_base_url: str = "http://localhost:8000"
    openai_api_key: str = "test-openai-key"
    db_path: str = "./data/agent.db"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()
