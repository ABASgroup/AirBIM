"""Service layer logic for Membership."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.membership import MembershipCRUD
from models.membership import Membership
from schemas.membership import MembershipCreate


async def create_membership(membership_data: MembershipCreate, session: AsyncSession) -> Membership:
    """
    Create a new membership for the workspace.
    """
    try:
        workspace = await MembershipCRUD.create(membership_data, session=session)
        await session.commit()
        return workspace
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def get_membership(user_id: int, workspace_id: int, session: AsyncSession) -> Membership:
    """
    Get user membership in the workspace.
    """
    try:
        membership = await MembershipCRUD.get_user_workspace_membership(
            user_id,
            workspace_id,
            session=session
        )
        return membership
    except Exception as exc:
        raise Exception from exc
