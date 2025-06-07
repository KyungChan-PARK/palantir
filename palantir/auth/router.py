from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from .models import User
from .manager import get_user_manager
from .config import auth_backend
from .schemas import UserRead, UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)

router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
) 