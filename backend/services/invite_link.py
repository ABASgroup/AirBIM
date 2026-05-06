"""Service layer logic for InviteLink."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core.roles import Role, InviteableRole
from core.exceptions import InvalidInvitationError, NotFoundError, ProhibitedWorkspaceActionError
from repositories.invite_link import InviteLinkRepository
from repositories.workspace import WorkspaceRepository
from models.invite_link import InviteLink
from models.workspace import WorkspaceType
from schemas.invite_link import InviteLinkModel
from core.security import generate_link_token, hash_link_token


async def generate_invite_link(
    workspace_id: uuid.UUID,
    creator_id: uuid.UUID,
    role: InviteableRole,
    session: AsyncSession
) -> tuple[InviteLink, str]:
    """
    Generates new unique role invite link.

    You can't generate link for personal workspaces.

    DB requires all links to be unique, tries to generate token again
    if there :class:`~sqlalchemy.exc.IntegrityError`.

    Returns tuple of invite link and token (not hashed, for client).
    """
    while True:
        try:
            # check workspace type first
            workspace = await WorkspaceRepository.get_by_id(workspace_id, session=session)
            if workspace is None:
                raise NotFoundError("Workspace not found")
            if workspace.type == WorkspaceType.PERSONAL:
                raise ProhibitedWorkspaceActionError(
                    "creating invite link for a personal workspace")

            # hide token!
            token = generate_link_token()
            token_hashed = hash_link_token(token)

            invite_link_data = InviteLinkModel(token_hashed=token_hashed,
                                               workspace_id=workspace_id,
                                               creator_id=creator_id,
                                               role=Role(role))

            link = await InviteLinkRepository.create(invite_link_data, session=session)

            link = await InviteLinkRepository.refresh(link, session=session, relations=["created_by", "workspace"])

            # token is not hashed, ALWAYS return token
            return link, token
        except IntegrityError:
            # the token was not unique
            # strange, but let's
            # try again
            continue


async def revoke_links(workspace_id: uuid.UUID, session: AsyncSession):
    """
    Removes all previous (existing) invite links for the workspace.

    Use to secure access to the workspace, when links are compromised.
    """
    # delete old links
    await InviteLinkRepository.delete_by_workspace_id(workspace_id, session=session)


async def validate_invite_link(token: str, session: AsyncSession) -> InviteLink:
    """
    Validates invite link using its token.

    Invalid link's token will not be found in the DB.
    """
    # try to find hashed token
    # reminder: hash is determined
    token_hashed = hash_link_token(token)
    link = await InviteLinkRepository.get_by_token(token_hashed, session=session)

    # link is not found, token is invalid
    if link is None:
        raise InvalidInvitationError(
            "Invite link is invalid: token has not passed")

    # still want to send back not hashed token
    return link
