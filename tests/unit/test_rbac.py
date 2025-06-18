import pytest
from fastapi import HTTPException
from fastapi.security import SecurityScopes

from palantir.auth.models import User
from palantir.auth.rbac import (
    Permission,
    Role,
    check_permissions,
    get_permissions_for_role,
    get_required_permissions,
    get_user_permissions,
    require_permissions,
)


@pytest.fixture
def mock_user():
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
        roles=["user"],
        permissions=[],
    )


@pytest.fixture
def mock_admin_user():
    return User(
        id=2,
        email="admin@example.com",
        username="admin",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
        roles=["admin"],
        permissions=[],
    )


def test_role_enum():
    """Test Role enum values"""
    assert Role.ADMIN.value == "admin"
    assert Role.DEVELOPER.value == "developer"
    assert Role.REVIEWER.value == "reviewer"
    assert Role.USER.value == "user"


def test_permission_enum():
    """Test Permission enum values"""
    assert Permission.MANAGE_USERS.value == "manage:users"
    assert Permission.WRITE_CODE.value == "write:code"
    assert Permission.REVIEW_CODE.value == "review:code"
    assert Permission.READ_DOCS.value == "read:docs"


def test_get_permissions_for_role():
    """Test getting permissions for a role"""
    admin_perms = get_permissions_for_role(Role.ADMIN)
    assert Permission.MANAGE_USERS in admin_perms
    assert Permission.MANAGE_ROLES in admin_perms
    assert len(admin_perms) > 0

    user_perms = get_permissions_for_role(Role.USER)
    assert Permission.READ_DOCS in user_perms
    assert Permission.MANAGE_USERS not in user_perms


def test_get_required_permissions():
    """Test getting required permissions from security scopes"""
    scopes = SecurityScopes(scopes=["read:docs", "write:code"])
    required = get_required_permissions(scopes)
    assert "read:docs" in required
    assert "write:code" in required
    assert len(required) == 2


def test_check_permissions():
    """Test permission checking"""
    required = {"read:docs", "write:code"}
    user_perms = {"read:docs", "write:code", "read:metrics"}
    assert check_permissions(required, user_perms) is True

    insufficient_perms = {"read:docs"}
    assert check_permissions(required, insufficient_perms) is False


def test_get_user_permissions(mock_user, mock_admin_user):
    """Test getting user permissions based on roles"""
    user_perms = get_user_permissions(mock_user)
    assert str(Permission.READ_DOCS) in user_perms
    assert str(Permission.MANAGE_USERS) not in user_perms

    admin_perms = get_user_permissions(mock_admin_user)
    assert str(Permission.MANAGE_USERS) in admin_perms
    assert str(Permission.MANAGE_ROLES) in admin_perms


@pytest.mark.asyncio
async def test_require_permissions_success(mock_admin_user):
    """Test permission requirement success"""
    security_scopes = SecurityScopes(scopes=[])
    permission_checker = require_permissions([Permission.MANAGE_USERS])
    
    # Should not raise an exception
    result = await permission_checker(security_scopes, mock_admin_user)
    assert result == mock_admin_user


@pytest.mark.asyncio
async def test_require_permissions_failure(mock_user):
    """Test permission requirement failure"""
    security_scopes = SecurityScopes(scopes=[])
    permission_checker = require_permissions([Permission.MANAGE_USERS])
    
    with pytest.raises(HTTPException) as exc_info:
        await permission_checker(security_scopes, mock_user)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_permissions_inactive_user(mock_user):
    """Test permission check with inactive user"""
    mock_user.is_active = False
    security_scopes = SecurityScopes(scopes=[])
    permission_checker = require_permissions([Permission.READ_DOCS])
    
    with pytest.raises(HTTPException) as exc_info:
        await permission_checker(security_scopes, mock_user)
    
    assert exc_info.value.status_code == 401 