"""Service layer logic for InviteLink."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.workspace import Workspace
from roles import Role, InviteableRole
from crud.invite_link import InviteLinkCRUD
from schemas.invite_link import InviteLinkCreate
from security import generate_link_token, hash_link_token
from models.invite_link import InviteLink


async def generate_invite_link(
    workspace_id: int,
    role: InviteableRole,
    session: AsyncSession
) -> InviteLink:
    """
    Generates new unique role invite link

    DB requires all links to be unique, tries to generate token again
    if there :class:`~sqlalchemy.exc.IntegrityError`
    """
    while True:
        try:
            # hide token!
            token = hash_link_token(generate_link_token())

            invite_link_data = InviteLinkCreate(token_hashed=token,
                                                workspace_id=workspace_id,
                                                role=Role(role))

            link = await InviteLinkCRUD.create(invite_link_data, session=session)
            return link
        except IntegrityError:
            # the token was not unique
            # try again
            await session.rollback()
            continue


async def create_new_invite_links(workspace_id: int, session: AsyncSession) -> list[InviteLink]:
    """
    Create new invite links for the team workspace

    All previous links will be removed
    """
    try:
        # delete old links
        await InviteLinkCRUD.delete_by_workspace_id(workspace_id, session=session)

        # generate new links for inviteable roles
        # they should be unique
        links = []
        for role in InviteableRole:
            link = await generate_invite_link(workspace_id, role, session=session)
            links.append(link)

        await session.commit()
        return links
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def get_invite_link(workspace_id: int, role: InviteableRole, session: AsyncSession) -> InviteLink:
    """
    Get role invite link for the workspace
    """
    try:
        converted_role = Role(role.value)
        link = await InviteLinkCRUD.get_by_workspace_id_and_role(
            workspace_id, converted_role, session=session
        )
        return link
    except Exception as exc:
        raise Exception from exc


async def validate_invite_link(token: str, session: AsyncSession) -> Workspace:
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

        return link
    except Exception as exc:
        raise Exception from exc
