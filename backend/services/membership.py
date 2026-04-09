"""Service layer logic for Membership."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from roles import Role
from repositories.membership import MembershipRepository
from models.membership import Membership
from schemas.membership import MembershipModel
from exceptions.exceptions import NotMemberError, ProhibitedWorkspaceActionError


async def get_workspace_members(workspace_id: uuid.UUID, session: AsyncSession) -> list[Membership]:
    """Get all memberships related to this workspace with user data."""
    memberships = await MembershipRepository.get_all_workspace_users(
        workspace_id,
        session=session
    )

    return list(memberships)


async def get_membership(user_id: uuid.UUID, workspace_id: uuid.UUID, session: AsyncSession) -> Membership:
    """
    Get user membership in the workspace.
    """
    membership = await MembershipRepository.get_user_workspace_membership(
        user_id,
        workspace_id,
        session=session
    )

    if membership is None:
        raise NotMemberError()

    return membership


async def create_membership(membership_data: MembershipModel, session: AsyncSession) -> Membership:
    """
    Create a new membership for the workspace.
    """
    try:
        workspace = await MembershipRepository.create(membership_data, session=session)
        await session.commit()
        return workspace
    except Exception:
        await session.rollback()
        raise


async def delete_membership(user_id: uuid.UUID, workspace_id: uuid.UUID, session: AsyncSession) -> Membership:
    """
    Delete user's membership in the workspace

    Make sure to check permission

    You can't remove the owner from the workspace
    """
    try:
        membership = await MembershipRepository.get_user_workspace_membership(
            user_id,
            workspace_id,
            session=session)

        if membership is None:
            raise NotMemberError()

        # check role first
        if membership.role == Role.OWNER:
            raise ProhibitedWorkspaceActionError(
                "deleting owner from workspace")

        # not an owner, delete
        await MembershipRepository.delete(membership, session=session)
        await session.commit()
        return membership
    except Exception:
        await session.rollback()
        raise
