from datetime import datetime, timedelta

from fastapi import APIRouter
from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()
_blacklist = set()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def blacklist_refresh_token(token: str) -> None:
    _blacklist.add(token)


def is_refresh_token_blacklisted(token: str) -> bool:
    return token in _blacklist


@router.post("/auth/token")
async def login():
    return {"access_token": create_access_token({"sub": "user"}), "refresh_token": "r"}
