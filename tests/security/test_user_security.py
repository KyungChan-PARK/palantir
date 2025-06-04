"""사용자 관리 시스템 보안 테스트 모듈."""

import time
from datetime import timedelta

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palantir.core.auth import create_access_token, get_password_hash
from palantir.core.user import Base, UserDB
from palantir.main import app

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
        username="security_test_user",
        email="security_test@example.com",
        full_name="Security Test User",
        hashed_password=get_password_hash("test_password"),
        scopes=["user"],
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


async def test_password_security(async_client, test_user):
    """비밀번호 보안 테스트."""
    # 1. 약한 비밀번호 검증
    weak_passwords = [
        "password",
        "123456",
        "qwerty",
        "admin123",
        "test123",
        "password123",
        "abc123",
        "letmein",
        "welcome",
        "monkey123",
    ]

    for password in weak_passwords:
        response = await async_client.post(
            "/users/",
            headers={
                "Authorization": f"Bearer {create_access_token(data={'sub': 'admin', 'scopes': ['admin']})}"
            },
            json={
                "username": f"weak_pass_user_{password}",
                "email": f"weak_pass_{password}@example.com",
                "password": password,
                "full_name": "Weak Password User",
                "scopes": ["user"],
            },
        )
        assert response.status_code == 400, f"약한 비밀번호가 허용됨: {password}"

    # 2. 비밀번호 복잡성 검증
    strong_password = "P@ssw0rd!2024"
    response = await async_client.post(
        "/users/",
        headers={
            "Authorization": f"Bearer {create_access_token(data={'sub': 'admin', 'scopes': ['admin']})}"
        },
        json={
            "username": "strong_pass_user",
            "email": "strong_pass@example.com",
            "password": strong_password,
            "full_name": "Strong Password User",
            "scopes": ["user"],
        },
    )
    assert response.status_code == 201


async def test_token_security(async_client, test_user):
    """토큰 보안 테스트."""
    # 1. 만료된 토큰 테스트
    expired_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes},
        expires_delta=timedelta(microseconds=1),
    )
    time.sleep(0.1)  # 토큰 만료 대기

    response = await async_client.get(
        "/users/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

    # 2. 잘못된 서명 토큰 테스트
    invalid_token = expired_token[:-1] + "X"
    response = await async_client.get(
        "/users/me", headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert response.status_code == 401

    # 3. 토큰 탈취 방지 테스트
    valid_token = create_access_token(
        data={"sub": test_user.username, "scopes": test_user.scopes}
    )

    # 토큰 사용
    response = await async_client.get(
        "/users/me", headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200

    # 동일 토큰 재사용 시도
    response = await async_client.get(
        "/users/me", headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 401


async def test_sql_injection_prevention(async_client, test_user):
    """SQL 인젝션 방지 테스트."""
    # SQL 인젝션 시도
    injection_attempts = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users; --",
        "' OR 1=1; --",
        "admin' --",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "' OR '1'='1'/*",
        "admin'/*",
        "' OR '1'='1' LIMIT 1; --",
    ]

    for attempt in injection_attempts:
        response = await async_client.post(
            "/auth/token", data={"username": attempt, "password": attempt}
        )
        assert response.status_code == 401


async def test_xss_prevention(async_client, test_user):
    """XSS 공격 방지 테스트."""
    # XSS 공격 시도
    xss_attempts = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg/onload=alert('XSS')>",
        "'-alert('XSS')-'",
        "<script>fetch('http://evil.com')</script>",
        "<img src=x onerror=eval(atob('YWxlcnQoJ1hTUycp'))>",
        "<script>document.location='http://evil.com'</script>",
        "<iframe src=javascript:alert('XSS')></iframe>",
        "<body onload=alert('XSS')>",
    ]

    for attempt in xss_attempts:
        response = await async_client.put(
            f"/users/{test_user.id}",
            headers={
                "Authorization": f"Bearer {create_access_token(data={'sub': test_user.username, 'scopes': test_user.scopes})}"
            },
            json={"full_name": attempt, "email": f"{attempt}@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert attempt not in data["full_name"]
        assert attempt not in data["email"]


async def test_csrf_prevention(async_client, test_user):
    """CSRF 공격 방지 테스트."""
    # CSRF 토큰 없이 요청 시도
    response = await async_client.post(
        "/users/",
        headers={
            "Authorization": f"Bearer {create_access_token(data={'sub': 'admin', 'scopes': ['admin']})}",
            "Origin": "http://evil.com",
        },
        json={
            "username": "csrf_test_user",
            "email": "csrf_test@example.com",
            "password": "password123",
            "full_name": "CSRF Test User",
            "scopes": ["user"],
        },
    )
    assert response.status_code == 403


async def test_rate_limiting(async_client, test_user):
    """요청 제한 테스트."""
    # 빠른 연속 요청
    for _ in range(100):
        response = await async_client.post(
            "/auth/token",
            data={"username": test_user.username, "password": "wrong_password"},
        )

    # 마지막 요청이 제한되어야 함
    assert response.status_code == 429


async def test_input_validation(async_client, test_user):
    """입력값 검증 테스트."""
    # 잘못된 이메일 형식
    response = await async_client.put(
        f"/users/{test_user.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(data={'sub': test_user.username, 'scopes': test_user.scopes})}"
        },
        json={"email": "invalid_email"},
    )
    assert response.status_code == 422

    # 잘못된 사용자 이름 형식
    response = await async_client.put(
        f"/users/{test_user.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(data={'sub': test_user.username, 'scopes': test_user.scopes})}"
        },
        json={"username": "invalid username"},
    )
    assert response.status_code == 422

    # 잘못된 권한 범위
    response = await async_client.put(
        f"/users/{test_user.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(data={'sub': test_user.username, 'scopes': test_user.scopes})}"
        },
        json={"scopes": ["invalid_scope"]},
    )
    assert response.status_code == 422


async def test_session_security(async_client, test_user):
    """세션 보안 테스트."""
    # 1. 로그인
    response = await async_client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "test_password"},
    )
    assert response.status_code == 200
    tokens = response.json()

    # 2. 로그아웃
    response = await async_client.post(
        "/auth/logout", data={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200

    # 3. 로그아웃된 토큰으로 접근 시도
    response = await async_client.get(
        "/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 401

    # 4. 리프레시 토큰 재사용 시도
    response = await async_client.post(
        "/auth/refresh", data={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 401
