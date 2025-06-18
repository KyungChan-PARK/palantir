import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from palantir.auth.models import User
from palantir.auth.router import auth_router
from palantir.auth.rbac import Role, Permission


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(auth_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
        "roles": [Role.USER.value],
    }


@pytest.fixture
def test_admin():
    return {
        "email": "admin@example.com",
        "username": "admin",
        "password": "adminpass123",
        "roles": [Role.ADMIN.value],
    }


@pytest.mark.asyncio
async def test_register_user(async_client, test_user):
    """Test user registration endpoint"""
    response = await async_client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]
    assert "password" not in data
    assert Role.USER.value in data["roles"]


@pytest.mark.asyncio
async def test_login_user(async_client, test_user):
    """Test user login endpoint"""
    # First register the user
    await async_client.post("/auth/register", json=test_user)
    
    # Then try to login
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = await async_client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user(async_client, test_user):
    """Test getting current user info"""
    # Register and login
    await async_client.post("/auth/register", json=test_user)
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    token = login_response.json()["access_token"]
    
    # Get current user info
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]


@pytest.mark.asyncio
async def test_update_user_roles(async_client, test_user, test_admin):
    """Test updating user roles (admin only)"""
    # Register admin and normal user
    await async_client.post("/auth/register", json=test_admin)
    user_response = await async_client.post("/auth/register", json=test_user)
    user_id = user_response.json()["id"]
    
    # Login as admin
    admin_login = await async_client.post(
        "/auth/login",
        data={
            "username": test_admin["email"],
            "password": test_admin["password"],
        },
    )
    admin_token = admin_login.json()["access_token"]
    
    # Update user roles
    new_roles = [Role.DEVELOPER.value]
    response = await async_client.put(
        f"/auth/users/{user_id}/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"roles": new_roles},
    )
    assert response.status_code == 200
    data = response.json()
    assert Role.DEVELOPER.value in data["roles"]
    assert Role.USER.value not in data["roles"]


@pytest.mark.asyncio
async def test_unauthorized_role_update(async_client, test_user):
    """Test that non-admin users cannot update roles"""
    # Register and login as normal user
    await async_client.post("/auth/register", json=test_user)
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    token = login_response.json()["access_token"]
    
    # Try to update roles (should fail)
    response = await async_client.put(
        "/auth/users/1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"roles": [Role.ADMIN.value]},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_permissions(async_client, test_user):
    """Test getting user permissions"""
    # Register and login
    await async_client.post("/auth/register", json=test_user)
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    token = login_response.json()["access_token"]
    
    # Get permissions
    response = await async_client.get(
        "/auth/me/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    permissions = response.json()
    assert str(Permission.READ_DOCS) in permissions
    assert str(Permission.MANAGE_USERS) not in permissions 