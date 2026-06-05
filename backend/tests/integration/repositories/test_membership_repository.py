import pytest

from core.roles import Role
from repositories.membership import MembershipRepository
from schemas.membership import MembershipModel
from tests.helpers import create_test_workspace, create_test_user


@pytest.mark.asyncio
async def test_membership_repository_create_and_get(db_session):
    """Test creating a membership and retrieving it."""
    # Create a workspace
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create a membership in the workspace
    membership_data = MembershipModel(
        workspace_id=workspace.id,
        user_id=user.id,
        role=Role.MEMBER
    ).model_dump(exclude_unset=True)
    created_membership = await MembershipRepository.create(membership_data, db_session)

    # Retrieve the membership by user and workspace ID
    retrieved_membership = await MembershipRepository.get_user_workspace_membership(
        user_id=user.id,
        workspace_id=workspace.id,
        session=db_session
    )

    # Assertions
    assert retrieved_membership is not None
    assert retrieved_membership.id == created_membership.id
    assert retrieved_membership.user_id == user.id
    assert retrieved_membership.role == Role.MEMBER


@pytest.mark.asyncio
async def test_membership_repository_get_all_workspace_users(db_session):
    """Test retrieving all memberships in a workspace."""
    # Create a workspace and users
    workspace = await create_test_workspace(db_session)
    user1 = await create_test_user(db_session, email="test2@test.com")
    user2 = await create_test_user(db_session)

    # Create memberships for both users in the workspace
    membership_data1 = MembershipModel(
        workspace_id=workspace.id,
        user_id=user1.id,
        role=Role.MEMBER
    ).model_dump(exclude_unset=True)
    membership_data2 = MembershipModel(
        workspace_id=workspace.id,
        user_id=user2.id,
        role=Role.OWNER
    ).model_dump(exclude_unset=True)

    await MembershipRepository.create(membership_data1, db_session)
    await MembershipRepository.create(membership_data2, db_session)

    # Retrieve all memberships in the workspace
    memberships = await MembershipRepository.get_all_workspace_users(
        workspace_id=workspace.id,
        session=db_session
    )

    # Assertions
    assert len(memberships) == 2
    assert any(m.user_id == user1.id and m.role ==
               Role.MEMBER for m in memberships)
    assert any(m.user_id == user2.id and m.role ==
               Role.OWNER for m in memberships)


@pytest.mark.asyncio
async def test_membership_repository_get_all_user_memberships(db_session):
    """Test retrieving all memberships for a user."""
    # Create a workspace and user
    workspace1 = await create_test_workspace(db_session)
    workspace2 = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create memberships for the user in both workspaces
    membership_data1 = MembershipModel(
        workspace_id=workspace1.id,
        user_id=user.id,
        role=Role.MEMBER
    ).model_dump(exclude_unset=True)
    membership_data2 = MembershipModel(
        workspace_id=workspace2.id,
        user_id=user.id,
        role=Role.OWNER
    ).model_dump(exclude_unset=True)

    await MembershipRepository.create(membership_data1, db_session)
    await MembershipRepository.create(membership_data2, db_session)

    # Retrieve all memberships for the user
    memberships = await MembershipRepository.get_all_user_memberships(
        user_id=user.id,
        session=db_session
    )

    # Assertions
    assert len(memberships) == 2
    assert any(m.workspace_id == workspace1.id and m.role ==
               Role.MEMBER for m in memberships)
    assert any(m.workspace_id == workspace2.id and m.role ==
               Role.OWNER for m in memberships)


@pytest.mark.asyncio
async def test_membership_repository_delete_user_workspace_membership(db_session):
    """Test deleting a user's membership in a workspace."""
    # Create a workspace and user
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(db_session)

    # Create a membership for the user in the workspace
    membership_data = MembershipModel(
        workspace_id=workspace.id,
        user_id=user.id,
        role=Role.MEMBER
    ).model_dump(exclude_unset=True)
    await MembershipRepository.create(membership_data, db_session)

    # Delete the user's membership in the workspace
    await MembershipRepository.delete_user_workspace_membership(
        user_id=user.id,
        workspace_id=workspace.id,
        session=db_session
    )

    # Try to retrieve the deleted membership
    deleted_membership = await MembershipRepository.get_user_workspace_membership(
        user_id=user.id,
        workspace_id=workspace.id,
        session=db_session
    )

    # Assertions
    assert deleted_membership is None
