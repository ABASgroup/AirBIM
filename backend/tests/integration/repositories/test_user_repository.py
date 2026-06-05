"""Tests for User Repository."""
import pytest

from repositories.user import UserRepository
from schemas.user import UserModel


@pytest.mark.asyncio
async def test_user_repository_create_and_get_by_email(db_session):
    """Repository should persist a user and fetch it back by email."""
    user_data = UserModel(
        username="repo-user",
        email="repo@example.com",
        password_hashed="hashed-password",
    ).model_dump(exclude_unset=True)

    created_user = await UserRepository.create(user_data, session=db_session)
    assert created_user.id is not None

    fetched_user = await UserRepository.get_by_email("repo@example.com", session=db_session)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.username == "repo-user"
    assert fetched_user.email == "repo@example.com"


@pytest.mark.asyncio
async def test_user_repository_get_by_email_nonexistent(db_session):
    """Repository should return None if user with email does not exist."""
    fetched_user = await UserRepository.get_by_email("nonexist@example.com", session=db_session)
    assert fetched_user is None
