"""Tests for Membership Service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    MembershipViolationError,
    NotMemberError,
    ProhibitedWorkspaceActionError,
)
from core.roles import Role

from schemas.membership import MembershipModel

from services.membership import (
    change_user_role,
    create_membership,
    delete_membership,
    get_membership,
    get_workspace_members,
)

from tests.helpers import (
    create_test_membership,
    create_test_user,
    create_test_workspace,
)


@pytest.mark.asyncio
async def test_create_membership(db_session: AsyncSession) -> None:
    """Service should create membership."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    membership_data = MembershipModel(
        workspace_id=workspace.id, user_id=user.id, role=Role.MEMBER
    )
    membership = await create_membership(membership_data, session=db_session)

    assert membership.workspace_id == workspace.id
    assert membership.user_id == user.id
    assert membership.role == Role.MEMBER


@pytest.mark.asyncio
async def test_get_membership(db_session: AsyncSession) -> None:
    """Service should return membership."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)
    created_membership = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.MEMBER
    )

    membership = await get_membership(user.id, workspace.id, session=db_session)

    assert membership == created_membership


@pytest.mark.asyncio
async def test_get_nonexistent_membership(db_session: AsyncSession) -> None:
    """Service should raise NotMemberError if membership does not exist."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    with pytest.raises(NotMemberError):
        await get_membership(user.id, workspace.id, session=db_session)


@pytest.mark.asyncio
async def test_get_workspace_members(db_session: AsyncSession) -> None:
    """Service should return all workspace memberships."""
    workspace = await create_test_workspace(db_session)
    user1 = await create_test_user(db_session, email="test@test.com")
    user2 = await create_test_user(db_session, email="test2@test.com")

    membership1 = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user1.id, role=Role.MEMBER
    )
    membership2 = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user2.id, role=Role.MEMBER
    )

    members = await get_workspace_members(workspace.id, session=db_session)

    assert len(members) == 2
    assert membership1 in members
    assert membership2 in members


@pytest.mark.asyncio
async def test_delete_membership(db_session: AsyncSession) -> None:
    """Service should delete membership."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    membership = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.MEMBER
    )

    deleted_membership = await delete_membership(
        user.id, workspace.id, session=db_session
    )

    assert deleted_membership == membership

    with pytest.raises(NotMemberError):
        await get_membership(user.id, workspace.id, session=db_session)


@pytest.mark.asyncio
async def test_delete_owner_membership(db_session: AsyncSession) -> None:
    """Service should not allow deleting owner membership."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.OWNER
    )

    with pytest.raises(ProhibitedWorkspaceActionError):
        await delete_membership(user.id, workspace.id, session=db_session)


@pytest.mark.asyncio
async def test_delete_nonexistent_membership(db_session: AsyncSession) -> None:
    """Service should raise NotMemberError when trying to delete non-existent membership."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    with pytest.raises(NotMemberError):
        await delete_membership(user.id, workspace.id, session=db_session)


@pytest.mark.asyncio
async def test_change_user_role(db_session: AsyncSession) -> None:
    """Service should change user role."""
    workspace = await create_test_workspace(db_session)
    editor = await create_test_user(db_session, email="test@test.com")
    user = await create_test_user(db_session, email="test2@test.com")
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=editor.id, role=Role.OWNER
    )
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.MEMBER
    )

    updated_membership = await change_user_role(
        editor_id=editor.id,
        user_id=user.id,
        workspace_id=workspace.id,
        new_role=Role.ADMIN,
        session=db_session,
    )

    assert updated_membership.role == Role.ADMIN


@pytest.mark.asyncio
async def test_change_user_role_to_owner(db_session: AsyncSession) -> None:
    """Service should not allow changing user role to owner."""
    workspace = await create_test_workspace(db_session)
    editor = await create_test_user(db_session, email="test@test.com")
    user = await create_test_user(db_session, email="test2@test.com")
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=editor.id, role=Role.OWNER
    )
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.MEMBER
    )

    with pytest.raises(MembershipViolationError):
        await change_user_role(
            editor_id=editor.id,
            user_id=user.id,
            workspace_id=workspace.id,
            new_role=Role.OWNER,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_change_owner_role(db_session: AsyncSession) -> None:
    """Service should not allow changing owner's role."""
    workspace = await create_test_workspace(db_session)
    editor = await create_test_user(db_session, email="test@test.com")
    user = await create_test_user(db_session, email="test2@test.com")
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=editor.id, role=Role.ADMIN
    )
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=user.id, role=Role.OWNER
    )

    with pytest.raises(MembershipViolationError):
        await change_user_role(
            editor_id=editor.id,
            user_id=user.id,
            workspace_id=workspace.id,
            new_role=Role.ADMIN,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_change_user_role_nonexistent_membership(
    db_session: AsyncSession,
) -> None:
    """Service should raise NotMemberError when trying to change role of non-existent membership."""
    workspace = await create_test_workspace(db_session)
    editor = await create_test_user(db_session, email="test@test.com")
    user = await create_test_user(db_session, email="test2@test.com")
    _ = await create_test_membership(
        db_session, workspace_id=workspace.id, user_id=editor.id, role=Role.ADMIN
    )

    with pytest.raises(NotMemberError):
        await change_user_role(
            editor_id=editor.id,
            user_id=user.id,
            workspace_id=workspace.id,
            new_role=Role.ADMIN,
            session=db_session,
        )

    with pytest.raises(NotMemberError):
        await change_user_role(
            editor_id=user.id,
            user_id=editor.id,
            workspace_id=workspace.id,
            new_role=Role.ADMIN,
            session=db_session,
        )
