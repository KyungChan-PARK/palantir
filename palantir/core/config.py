"""Application configuration utilities."""

from typing import Optional
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "False").lower() == "true"
    LOCAL_MODELS_PATH: Optional[str] = os.getenv("LOCAL_MODELS_PATH", None)
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    LLM_PROVIDER: str = "openai"

    class Config:
        env_prefix = ""

settings = Settings()
