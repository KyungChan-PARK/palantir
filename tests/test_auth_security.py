import pytest
from fastapi.testclient import TestClient
import time
from main import app
from palantir.auth.validators import validate_password, validate_email

client = TestClient(app)


def test_rate_limiting():
    """레이트 리미팅 테스트"""
    # 허용된 요청 수보다 많은 요청 시도
    for _ in range(10):
        response = client.post(
            "/auth/jwt/login",
            data={"username": "test@example.com", "password": "test123"},
        )
        if response.status_code == 429:
            break
        time.sleep(0.1)

    assert response.status_code == 429
    assert "너무 많은 요청이 발생했습니다" in response.json()["detail"]


def test_password_validation():
    """비밀번호 정책 테스트"""
    # 취약한 비밀번호 테스트
    weak_passwords = [
        "short",  # 너무 짧음
        "onlylowercase",  # 대문자 없음
        "ONLYUPPERCASE",  # 소문자 없음
        "NoSpecialChar1",  # 특수문자 없음
        "NoNumber!",  # 숫자 없음
    ]

    for password in weak_passwords:
        is_valid, errors = validate_password(password)
        assert not is_valid
        assert len(errors) > 0

    # 강력한 비밀번호 테스트
    strong_password = "StrongP@ssw0rd"
    is_valid, errors = validate_password(strong_password)
    assert is_valid
    assert len(errors) == 0


def test_email_validation():
    """이메일 유효성 검사 테스트"""
    invalid_emails = [
        "notanemail",
        "missing@dot",
        "@nodomain.com",
        "spaces in@email.com",
        "korean@한글.com",
    ]

    for email in invalid_emails:
        is_valid, errors = validate_email(email)
        assert not is_valid
        assert len(errors) > 0

    # 유효한 이메일 테스트
    valid_emails = [
        "test@example.com",
        "user.name+tag@example.co.kr",
        "first.last@subdomain.example.com",
    ]

    for email in valid_emails:
        is_valid, errors = validate_email(email)
        assert is_valid
        assert len(errors) == 0


def test_sql_injection_prevention():
    """SQL 인젝션 방지 테스트"""
    injection_attempts = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users; --",
    ]

    for attempt in injection_attempts:
        response = client.post(
            "/auth/jwt/login", data={"username": attempt, "password": attempt}
        )
        assert response.status_code in [401, 422]  # 인증 실패 또는 유효성 검사 실패


def test_xss_prevention():
    """XSS 방지 테스트"""
    xss_payload = "<script>alert('xss')</script>"
    response = client.post(
        "/auth/register",
        json={
            "email": f"test{xss_payload}@example.com",
            "username": f"user{xss_payload}",
            "password": "StrongP@ssw0rd",
        },
    )
    assert response.status_code == 422  # 유효성 검사 실패 예상


def test_jwt_expiration():
    """JWT 토큰 만료 테스트"""
    # 먼저 사용자 등록
    client.post(
        "/auth/register",
        json={
            "email": "jwt@test.com",
            "username": "jwtuser",
            "password": "StrongP@ssw0rd",
        },
    )

    # 로그인하여 토큰 받기
    response = client.post(
        "/auth/jwt/login",
        data={"username": "jwt@test.com", "password": "StrongP@ssw0rd"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # 만료되지 않은 토큰으로 요청
    response = client.get(
        "/protected-route", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]  # 라우트가 없을 수 있음

    # 만료된 토큰으로 요청 (실제 환경에서는 1시간 대기 필요)
    # 여기서는 테스트를 위해 잘못된 토큰 사용
    expired_token = token[:-1] + "X"
    response = client.get(
        "/protected-route", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
