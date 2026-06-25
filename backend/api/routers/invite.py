import uuid
from fastapi import APIRouter, Depends
from core.dependencies import (
    get_database_uow,
    DatabaseSessionUOW
)
from core.roles import get_role_permissions
from schemas.membership import (
    MembershipPermissionsResponse,
    MembershipModel,
)
from api.dependencies import get_current_user_id

from schemas.invite_link import InviteLinkResponse
from services import membership as membership_service
from services import invite_link as invite_link_service


router = APIRouter(prefix="/invites", tags=["workspace invitations"])


@router.get("/{token}", response_model=InviteLinkResponse)
async def validate_invite_link(
    token: str, uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Use invite link to the workspace.

    Used to validate link first before accepting invitation.

    The link will be validated, if valid - get information related to the link.
    """
    async with uow:
        link = await invite_link_service.validate_invite_link(token, session=uow.session)
    return link


@router.post("/{token}/accept", response_model=MembershipPermissionsResponse)
async def accept_link_invitation(
    token: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Accept invitation to the workspace and become its member.

    You can't become a part of workspace if not authorized first.

    Best to validate link and show related information before accepting it blindly.
    """
    async with uow:
        link = await invite_link_service.validate_invite_link(token, session=uow.session)

        membership_model = MembershipModel(
            workspace_id=link.workspace_id,
            user_id=user_id,
            role=link.role
        )

        membership = await membership_service.create_membership(membership_model, uow.session)

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
