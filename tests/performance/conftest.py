"""성능 테스트 설정 모듈."""

import asyncio
import time
from typing import Any, Dict

import aiohttp
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palantir.core.security import get_password_hash
from palantir.core.user import Base, UserDB

# 테스트 데이터베이스 URL
TEST_DATABASE_URL = "sqlite:///./test_performance.db"

# 테스트용 엔진 생성
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """데이터베이스 엔진 픽스처."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """데이터베이스 세션 픽스처."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
async def async_client():
    """비동기 HTTP 클라이언트 픽스처."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def test_user(db_session) -> Dict[str, Any]:
    """테스트 사용자 픽스처."""
    user = UserDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("Test123!@#"),
        disabled=False,
        scopes=["user"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "scopes": user.scopes,
    }


class PerformanceMetrics:
    """성능 메트릭 수집 클래스."""

    def __init__(self):
        self.response_times = []
        self.start_time = None
        self.end_time = None

    def start(self):
        """측정 시작."""
        self.start_time = time.time()

    def stop(self):
        """측정 종료."""
        self.end_time = time.time()
        self.response_times.append(self.end_time - self.start_time)

    def get_statistics(self) -> Dict[str, float]:
        """통계 정보 반환."""
        if not self.response_times:
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0, "p99": 0}

        sorted_times = sorted(self.response_times)
        return {
            "min": min(self.response_times),
            "max": max(self.response_times),
            "mean": sum(self.response_times) / len(self.response_times),
            "median": sorted_times[len(sorted_times) // 2],
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
        }

    def reset(self):
        """메트릭 초기화."""
        self.response_times = []
        self.start_time = None
        self.end_time = None


@pytest.fixture
def metrics():
    """성능 메트릭 픽스처."""
    return PerformanceMetrics()
