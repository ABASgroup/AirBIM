"""Tests for Invite link Service."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    InvalidInvitationError,
    NotFoundError,
    ProhibitedWorkspaceActionError,
)
from core.roles import InviteableRole, Role

from schemas.workspace import WorkspaceType

from services.invite_link import (
    generate_invite_link,
    revoke_links,
    validate_invite_link,
)

from tests.helpers import create_test_user, create_test_workspace


@pytest.mark.asyncio
async def test_generate_invite_link(db_session: AsyncSession) -> None:
    """Service should generate invite link."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    invite_link, token = await generate_invite_link(
        workspace.id, user.id, InviteableRole.MEMBER, session=db_session
    )

    assert invite_link.id is not None
    assert invite_link.workspace_id == workspace.id
    assert invite_link.creator_id == user.id
    assert invite_link.role == Role.MEMBER
    assert token is not None
    assert invite_link.token_hashed != token, "token should be hashed in the database"


@pytest.mark.asyncio
async def test_generate_invite_link_for_personal_workspace(
    db_session: AsyncSession,
) -> None:
    """Service should not generate invite link for personal workspace."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.PERSONAL
    )
    user = await create_test_user(db_session)

    with pytest.raises(ProhibitedWorkspaceActionError):
        await generate_invite_link(
            workspace.id, user.id, InviteableRole.MEMBER, session=db_session
        )


@pytest.mark.asyncio
async def test_generate_invite_link_for_nonexistent_workspace(
    db_session: AsyncSession,
) -> None:
    """Service should not generate invite link for nonexistent workspace."""
    user = await create_test_user(db_session)

    with pytest.raises(NotFoundError):
        await generate_invite_link(
            uuid.uuid4(), user.id, InviteableRole.MEMBER, session=db_session
        )


@pytest.mark.asyncio
async def test_validate_invite_link(db_session: AsyncSession) -> None:
    """Service should validate invite link."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    invite_link, token = await generate_invite_link(
        workspace.id, user.id, InviteableRole.MEMBER, session=db_session
    )

    # valid token should return invite link
    validated_link = await validate_invite_link(token, session=db_session)
    assert validated_link == invite_link


@pytest.mark.asyncio
async def test_validate_invalid_invite_link(db_session: AsyncSession) -> None:
    """Service should not validate invalid invite link."""
    with pytest.raises(InvalidInvitationError):
        await validate_invite_link("invalid_token", session=db_session)


@pytest.mark.asyncio
async def test_revoke_links(db_session: AsyncSession) -> None:
    """Service should revoke invite links."""
    workspace = await create_test_workspace(db_session)
    user1 = await create_test_user(db_session)
    user2 = await create_test_user(db_session, email="test2@gmail.com")

    _, token1 = await generate_invite_link(
        workspace.id, user1.id, InviteableRole.MEMBER, session=db_session
    )
    _, token2 = await generate_invite_link(
        workspace.id, user2.id, InviteableRole.MEMBER, session=db_session
    )

    # validate links before revocation, they should be valid
    assert await validate_invite_link(token1, session=db_session)
    assert await validate_invite_link(token2, session=db_session)

    await revoke_links(workspace.id, session=db_session)

    # validate links after revocation, they should be invalid
    with pytest.raises(InvalidInvitationError):
        await validate_invite_link(token1, session=db_session)

    with pytest.raises(InvalidInvitationError):
        await validate_invite_link(token2, session=db_session)
