from functools import wraps

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from palantir.core.cache import get_cache

SECRET_KEY = "palantir-secret"  # 실제 운영 시 환경변수로 관리
ALGORITHM = "HS256"

def user_tier_func(request: Request):
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split()[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            tier = payload.get("tier", "free").lower()
            if tier == "gold":
                return "10/minute"
            else:
                return "5/minute"
        except Exception:
            return "5/minute"
    return "5/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[user_tier_func])
cache = get_cache(128)
auth_scheme = HTTPBearer()

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def rate_limit_for_tier(tier: str):
    if tier == "admin":
        return "100/minute"
    elif tier == "pro":
        return "30/minute"
    else:
        return "5/minute"

def cache_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        cache_key = str(request.url) + str(await request.body())
        if cache_key in cache:
            return cache[cache_key]
        result = await func(*args, **kwargs)
        cache[cache_key] = result
        return result
    return wrapper
