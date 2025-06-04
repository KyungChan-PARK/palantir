"""사용자 관리 시스템 통합 테스트 모듈."""

import pytest
import httpx
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palantir.core.user import Base, UserDB, UserCreate
from palantir.core.auth import create_access_token, get_password_hash
from palantir.main import app

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
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
def test_user(db_session):
    """테스트용 사용자를 생성합니다."""
    user = UserDB(
        username="integration_test_user",
        email="integration_test@example.com",
        full_name="Integration Test User",
        hashed_password=get_password_hash("test_password"),
        scopes=["user"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="module")
def admin_user(db_session):
    """테스트용 관리자 사용자를 생성합니다."""
    user = UserDB(
        username="integration_admin",
        email="integration_admin@example.com",
        full_name="Integration Admin User",
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

async def test_user_lifecycle(async_client, admin_user, test_user):
    """사용자 생명주기 테스트."""
    # 1. 관리자 로그인
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    # 2. 새 사용자 생성
    new_user_data = {
        "username": "new_integration_user",
        "email": "new_integration@example.com",
        "password": "new_password",
        "full_name": "New Integration User",
        "scopes": ["user"]
    }
    
    response = await async_client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_user_data
    )
    assert response.status_code == 201
    created_user = response.json()
    
    # 3. 생성된 사용자로 로그인
    new_user_token = create_access_token(
        data={"sub": created_user["username"], "scopes": created_user["scopes"]}
    )
    
    # 4. 사용자 정보 조회
    response = await async_client.get(
        f"/users/{created_user['id']}",
        headers={"Authorization": f"Bearer {new_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == new_user_data["username"]
    
    # 5. 사용자 정보 업데이트
    update_data = {
        "full_name": "Updated Integration User",
        "email": "updated_integration@example.com"
    }
    response = await async_client.put(
        f"/users/{created_user['id']}",
        headers={"Authorization": f"Bearer {new_user_token}"},
        json=update_data
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == update_data["full_name"]
    
    # 6. 사용자 삭제
    response = await async_client.delete(
        f"/users/{created_user['id']}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

async def test_concurrent_user_operations(async_client, admin_user):
    """동시 사용자 작업 테스트."""
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    # 여러 사용자 동시 생성
    user_data_list = [
        {
            "username": f"concurrent_user_{i}",
            "email": f"concurrent_{i}@example.com",
            "password": "password123",
            "full_name": f"Concurrent User {i}",
            "scopes": ["user"]
        }
        for i in range(5)
    ]
    
    # 비동기로 여러 사용자 생성
    responses = await asyncio.gather(*[
        async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        for user_data in user_data_list
    ])
    
    # 모든 생성 요청이 성공했는지 확인
    assert all(response.status_code == 201 for response in responses)
    
    # 생성된 사용자 ID 수집
    created_user_ids = [response.json()["id"] for response in responses]
    
    # 동시에 여러 사용자 정보 조회
    get_responses = await asyncio.gather(*[
        async_client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        for user_id in created_user_ids
    ])
    
    # 모든 조회 요청이 성공했는지 확인
    assert all(response.status_code == 200 for response in get_responses)
    
    # 동시에 여러 사용자 삭제
    delete_responses = await asyncio.gather(*[
        async_client.delete(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        for user_id in created_user_ids
    ])
    
    # 모든 삭제 요청이 성공했는지 확인
    assert all(response.status_code == 204 for response in delete_responses)

async def test_user_authentication_flow(async_client, test_user):
    """사용자 인증 흐름 테스트."""
    # 1. 로그인 시도 (잘못된 비밀번호)
    response = await async_client.post(
        "/auth/token",
        data={
            "username": test_user.username,
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
    
    # 2. 올바른 비밀번호로 로그인
    response = await async_client.post(
        "/auth/token",
        data={
            "username": test_user.username,
            "password": "test_password"
        }
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    # 3. 액세스 토큰으로 API 접근
    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    
    # 4. 리프레시 토큰으로 새 액세스 토큰 발급
    response = await async_client.post(
        "/auth/refresh",
        data={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    
    # 5. 로그아웃
    response = await async_client.post(
        "/auth/logout",
        data={"refresh_token": new_tokens["refresh_token"]}
    )
    assert response.status_code == 200
    
    # 6. 로그아웃된 토큰으로 접근 시도
    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    )
    assert response.status_code == 401

async def test_user_permission_boundaries(async_client, test_user, admin_user):
    """사용자 권한 경계 테스트."""
    # 일반 사용자 토큰
    user_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes}
    )
    
    # 관리자 토큰
    admin_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )
    
    # 1. 일반 사용자가 다른 사용자 생성 시도
    response = await async_client.post(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "username": "unauthorized_user",
            "email": "unauthorized@example.com",
            "password": "password123",
            "full_name": "Unauthorized User",
            "scopes": ["user"]
        }
    )
    assert response.status_code == 403
    
    # 2. 일반 사용자가 사용자 목록 조회 시도
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    
    # 3. 일반 사용자가 다른 사용자 정보 수정 시도
    response = await async_client.put(
        f"/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"full_name": "Hacked Admin"}
    )
    assert response.status_code == 403
    
    # 4. 일반 사용자가 다른 사용자 삭제 시도
    response = await async_client.delete(
        f"/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    
    # 5. 관리자가 모든 작업 수행 가능
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    response = await async_client.put(
        f"/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"disabled": True}
    )
    assert response.status_code == 200 