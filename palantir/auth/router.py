from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi_users import FastAPIUsers
from fastapi.security import SecurityScopes

from .config import auth_backend
from .manager import get_user_manager
from .models import User
from .rbac import Permission, require_permissions
from .schemas import UserCreate, UserRead, UserUpdate
from .metrics import (
    record_login_attempt,
    record_registration_attempt,
    record_permission_check,
    record_role_update,
    record_token_validation
)

router = APIRouter(prefix="/auth", tags=["auth"])

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# Basic auth routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)

# User management routes with RBAC
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))],
)

# Registration route (admin only)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))],
)

# Password reset and verification routes
router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)

# Role management routes
@router.put("/users/{user_id}/roles", tags=["users"])
async def update_user_roles(
    user_id: int,
    roles: list[str],
    current_user: User = Security(
        get_user_manager,
        scopes=[str(Permission.MANAGE_ROLES)]
    )
):
    """Update user roles (admin only)"""
    user_manager = get_user_manager()
    user = await user_manager.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.roles = roles
    await user_manager.update(user)
    for role in roles:
        record_role_update(success=True, role=role)
    return {"message": "Roles updated successfully"}

@router.post("/register", status_code=201)
async def register_user(user: UserCreate):
    try:
        # Existing registration logic...
        record_registration_attempt(success=True)
        return new_user
    except Exception as e:
        record_registration_attempt(success=False)
        raise

@router.post("/login")
async def login(username: str, password: str):
    try:
        # Existing login logic...
        record_login_attempt(success=True)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        record_login_attempt(success=False)
        raise

@router.get("/me")
async def get_current_user(
    user: User = Security(get_user_manager, scopes=[])
):
    record_token_validation("success")
    return user

@router.get("/me/permissions")
async def get_my_permissions(
    user: User = Security(get_user_manager, scopes=[])
):
    permissions = get_user_permissions(user)
    for perm in permissions:
        record_permission_check(granted=True, permission=perm)
    return permissions
