"""사용자 관리 시스템 테스트 모듈."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palantir.core.auth import create_access_token
from palantir.core.database import get_db
from palantir.core.user import Base, UserDB
from palantir.core.user_api import router

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """테스트용 데이터베이스 세션을 생성합니다."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자를 생성합니다."""
    user = UserDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        scopes=["user"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """테스트용 관리자 사용자를 생성합니다."""
    user = UserDB(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        scopes=["admin"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_client(db_session):
    """테스트용 FastAPI 클라이언트를 생성합니다."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_user(test_client, admin_user):
    """사용자 생성 테스트."""
    # 관리자 토큰 생성
    access_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )

    # 새 사용자 생성
    response = test_client.post(
        "/users/",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "full_name": "New User",
            "scopes": ["user"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "user" in data["scopes"]


def test_create_user_duplicate_username(test_client, admin_user, test_user):
    """중복된 사용자 이름으로 사용자 생성 시도 테스트."""
    access_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )

    response = test_client.post(
        "/users/",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "testuser",  # 이미 존재하는 사용자 이름
            "email": "another@example.com",
            "password": "password123",
            "full_name": "Another User",
            "scopes": ["user"],
        },
    )

    assert response.status_code == 400
    assert "이미 사용 중인 사용자 이름입니다" in response.json()["detail"]


def test_get_current_user(test_client, test_user):
    """현재 사용자 정보 조회 테스트."""
    access_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes}
    )

    response = test_client.get(
        "/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_get_user(test_client, test_user, admin_user):
    """특정 사용자 정보 조회 테스트."""
    access_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )

    response = test_client.get(
        f"/users/{test_user.id}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_update_user(test_client, test_user):
    """사용자 정보 업데이트 테스트."""
    access_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes}
    )

    response = test_client.put(
        f"/users/{test_user.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"full_name": "Updated Name", "email": "updated@example.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "updated@example.com"


def test_delete_user(test_client, admin_user, test_user):
    """사용자 삭제 테스트."""
    access_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )

    response = test_client.delete(
        f"/users/{test_user.id}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204

    # 삭제 확인
    response = test_client.get(
        f"/users/{test_user.id}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404


def test_list_users(test_client, admin_user, test_user):
    """사용자 목록 조회 테스트."""
    access_token = create_access_token(
        data={"sub": admin_user.username, "scopes": admin_user.scopes}
    )

    response = test_client.get(
        "/users/", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # admin_user와 test_user가 포함되어 있어야 함
    usernames = [user["username"] for user in data]
    assert "admin" in usernames
    assert "testuser" in usernames


def test_unauthorized_access(test_client):
    """인증되지 않은 접근 테스트."""
    # 토큰 없이 접근
    response = test_client.get("/users/me")
    assert response.status_code == 401

    # 잘못된 토큰으로 접근
    response = test_client.get(
        "/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_forbidden_access(test_client, test_user):
    """권한이 없는 접근 테스트."""
    access_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes}
    )

    # 일반 사용자가 사용자 목록 조회 시도
    response = test_client.get(
        "/users/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403
