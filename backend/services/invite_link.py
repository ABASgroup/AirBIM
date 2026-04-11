"""Service layer logic for InviteLink."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core.roles import Role, InviteableRole
from core.exceptions.exceptions import InvalidInvitationError
from repositories.invite_link import InviteLinkRepository
from models.invite_link import InviteLink
from schemas.invite_link import InviteLinkModel, InviteLinkResponse
from core.security import generate_link_token, hash_link_token


async def generate_invite_link(
    workspace_id: uuid.UUID,
    creator_id: uuid.UUID,
    role: InviteableRole,
    session: AsyncSession
) -> InviteLinkResponse:
    """
    Generates new unique role invite link.

    DB requires all links to be unique, tries to generate token again
    if there :class:`~sqlalchemy.exc.IntegrityError`.
    """
    while True:
        try:
            # hide token!
            token = generate_link_token()
            token_hashed = hash_link_token(token)

            invite_link_data = InviteLinkModel(token_hashed=token_hashed,
                                               workspace_id=workspace_id,
                                               creator_id=creator_id,
                                               role=Role(role))

            await InviteLinkRepository.create(invite_link_data, session=session)

            # output public information
            # token is not hashed, we need to output it first
            link_out = InviteLinkResponse(
                token=token, workspace_id=workspace_id, role=role)
            await session.commit()
            return link_out
        except IntegrityError:
            # the token was not unique
            # strange, but let's
            # try again
            await session.rollback()
            continue


async def revoke_links(workspace_id: uuid.UUID, session: AsyncSession):
    """
    Removes all previous (existing) invite links for the workspace.

    Use to secure access to the workspace, when links are compromised.
    """
    try:
        # delete old links
        await InviteLinkRepository.delete_by_workspace_id(workspace_id, session=session)
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def validate_invite_link(token: str, session: AsyncSession) -> InviteLinkResponse:
    """
    Validates invite link using its token.

    Invalid link's token will not be found in the DB.
    """
    try:
        # try to find hashed token
        # reminder: hash is determined
        token_hashed = hash_link_token(token)
        link = await InviteLinkRepository.get_by_token(token_hashed, session=session)

        # link is not found, token is invalid
        if link is None:
            raise InvalidInvitationError("Invite link is invalid: token has not passed")

        # still want to send back not hashed token
        public_link = InviteLinkResponse(
            token=token,
            workspace_id=link.workspace_id,
            role=InviteableRole(link.role))
        return public_link
    except Exception:
        await session.rollback()
        raise
