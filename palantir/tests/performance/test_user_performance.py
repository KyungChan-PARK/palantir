"""사용자 관리 시스템 성능 테스트 모듈."""

import asyncio
import statistics
import time
from typing import Dict, List

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palantir.core.auth import create_access_token, get_password_hash
from palantir.core.user import Base, UserDB
from palantir.main import app

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    """테스트용 데이터베이스 세션을 생성합니다."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def admin_user(db_session):
    """테스트용 관리자 사용자를 생성합니다."""
    user = UserDB(
        username="performance_admin",
        email="performance_admin@example.com",
        full_name="Performance Test Admin",
        hashed_password=get_password_hash("admin_password"),
        scopes=["admin"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="module")
async def async_client():
    """비동기 HTTP 클라이언트를 생성합니다."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

class PerformanceMetrics:
    """성능 메트릭을 수집하고 분석하는 클래스."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.start_time = time.time()
    
    def add_response_time(self, response_time: float):
        """응답 시간을 추가합니다."""
        self.response_times.append(response_time)
    
    def get_statistics(self) -> Dict[str, float]:
        """성능 통계를 계산합니다."""
        if not self.response_times:
            return {}
        
        return {
            "count": len(self.response_times),
            "min": min(self.response_times),
            "max": max(self.response_times),
            "mean": statistics.mean(self.response_times),
            "median": statistics.median(self.response_times),
            "p95": statistics.quantiles(self.response_times, n=20)[18],
            "p99": statistics.quantiles(self.response_times, n=100)[98],
            "total_time": time.time() - self.start_time
        }

async def test_user_creation_performance(async_client, admin_user):
    """사용자 생성 성능 테스트."""
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    metrics = PerformanceMetrics()
    num_users = 100
    
    # 사용자 생성 성능 테스트
    for i in range(num_users):
        start_time = time.time()
        response = await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": f"perf_user_{i}",
                "email": f"perf_{i}@example.com",
                "password": "password123",
                "full_name": f"Performance User {i}",
                "scopes": ["user"]
            }
        )
        response_time = time.time() - start_time
        metrics.add_response_time(response_time)
        assert response.status_code == 201
    
    stats = metrics.get_statistics()
    print("\n사용자 생성 성능 통계:")
    for key, value in stats.items():
        print(f"{key}: {value:.3f}초")

async def test_user_retrieval_performance(async_client, admin_user):
    """사용자 조회 성능 테스트."""
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    metrics = PerformanceMetrics()
    num_requests = 1000
    
    # 사용자 목록 조회 성능 테스트
    for _ in range(num_requests):
        start_time = time.time()
        response = await async_client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        response_time = time.time() - start_time
        metrics.add_response_time(response_time)
        assert response.status_code == 200
    
    stats = metrics.get_statistics()
    print("\n사용자 조회 성능 통계:")
    for key, value in stats.items():
        print(f"{key}: {value:.3f}초")

async def test_concurrent_user_operations_performance(async_client, admin_user):
    """동시 사용자 작업 성능 테스트."""
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    metrics = PerformanceMetrics()
    num_concurrent_operations = 50
    
    # 동시 사용자 생성
    start_time = time.time()
    user_data_list = [
        {
            "username": f"concurrent_perf_{i}",
            "email": f"concurrent_perf_{i}@example.com",
            "password": "password123",
            "full_name": f"Concurrent Performance User {i}",
            "scopes": ["user"]
        }
        for i in range(num_concurrent_operations)
    ]
    
    responses = await asyncio.gather(*[
        async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        for user_data in user_data_list
    ])
    
    total_time = time.time() - start_time
    metrics.add_response_time(total_time)
    
    assert all(response.status_code == 201 for response in responses)
    
    stats = metrics.get_statistics()
    print("\n동시 사용자 작업 성능 통계:")
    for key, value in stats.items():
        print(f"{key}: {value:.3f}초")

async def test_authentication_performance(async_client, admin_user):
    """인증 성능 테스트."""
    metrics = PerformanceMetrics()
    num_requests = 1000
    
    # 토큰 생성 성능 테스트
    for _ in range(num_requests):
        start_time = time.time()
        response = await async_client.post(
            "/auth/token",
            data={
                "username": admin_user.username,
                "password": "admin_password"
            }
        )
        response_time = time.time() - start_time
        metrics.add_response_time(response_time)
        assert response.status_code == 200
    
    stats = metrics.get_statistics()
    print("\n인증 성능 통계:")
    for key, value in stats.items():
        print(f"{key}: {value:.3f}초")

async def test_database_connection_pool_performance(async_client, admin_user):
    """데이터베이스 연결 풀 성능 테스트."""
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    metrics = PerformanceMetrics()
    num_connections = 100
    
    # 동시 데이터베이스 연결 테스트
    start_time = time.time()
    responses = await asyncio.gather(*[
        async_client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        for _ in range(num_connections)
    ])
    
    total_time = time.time() - start_time
    metrics.add_response_time(total_time)
    
    assert all(response.status_code == 200 for response in responses)
    
    stats = metrics.get_statistics()
    print("\n데이터베이스 연결 풀 성능 통계:")
    for key, value in stats.items():
        print(f"{key}: {value:.3f}초")

async def test_memory_usage_performance(async_client, admin_user):
    """메모리 사용량 성능 테스트."""
    import os

    import psutil
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 대량의 사용자 생성
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    num_users = 1000
    for i in range(num_users):
        await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": f"memory_user_{i}",
                "email": f"memory_{i}@example.com",
                "password": "password123",
                "full_name": f"Memory Test User {i}",
                "scopes": ["user"]
            }
        )
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print("\n메모리 사용량 통계:")
    print(f"초기 메모리: {initial_memory:.2f}MB")
    print(f"최종 메모리: {final_memory:.2f}MB")
    print(f"메모리 증가량: {memory_increase:.2f}MB")
    print(f"사용자당 평균 메모리: {memory_increase/num_users:.2f}MB") 