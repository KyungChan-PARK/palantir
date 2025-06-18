from enum import Enum
from typing import Dict, List, Set

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from fastapi_users import FastAPIUsers

from .models import User


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    USER = "user"


class Permission(str, Enum):
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_SYSTEM = "manage:system"
    
    # Developer permissions
    WRITE_CODE = "write:code"
    RUN_TESTS = "run:tests"
    MANAGE_PIPELINES = "manage:pipelines"
    
    # Reviewer permissions
    REVIEW_CODE = "review:code"
    APPROVE_CHANGES = "approve:changes"
    
    # User permissions
    READ_DOCS = "read:docs"
    READ_METRICS = "read:metrics"
    USE_API = "use:api"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.MANAGE_SYSTEM,
        Permission.WRITE_CODE,
        Permission.RUN_TESTS,
        Permission.MANAGE_PIPELINES,
        Permission.REVIEW_CODE,
        Permission.APPROVE_CHANGES,
        Permission.READ_DOCS,
        Permission.READ_METRICS,
        Permission.USE_API,
    },
    Role.DEVELOPER: {
        Permission.WRITE_CODE,
        Permission.RUN_TESTS,
        Permission.MANAGE_PIPELINES,
        Permission.READ_DOCS,
        Permission.READ_METRICS,
        Permission.USE_API,
    },
    Role.REVIEWER: {
        Permission.REVIEW_CODE,
        Permission.APPROVE_CHANGES,
        Permission.READ_DOCS,
        Permission.READ_METRICS,
        Permission.USE_API,
    },
    Role.USER: {
        Permission.READ_DOCS,
        Permission.READ_METRICS,
        Permission.USE_API,
    },
}


def get_permissions_for_role(role: Role) -> Set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_required_permissions(security_scopes: SecurityScopes) -> Set[str]:
    """Get required permissions from security scopes."""
    return set(security_scopes.scopes)


def check_permissions(
    required_permissions: Set[str],
    user_permissions: Set[str],
) -> bool:
    """Check if user has all required permissions."""
    return required_permissions.issubset(user_permissions)


def get_user_permissions(user: User) -> Set[str]:
    """Get all permissions for a user based on their roles."""
    permissions = set()
    for role in user.roles:
        try:
            role_enum = Role(role)
            permissions.update(get_permissions_for_role(role_enum))
        except ValueError:
            continue
    return {str(perm) for perm in permissions}


def require_permissions(permissions: List[Permission]):
    """Dependency for requiring specific permissions."""
    
    async def permission_checker(
        security_scopes: SecurityScopes,
        user: User = Depends(fastapi_users.current_user(active=True)),
    ) -> User:
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive user")
            
        user_permissions = get_user_permissions(user)
        required = {str(perm) for perm in permissions}
        
        if not check_permissions(required, user_permissions):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    return permission_checker 