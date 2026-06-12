"""Tests for Invite link Repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Role

from repositories.invite_link import InviteLinkRepository

from schemas.invite_link import InviteLinkModel

from tests.helpers import create_test_user, create_test_workspace


@pytest.mark.asyncio
async def test_invite_link_repository_create_and_get_by_token(
    db_session: AsyncSession,
) -> None:
    """Test creating an invite link and retrieving it."""
    # Create a workspace and user
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create an invite link for the workspace
    invite_link_data = InviteLinkModel(
        token_hashed="hashed_token",
        workspace_id=workspace.id,
        creator_id=user.id,
        role=Role.MEMBER,
    ).model_dump(exclude_unset=True)
    created_invite_link = await InviteLinkRepository.create(
        invite_link_data, db_session
    )

    # Retrieve the invite link by token
    retrieved_invite_link = await InviteLinkRepository.get_by_token(
        token_hashed="hashed_token", session=db_session
    )

    # Assertions
    assert retrieved_invite_link is not None
    assert retrieved_invite_link.id == created_invite_link.id
    assert retrieved_invite_link.workspace_id == workspace.id
    assert retrieved_invite_link.creator_id == user.id
    assert retrieved_invite_link.role == Role.MEMBER


@pytest.mark.asyncio
async def test_invite_link_repository_get_by_workspace_id_and_role(
    db_session: AsyncSession,
) -> None:
    """Test retrieving an invite link by workspace ID and role."""
    # Create a workspace and user
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create an invite link for the workspace with a specific role
    invite_link_data = InviteLinkModel(
        token_hashed="hashed_token_2",
        workspace_id=workspace.id,
        creator_id=user.id,
        role=Role.OWNER,
    ).model_dump(exclude_unset=True)
    created_invite_link = await InviteLinkRepository.create(
        invite_link_data, db_session
    )

    # Retrieve the invite link by workspace ID and role
    retrieved_invite_link = await InviteLinkRepository.get_by_workspace_id_and_role(
        workspace_id=workspace.id, role=Role.OWNER, session=db_session
    )

    # Assertions
    assert retrieved_invite_link is not None
    assert retrieved_invite_link.id == created_invite_link.id
    assert retrieved_invite_link.workspace_id == workspace.id
    assert retrieved_invite_link.creator_id == user.id
    assert retrieved_invite_link.role == Role.OWNER


@pytest.mark.asyncio
async def test_invite_link_repository_delete_by_workspace_id(
    db_session: AsyncSession,
) -> None:
    """Test deleting invite links by workspace ID."""
    # Create a workspace and user
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create multiple invite links for the workspace
    for i in range(3):
        invite_link_data = InviteLinkModel(
            token_hashed=f"hashed_token_{i}",
            workspace_id=workspace.id,
            creator_id=user.id,
            role=Role.MEMBER,
        ).model_dump(exclude_unset=True)
        await InviteLinkRepository.create(invite_link_data, db_session)

    # Delete invite links by workspace ID
    await InviteLinkRepository.delete_by_workspace_id(
        workspace_id=workspace.id, session=db_session
    )

    # Try to retrieve any invite link for the workspace
    retrieved_invite_link = await InviteLinkRepository.get_by_workspace_id_and_role(
        workspace_id=workspace.id, role=Role.MEMBER, session=db_session
    )

    # Assertions
    assert retrieved_invite_link is None
