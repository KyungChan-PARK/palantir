import pytest
import asyncio
import time
from typing import List, Dict
import random
import string

from palantir.services.user_service import UserService
from palantir.core.database import DatabaseManager
from palantir.models.user import User

@pytest.fixture(scope="module")
async def user_service(db_manager):
    """사용자 서비스를 초기화합니다."""
    return UserService(await db_manager.get_pool())

@pytest.fixture(scope="module")
async def test_users() -> List[Dict]:
    """테스트용 사용자 데이터를 생성합니다."""
    users = []
    for i in range(100):
        user = {
            "email": f"test{i}@example.com",
            "username": f"testuser{i}",
            "password": "".join(random.choices(string.ascii_letters + string.digits, k=12))
        }
        users.append(user)
    return users

async def test_user_creation_performance(user_service, test_users):
    """사용자 생성 성능을 테스트합니다."""
    start_time = time.time()
    
    # 100명의 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    duration = time.time() - start_time
    
    assert duration < 10.0  # 10초 이내에 완료되어야 함
    assert len(created_users) == 100
    
    return duration

async def test_user_retrieval_performance(user_service, test_users):
    """사용자 조회 성능을 테스트합니다."""
    # 먼저 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    start_time = time.time()
    
    # 1000번의 사용자 조회
    for _ in range(1000):
        user_id = random.choice(created_users).id
        user = await user_service.get_user_by_id(user_id)
        assert user is not None
    
    duration = time.time() - start_time
    
    assert duration < 5.0  # 5초 이내에 완료되어야 함
    return duration

async def test_concurrent_user_operations(user_service, test_users):
    """동시 사용자 작업 성능을 테스트합니다."""
    # 먼저 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    async def update_user(user_id: int):
        update_data = {
            "username": f"updated_{random.randint(1000, 9999)}"
        }
        return await user_service.update_user(user_id, update_data)
    
    start_time = time.time()
    
    # 50개의 동시 업데이트
    tasks = [update_user(user.id) for user in created_users[:50]]
    updated_users = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    
    assert duration < 5.0  # 5초 이내에 완료되어야 함
    assert len(updated_users) == 50
    
    return duration

async def test_authentication_performance(user_service, test_users):
    """인증 성능을 테스트합니다."""
    # 먼저 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    start_time = time.time()
    
    # 1000번의 인증 시도
    for _ in range(1000):
        user_data = random.choice(test_users)
        user = await user_service.authenticate_user(
            user_data["email"],
            user_data["password"]
        )
        assert user is not None
    
    duration = time.time() - start_time
    
    assert duration < 10.0  # 10초 이내에 완료되어야 함
    return duration

async def test_token_operations_performance(user_service, test_users):
    """토큰 작업 성능을 테스트합니다."""
    # 먼저 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    start_time = time.time()
    
    # 1000번의 토큰 생성 및 검증
    for _ in range(1000):
        user = random.choice(created_users)
        token = await user_service.create_access_token(user)
        verified_user = await user_service.verify_token(token)
        assert verified_user is not None
        assert verified_user.id == user.id
    
    duration = time.time() - start_time
    
    assert duration < 10.0  # 10초 이내에 완료되어야 함
    return duration

async def test_cache_hit_performance(user_service, test_users):
    """캐시 히트 성능을 테스트합니다."""
    # 먼저 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    # 첫 번째 조회 (캐시 미스)
    start_time = time.time()
    for user in created_users[:10]:
        await user_service.get_user_by_id(user.id)
    first_duration = time.time() - start_time
    
    # 두 번째 조회 (캐시 히트)
    start_time = time.time()
    for user in created_users[:10]:
        await user_service.get_user_by_id(user.id)
    second_duration = time.time() - start_time
    
    # 캐시 히트가 더 빨라야 함
    assert second_duration < first_duration
    assert second_duration < 1.0  # 1초 이내에 완료되어야 함
    
    return {"cache_miss": first_duration, "cache_hit": second_duration}

async def test_bulk_user_operations(user_service, test_users):
    """대량 사용자 작업 성능을 테스트합니다."""
    start_time = time.time()
    
    # 100명의 사용자 생성
    created_users = []
    for user_data in test_users:
        user = await user_service.create_user(user_data)
        created_users.append(user)
    
    # 100명의 사용자 정보 업데이트
    for user in created_users:
        update_data = {
            "username": f"bulk_updated_{random.randint(1000, 9999)}"
        }
        await user_service.update_user(user.id, update_data)
    
    # 100명의 사용자 삭제
    for user in created_users:
        await user_service.delete_user(user.id)
    
    duration = time.time() - start_time
    
    assert duration < 20.0  # 20초 이내에 완료되어야 함
    return duration 