import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from palantir.core.cache import get_cache

# 환경 변수에서 설정 로드
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "palantir-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))
DEFAULT_RATE_LIMIT = os.getenv("DEFAULT_RATE_LIMIT", "5/minute")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def user_tier_func(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split()[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            tier = payload.get("tier", "free").lower()
            return rate_limit_for_tier(tier)
        except Exception:
            return DEFAULT_RATE_LIMIT
    return DEFAULT_RATE_LIMIT

limiter = Limiter(key_func=get_remote_address, default_limits=[user_tier_func])
cache = get_cache(128)
auth_scheme = HTTPBearer()

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token has expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def rate_limit_for_tier(tier: str) -> str:
    limits = {
        "admin": "100/minute",
        "pro": "30/minute",
        "gold": "10/minute",
        "free": "5/minute"
    }
    return limits.get(tier.lower(), DEFAULT_RATE_LIMIT)

def cache_response(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            cache_key = f"{request.url}:{await request.body()}"
            if cache_key in cache:
                return cache[cache_key]
            result = await func(*args, **kwargs)
            cache[cache_key] = result
            return result
        return wrapper
    return decorator
