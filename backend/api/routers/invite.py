import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import (
    get_db_session,
    get_current_user_id,
)
from core.roles import get_role_permissions
from schemas.membership import (
    MembershipPermissionsResponse,
    MembershipModel,
)
from services import membership as membership_service
from services import invite_link as invite_link_service


router = APIRouter(prefix="/invites", tags=["workspace invitations"])


@router.get("/{token}")
async def validate_invite_link(
    token: str, session: AsyncSession = Depends(get_db_session)
):
    """
    Use invite link to the workspace.

    Used to validate link first before accepting invitation.

    The link will be validated, if valid - get information related to the link.
    """
    link = await invite_link_service.validate_invite_link(token, session=session)
    return link


@router.post("/{token}/accept", response_model=MembershipPermissionsResponse)
async def accept_link_invitation(
    token: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Accept invitation to the workspace and become its member.

    You can't become a part of workspace if not authorized first.

    Best to validate link and show related information before accepting it blindly.
    """
    link = await invite_link_service.validate_invite_link(token, session=session)

    membership_model = MembershipModel(
        workspace_id=link.workspace_id, user_id=user_id, role=link.role
    )

    membership = await membership_service.create_membership(membership_model, session)

    permissions = get_role_permissions(membership.role)
    return MembershipPermissionsResponse(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        permissions=permissions,
        id=membership.id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )
