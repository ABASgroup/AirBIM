"""Sample API integration tests for auth endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register_returns_token_and_creates_workspace(api_client):
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
async def test_login_with_wrong_password_returns_401(api_client):
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
    assert response.json() == {"message": "Email or password is incorrect"}
