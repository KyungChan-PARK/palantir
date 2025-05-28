from typing import Set

from fastapi import APIRouter, HTTPException
from jose import jwt

SECRET_KEY = "palantir-secret"
ALGORITHM = "HS256"

router = APIRouter()

# 메모리 기반 블랙리스트 (운영은 Redis 등 권장)
refresh_blacklist: Set[str] = set()


def blacklist_refresh_token(token: str):
    refresh_blacklist.add(token)


def is_refresh_token_blacklisted(token: str) -> bool:
    return token in refresh_blacklist


@router.post("/auth/logout")
def logout(refresh_token: str):
    blacklist_refresh_token(refresh_token)
    return {"logout": True}


@router.post("/auth/refresh")
def refresh(refresh_token: str):
    if is_refresh_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="Token revoked")
    # 실제 토큰 검증 및 재발급 로직 필요
    jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    # ...
    return {"access_token": "new-token"}
