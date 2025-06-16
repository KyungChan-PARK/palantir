"""
Palantir 테스트를 위한 공통 픽스처와 설정
"""

import os
import tempfile
import pytest
import yaml
from pathlib import Path
from typing import Generator, Dict, Any

# 테스트 데이터 경로
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """기본 테스트 설정을 제공합니다."""
    config = {
        "server": {"host": "localhost", "port": 8000, "debug": True},
        "database": {"type": "sqlite", "path": ":memory:"},
        "logging": {"level": "DEBUG", "file": None},
    }
    return config


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """임시 디렉토리를 제공합니다."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def temp_config_file(
    temp_dir: Path, test_config: Dict[str, Any]
) -> Generator[Path, None, None]:
    """임시 설정 파일을 생성합니다."""
    config_file = temp_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.safe_dump(test_config, f)
    yield config_file
    if config_file.exists():
        config_file.unlink()


@pytest.fixture(scope="function")
def mock_llm_response() -> Dict[str, Any]:
    """LLM 응답을 모킹합니다."""
    return {
        "id": "test-response-id",
        "choices": [{"text": "Test response", "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


@pytest.fixture(scope="function")
def mock_db(temp_dir: Path) -> Generator[Path, None, None]:
    """테스트용 SQLite 데이터베이스를 생성합니다."""
    db_file = temp_dir / "test.db"
    yield db_file
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(scope="function")
def mock_agent_config() -> Dict[str, Any]:
    """에이전트 설정을 모킹합니다."""
    return {
        "name": "test_agent",
        "type": "planner",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
    }


@pytest.fixture(scope="function")
def mock_mcp_config() -> Dict[str, Any]:
    """MCP 설정을 모킹합니다."""
    return {
        "llm": {"default_model": "gpt-4", "timeout": 30, "retry_attempts": 3},
        "file": {"max_size": 1048576, "allowed_types": ["py", "txt", "md"]},
        "git": {"remote": "origin", "branch": "main"},
    }


@pytest.fixture(scope="function")
def mock_api_client(test_config: Dict[str, Any]):
    """API 클라이언트를 모킹합니다."""
    from fastapi.testclient import TestClient
    from palantir.api.main import app

    client = TestClient(app)
    return client


@pytest.fixture(scope="function")
def mock_auth_token() -> str:
    """인증 토큰을 모킹합니다."""
    return "test.auth.token"


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """테스트 환경을 설정합니다."""
    # 테스트용 환경 변수 설정
    os.environ["PALANTIR_ENV"] = "test"
    os.environ["PALANTIR_CONFIG_DIR"] = str(TEST_DATA_DIR)
    os.environ["PALANTIR_LOG_LEVEL"] = "DEBUG"

    yield

    # 테스트 후 정리
    if "PALANTIR_ENV" in os.environ:
        del os.environ["PALANTIR_ENV"]
    if "PALANTIR_CONFIG_DIR" in os.environ:
        del os.environ["PALANTIR_CONFIG_DIR"]
    if "PALANTIR_LOG_LEVEL" in os.environ:
        del os.environ["PALANTIR_LOG_LEVEL"]
