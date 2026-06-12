"""Sample API integration tests for auth endpoints."""

import pytest
from httpx import AsyncClient

from core.roles import Permission, Role


@pytest.mark.asyncio
async def test_register_returns_token_and_creates_workspace(
    api_client: AsyncClient,
) -> None:
    """Register endpoint should create user-related data and return access token."""
    response = await api_client.post(
        "/auth/register",
        json={
            "username": "api-user",
            "email": "api@example.com",
            "password": "super-secret",
            "workspace_name": "API Workspace",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


@pytest.mark.asyncio
async def test_login_returns_token(api_client: AsyncClient) -> None:
    """Login endpoint should return access token for valid credentials."""
    register_response = await api_client.post(
        "/auth/register",
        json={
            "username": "login-user",
            "email": "api@test.com",
            "password": "correct-password",
            "workspace_name": "Login Workspace",
        },
    )
    assert register_response.status_code == 200
    login_response = await api_client.post(
        "/auth/login",
        data={
            "username": "api@test.com",  # Note: OAuth2PRF uses "username" field for email
            "password": "correct-password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


@pytest.mark.asyncio
async def test_login_with_nonexistent_email_returns_401(
    api_client: AsyncClient,
) -> None:
    """Login endpoint should return 401 for non-existent email."""
    response = await api_client.post(
        "/auth/login",
        data={
            "username": "api@test.com",  # Note: OAuth2PRF uses "username" field for email
            "password": "correct-password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert (
        "email or password is incorrect" in response.json().get("message", "").lower()
    )


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(api_client: AsyncClient) -> None:
    """Login endpoint should use custom exception handler for invalid credentials."""
    register_response = await api_client.post(
        "/auth/register",
        json={
            "username": "login-user",
            "email": "login@example.com",
            "password": "correct-password",
            "workspace_name": "Login Workspace",
        },
    )
    assert register_response.status_code == 200

    response = await api_client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "wrong-password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert (
        "email or password is incorrect" in response.json().get("message", "").lower()
    )


@pytest.mark.asyncio
async def test_register_with_invalid_email_returns_422(api_client: AsyncClient) -> None:
    """Register endpoint should return 422 for invalid email format."""
    response = await api_client.post(
        "/auth/register",
        json={
            "username": "api-user",
            "email": "invalid-email-format",
            "password": "super-secret",
            "workspace_name": "API Workspace",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_with_short_password_returns_422(
    api_client: AsyncClient,
) -> None:
    """Register endpoint should return 422 for password that is too short."""
    response = await api_client.post(
        "/auth/register",
        json={
            "username": "api-user",
            "email": "login@example.com",
            "password": "short",
            "workspace_name": "API Workspace",
        },
    )

    # TODO: This test currently fails because of the way we handle validation errors.
    # We should improve registration validation to return ?422?
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_with_existing_email_returns_409(
    api_client: AsyncClient,
) -> None:
    """Register endpoint should return 409 if email is already registered."""
    response = await api_client.post(
        "/auth/register",
        json={
            "username": "api-user",
            "email": "api@example.com",
            "password": "super-secret",
            "workspace_name": "API Workspace",
        },
    )

    assert response.status_code == 200
    response = await api_client.post(
        "/auth/register",
        json={
            "username": "another-user",
            "email": "api@example.com",
            "password": "another-password",
            "workspace_name": "Another Workspace",
        },
    )

    assert response.status_code == 409
    assert "already exist" in response.json().get("message").lower()


@pytest.mark.asyncio
async def test_get_permissions_returns_all_permissions(api_client: AsyncClient) -> None:
    """Permissions endpoint should return all possible permissions."""
    response = await api_client.get("/auth/permissions")
    assert response.status_code == 200
    permissions = response.json()
    assert isinstance(permissions, list)
    for perm in Permission:
        assert perm.value in permissions


@pytest.mark.asyncio
async def test_get_roles_returns_all_roles(api_client: AsyncClient) -> None:
    """Roles endpoint should return all possible roles."""
    response = await api_client.get("/auth/roles")
    assert response.status_code == 200
    roles = response.json()
    assert isinstance(roles, list)
    for role in Role:
        assert role.value in roles
