"""Service layer logic for files."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


def validate_file_request(filename: str, extension: str, size: int):
    """
    Runs checks on the file request:
    
    - file extension
    
    """
    pass    
filename: str
    extension: str
    size: str

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
        except IntegrityError:
            # the token was not unique
            # strange, but let's
            # try again
            await session.rollback()
            continue


async def revoke_links(workspace_id: int, session: AsyncSession):
    """
    All previous links will be removed

    Use to secure access to the workspace
    """
    try:
        # delete old links
        await InviteLinkCRUD.delete_by_workspace_id(workspace_id, session=session)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
