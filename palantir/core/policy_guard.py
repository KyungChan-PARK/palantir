from typing import Any, Callable
from functools import wraps
import hashlib
import json

from fastapi import HTTPException
from jose import jwt

from .config import settings
from .cache import get_cache, set_cache

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


def rate_limit_for_tier(tier: str) -> str:
    return {
        "admin": "100/minute",
        "pro": "30/minute",
        "gold": "10/minute",
        "free": "5/minute",
    }.get(tier, "5/minute")


def verify_jwt(credentials: Any):
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def user_tier_func(request: Any) -> str:
    auth = request.headers.get("authorization") if hasattr(request, "headers") else None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return rate_limit_for_tier(payload.get("tier", "free"))
        except Exception:
            return "5/minute"
    return "5/minute"


def cache_response(ttl: int = 300):
    """응답을 캐시하는 데코레이터입니다."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key_parts = [func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 캐시된 응답 확인
            cached_response = await get_cache(cache_key)
            if cached_response:
                return json.loads(cached_response)

            # 함수 실행 및 결과 캐시
            result = await func(*args, **kwargs)
            await set_cache(cache_key, json.dumps(result), ttl)
            return result

        return wrapper

    return decorator
