from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_root = Path(__file__).resolve().parent.parent.parent
_default_config_dir = _root / "config"

class Settings(BaseSettings):
    """애플리케이션 전역 설정.

    .env 파일 혹은 환경변수로 오버라이드 가능하며,
    `APP_ENV`(development|staging|production)에 따라 config/<env>.env 를 추가로 로드한다.
    """

    # 공통
    app_name: str = "Palantir AI Platform"
    debug: bool = False
    app_env: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = "sqlite:///./test.db"

    # JWT
    jwt_secret_key: str = "changeme"

    # model config
    model_config = SettingsConfigDict(env_file=_default_config_dir / ".env", env_prefix="PALANTIR_", extra="ignore")

    @classmethod
    @lru_cache()
    def load(cls) -> "Settings":
        env = cls().app_env  # prelim load to get env
        env_file = _default_config_dir / f"{env}.env"
        return cls(_env_file=env_file if env_file.exists() else None)


settings = Settings.load() 