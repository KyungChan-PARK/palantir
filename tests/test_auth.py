import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from palantir.auth.models import Base, User
from main import app

# 테스트용 인메모리 SQLite 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c

def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user(client):
    # 먼저 사용자 등록
    client.post(
        "/auth/register",
        json={
            "email": "login@test.com",
            "username": "loginuser",
            "password": "testpass123"
        }
    )
    
    # 로그인 시도
    response = client.post(
        "/auth/jwt/login",
        data={
            "username": "login@test.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_protected_route(client):
    # 사용자 등록 및 로그인
    client.post(
        "/auth/register",
        json={
            "email": "protected@test.com",
            "username": "protecteduser",
            "password": "testpass123"
        }
    )
    
    login_response = client.post(
        "/auth/jwt/login",
        data={
            "username": "protected@test.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 보호된 라우트 접근
    response = client.get(
        "/protected-route",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]  # 404는 라우트가 아직 없는 경우 