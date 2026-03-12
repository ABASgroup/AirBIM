"""Service layer logic for InviteLink."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.workspace import Workspace
from roles import Role, InviteableRole
from crud.invite_link import InviteLinkCRUD
from schemas.invite_link import InviteLinkCreate, InviteLinkPublic
from security import generate_link_token, hash_link_token
from models.invite_link import InviteLink


async def generate_invite_link(
    workspace_id: int,
    creator_id: int,
    role: InviteableRole,
    session: AsyncSession
) -> InviteLinkPublic:
    """
    Generates new unique role invite link

    DB requires all links to be unique, tries to generate token again
    if there :class:`~sqlalchemy.exc.IntegrityError`
    """
    while True:
        try:
            # hide token!
            token = generate_link_token()
            token_hashed = hash_link_token(token)

            invite_link_data = InviteLinkCreate(token_hashed=token_hashed,
                                                workspace_id=workspace_id,
                                                creator_id=creator_id,
                                                role=Role(role))

            link = await InviteLinkCRUD.create(invite_link_data, session=session)

            # output public information
            link_out = InviteLinkPublic(
                token=token, workspace_id=workspace_id, role=role)
            await session.commit()
            return link_out
        except IntegrityError as exc:
            # the token was not unique
            # strange, but let's
            # try again
            await session.rollback()
            continue


async def refresh_links(workspace_id: int, session: AsyncSession) -> list[InviteLink]:
    """
    All previous links will be removed

    Use to secure access to the workspace
    """
    try:
        # delete old links
        links = await InviteLinkCRUD.delete_by_workspace_id(workspace_id, session=session)

        await session.commit()
        return list(links)
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def validate_invite_link(token: str, session: AsyncSession) -> InviteLinkPublic:
    """
    Validates invite link using its token

    Invalid link's token will not be found in the DB
    """
    try:
        # try to find hashed token
        # reminder: hash is determined
        token_hashed = hash_link_token(token)
        link = await InviteLinkCRUD.get_by_token(token_hashed, session=session)

        # link is not found, token is invalid
        if link is None:
            raise Exception

        public_link = InviteLinkPublic(
            token=token,
            workspace_id=link.workspace_id,
            role=InviteableRole(link.role))
        return public_link
    except Exception as exc:
        raise Exception from exc
