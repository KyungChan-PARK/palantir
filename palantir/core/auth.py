from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings
from .user import UserDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()
_blacklist: set[str] = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[UserDB]:
    user = UserDB.get_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS * 24)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def blacklist_refresh_token(token: str) -> None:
    _blacklist.add(token)


def is_refresh_token_blacklisted(token: str) -> bool:
    return token in _blacklist


def require_role(role: str):
    def dependency(user: UserDB = Depends(get_current_user)) -> UserDB:
        if role not in (user.scopes or []):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return dependency


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, scopes=payload.get("scopes", []))
    except JWTError:
        raise credentials_exception

    user = UserDB.get_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username, "scopes": user.scopes})
    refresh_token = create_refresh_token({"sub": user.username})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/auth/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    if is_refresh_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = UserDB.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    blacklist_refresh_token(refresh_token)
    access_token = create_access_token({"sub": user.username, "scopes": user.scopes})
    new_refresh_token = create_refresh_token({"sub": user.username})
    return {"access_token": access_token, "refresh_token": new_refresh_token}


@router.post("/auth/logout")
async def logout(refresh_token: str = Form(...)):
    blacklist_refresh_token(refresh_token)
    return {"detail": "Logged out"}


@router.get("/users/me")
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user.to_dict()
