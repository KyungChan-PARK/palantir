"""API 성능 테스트 모듈."""

import asyncio

import pytest

from palantir.core.security import create_access_token

pytestmark = pytest.mark.asyncio

async def test_user_creation_performance(
    async_client,
    metrics,
    db_session
):
    """사용자 생성 성능 테스트."""
    # 테스트 데이터 준비
    users = [
        {
            "username": f"testuser{i}",
            "email": f"test{i}@example.com",
            "password": "Test123!@#",
            "full_name": f"Test User {i}",
            "scopes": ["user"]
        }
        for i in range(100)
    ]
    
    # 관리자 토큰 생성
    admin_token = create_access_token({"sub": "admin", "scopes": ["admin"]})
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 성능 측정
    for user in users:
        metrics.start()
        async with async_client.post(
            "http://localhost:8000/api/users/",
            json=user,
            headers=headers
        ) as response:
            metrics.stop()
            assert response.status == 201
    
    # 결과 분석
    stats = metrics.get_statistics()
    print("\n사용자 생성 성능 테스트 결과:")
    print(f"최소 응답 시간: {stats['min']:.3f}초")
    print(f"최대 응답 시간: {stats['max']:.3f}초")
    print(f"평균 응답 시간: {stats['mean']:.3f}초")
    print(f"중앙값 응답 시간: {stats['median']:.3f}초")
    print(f"95퍼센타일 응답 시간: {stats['p95']:.3f}초")
    print(f"99퍼센타일 응답 시간: {stats['p99']:.3f}초")

async def test_user_retrieval_performance(
    async_client,
    metrics,
    db_session,
    test_user
):
    """사용자 조회 성능 테스트."""
    # 토큰 생성
    token = create_access_token({"sub": test_user["username"], "scopes": test_user["scopes"]})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 성능 측정
    for _ in range(1000):
        metrics.start()
        async with async_client.get(
            f"http://localhost:8000/api/users/{test_user['id']}",
            headers=headers
        ) as response:
            metrics.stop()
            assert response.status == 200
    
    # 결과 분석
    stats = metrics.get_statistics()
    print("\n사용자 조회 성능 테스트 결과:")
    print(f"최소 응답 시간: {stats['min']:.3f}초")
    print(f"최대 응답 시간: {stats['max']:.3f}초")
    print(f"평균 응답 시간: {stats['mean']:.3f}초")
    print(f"중앙값 응답 시간: {stats['median']:.3f}초")
    print(f"95퍼센타일 응답 시간: {stats['p95']:.3f}초")
    print(f"99퍼센타일 응답 시간: {stats['p99']:.3f}초")

async def test_concurrent_user_operations(
    async_client,
    metrics,
    db_session
):
    """동시 사용자 작업 성능 테스트."""
    # 테스트 데이터 준비
    users = [
        {
            "username": f"concurrent_user{i}",
            "email": f"concurrent{i}@example.com",
            "password": "Test123!@#",
            "full_name": f"Concurrent User {i}",
            "scopes": ["user"]
        }
        for i in range(50)
    ]
    
    # 관리자 토큰 생성
    admin_token = create_access_token({"sub": "admin", "scopes": ["admin"]})
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 동시 작업 실행
    async def create_user(user_data):
        async with async_client.post(
            "http://localhost:8000/api/users/",
            json=user_data,
            headers=headers
        ) as response:
            return response.status
    
    metrics.start()
    tasks = [create_user(user) for user in users]
    results = await asyncio.gather(*tasks)
    metrics.stop()
    
    # 결과 검증
    assert all(status == 201 for status in results)
    
    # 결과 분석
    total_time = metrics.end_time - metrics.start_time
    print("\n동시 사용자 작업 성능 테스트 결과:")
    print(f"총 처리 시간: {total_time:.3f}초")
    print(f"초당 처리량: {len(users) / total_time:.2f} 요청/초")

async def test_authentication_performance(
    async_client,
    metrics
):
    """인증 성능 테스트."""
    # 테스트 데이터
    auth_data = {
        "username": "testuser",
        "password": "Test123!@#"
    }
    
    # 성능 측정
    for _ in range(1000):
        metrics.start()
        async with async_client.post(
            "http://localhost:8000/api/auth/token",
            data=auth_data
        ) as response:
            metrics.stop()
            assert response.status == 200
    
    # 결과 분석
    stats = metrics.get_statistics()
    print("\n인증 성능 테스트 결과:")
    print(f"최소 응답 시간: {stats['min']:.3f}초")
    print(f"최대 응답 시간: {stats['max']:.3f}초")
    print(f"평균 응답 시간: {stats['mean']:.3f}초")
    print(f"중앙값 응답 시간: {stats['median']:.3f}초")
    print(f"95퍼센타일 응답 시간: {stats['p95']:.3f}초")
    print(f"99퍼센타일 응답 시간: {stats['p99']:.3f}초")

async def test_database_connection_pool(
    async_client,
    metrics,
    db_session
):
    """데이터베이스 연결 풀 성능 테스트."""
    # 토큰 생성
    token = create_access_token({"sub": "testuser", "scopes": ["user"]})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 동시 연결 테스트
    async def make_request():
        async with async_client.get(
            "http://localhost:8000/api/users/me",
            headers=headers
        ) as response:
            return response.status
    
    metrics.start()
    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    metrics.stop()
    
    # 결과 검증
    assert all(status == 200 for status in results)
    
    # 결과 분석
    total_time = metrics.end_time - metrics.start_time
    print("\n데이터베이스 연결 풀 성능 테스트 결과:")
    print(f"총 처리 시간: {total_time:.3f}초")
    print(f"초당 처리량: {len(tasks) / total_time:.2f} 요청/초")

async def test_memory_usage(
    async_client,
    metrics,
    db_session
):
    """메모리 사용량 테스트."""
    import os

    import psutil
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 대량의 사용자 생성
    users = [
        {
            "username": f"memory_test_user{i}",
            "email": f"memory_test{i}@example.com",
            "password": "Test123!@#",
            "full_name": f"Memory Test User {i}",
            "scopes": ["user"]
        }
        for i in range(1000)
    ]
    
    admin_token = create_access_token({"sub": "admin", "scopes": ["admin"]})
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    for user in users:
        async with async_client.post(
            "http://localhost:8000/api/users/",
            json=user,
            headers=headers
        ) as response:
            assert response.status == 201
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print("\n메모리 사용량 테스트 결과:")
    print(f"초기 메모리 사용량: {initial_memory:.2f}MB")
    print(f"최종 메모리 사용량: {final_memory:.2f}MB")
    print(f"메모리 증가량: {memory_increase:.2f}MB")
    print(f"사용자당 메모리 사용량: {memory_increase/1000:.2f}MB") 