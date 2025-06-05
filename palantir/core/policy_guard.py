from typing import Any

from fastapi import HTTPException
from jose import jwt

from .config import settings

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
