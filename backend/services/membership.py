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
