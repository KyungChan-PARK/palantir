"""Application configuration utilities."""

from typing import Optional

from pydantic import BaseSettings


class Config:
    """Placeholder for future configuration logic."""

    pass


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    OFFLINE_MODE: bool = False
    LOCAL_MODELS_PATH: Optional[str] = None
    WEAVIATE_URL: str = "http://localhost:8080"
    LLM_PROVIDER: str = "openai"

    class Config:
        env_prefix = ""


settings = Settings()
