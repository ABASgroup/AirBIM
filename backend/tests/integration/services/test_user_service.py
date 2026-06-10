"""Tests for User Service."""

import pytest

from core.exceptions import AlreadyExistsError, InvalidLoginInfoError

from schemas.user import UserRegisterRequest

from services.user import authenticate_user, register_user


@pytest.mark.asyncio
async def test_register_user_creates_hashed_password(db_session):
    """Service should create user and hash the incoming password."""
    request = UserRegisterRequest(
        username="service-user",
        email="service@example.com",
        password="password",
        workspace_name="Service workspace",
    )

    user = await register_user(request, session=db_session)

    assert user.id is not None
    assert user.email == "service@example.com"
    assert user.password_hashed != "plain-password"
    assert isinstance(user.password_hashed, str)


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session):
    """Service should not allow registering with an email that already exists."""
    request = UserRegisterRequest(
        username="first-service-user",
        email="service@exmaple.com",
        password="password1",
        workspace_name="First workspace",
    )
    await register_user(request, session=db_session)

    duplicate_request = UserRegisterRequest(
        username="second-service-user",
        email="service@exmaple.com",
        password="password2",
        workspace_name="Second workspace",
    )
    with pytest.raises(AlreadyExistsError):
        await register_user(duplicate_request, session=db_session)


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session):
    """Service should authenticate user with correct email and password."""
    request = UserRegisterRequest(
        username="auth-service-user",
        email="service@example.com",
        password="correct-password",
        workspace_name="Auth workspace",
    )
    await register_user(request, session=db_session)

    user = await authenticate_user(request.email, request.password, session=db_session)
    assert user is not None
    assert user.username == "auth-service-user"


@pytest.mark.asyncio
async def test_authenticate_user_invalid_credentials(db_session):
    """Service should raise error for invalid email or password."""
    request = UserRegisterRequest(
        username="auth-service-user",
        email="service@example.com",
        password="correct-password",
        workspace_name="Auth workspace",
    )
    await register_user(request, session=db_session)

    with pytest.raises(InvalidLoginInfoError):
        _ = await authenticate_user(
            request.email, "incorrect-password", session=db_session
        )

    with pytest.raises(InvalidLoginInfoError):
        _ = await authenticate_user(
            "nonexisten-user", request.password, session=db_session
        )
