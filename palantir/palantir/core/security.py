"""보안 관련 모듈."""

import logging
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
import redis
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from ratelimit import RateLimiter
from ratelimit.backends.redis import RedisBackend
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from .config import settings

logger = logging.getLogger(__name__)

# 보안 설정
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)

# Redis 설정
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Rate Limiter 설정
rate_limiter = RateLimiter(
    backend=RedisBackend(redis_client),
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    period=settings.RATE_LIMIT_PERIOD,
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 미들웨어."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # 요청 로깅
        logger.info(f"요청 시작: {request.method} {request.url.path}")

        # 보안 헤더 추가
        response = await call_next(request)
        for key, value in self.security_headers.items():
            response.headers[key] = value

        # 응답 시간 로깅
        process_time = time.time() - start_time
        logger.info(
            f"요청 완료: {request.method} {request.url.path} - {process_time:.3f}초"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """요청 제한 미들웨어."""

    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = 100  # 초당 최대 요청 수
        self.window = 60  # 시간 윈도우 (초)

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        # 현재 요청 수 확인
        current = self.redis.get(key)
        if current and int(current) >= self.rate_limit:
            raise HTTPException(
                status_code=429, detail="너무 많은 요청이 발생했습니다."
            )

        # 요청 수 증가
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        pipe.execute()

        return await call_next(request)


class TokenBlacklist:
    """토큰 블랙리스트 관리 클래스."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "blacklist:"

    def add_token(self, token: str, expires_in: int):
        """토큰을 블랙리스트에 추가합니다."""
        key = f"{self.prefix}{token}"
        self.redis.setex(key, expires_in, "1")

    def is_blacklisted(self, token: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인합니다."""
        key = f"{self.prefix}{token}"
        return bool(self.redis.get(key))


# 토큰 블랙리스트 인스턴스
token_blacklist = TokenBlacklist(redis_client)


class SecurityManager:
    def __init__(self, secret_key: str, redis_client: redis.Redis):
        self.secret_key = secret_key
        self.token_blacklist = TokenBlacklist(redis_client)
        self.bearer = HTTPBearer()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호를 검증합니다."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def hash_password(self, password: str) -> str:
        """비밀번호를 해시화합니다."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def validate_password(self, password: str) -> bool:
        """비밀번호 유효성을 검사합니다."""
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False
        return True

    def create_token(self, data: Dict[str, Any], expires_delta: int) -> str:
        """JWT 토큰을 생성합니다."""
        to_encode = data.copy()
        to_encode.update({"exp": time.time() + expires_delta})
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰을 검증합니다."""
        try:
            if self.token_blacklist.is_blacklisted(token):
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    def sanitize_input(self, input_str: str) -> str:
        """사용자 입력을 정제합니다."""
        # XSS 방지
        input_str = re.sub(r"<[^>]*>", "", input_str)
        # SQL 인젝션 방지
        input_str = re.sub(r"[\"';]", "", input_str)
        return input_str

    def validate_email(self, email: str) -> bool:
        """이메일 유효성을 검사합니다."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_username(self, username: str) -> bool:
        """사용자 이름 유효성을 검사합니다."""
        if len(username) < 3 or len(username) > 20:
            return False
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return False
        return True

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """보안 이벤트를 로깅합니다."""
        logger.warning(
            f"보안 이벤트: {event_type}",
            extra={
                "event_type": event_type,
                "details": details,
                "timestamp": time.time(),
            },
        )


security_manager = SecurityManager(settings.SECRET_KEY, redis_client)


def validate_password(password: str) -> bool:
    """비밀번호 유효성을 검사합니다."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    return bool(PASSWORD_PATTERN.match(password))


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """리프레시 토큰을 생성합니다."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def sanitize_input(input_str: str) -> str:
    """입력값을 정제합니다."""
    # XSS 방지
    input_str = input_str.replace("<", "&lt;").replace(">", "&gt;")
    # SQL 인젝션 방지
    input_str = re.sub(r"[\"';]", "", input_str)
    return input_str


def validate_email(email: str) -> bool:
    """이메일 주소를 검증합니다."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """사용자 이름을 검증합니다."""
    pattern = r"^[a-zA-Z0-9_-]{3,20}$"
    return bool(re.match(pattern, username))


def check_permissions(user_scopes: List[str], required_scopes: List[str]) -> bool:
    """사용자 권한을 검사합니다."""
    return all(scope in user_scopes for scope in required_scopes)


def log_security_event(event_type: str, details: Dict[str, Any]):
    """보안 이벤트를 로깅합니다."""
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        },
    )
