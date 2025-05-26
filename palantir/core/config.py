import os
from typing import Optional

class Config:
    pass 

class Settings:
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "False").lower() == "true"
    LOCAL_MODELS_PATH: Optional[str] = os.getenv("LOCAL_MODELS_PATH", None)
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080") 