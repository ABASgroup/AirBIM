"""Dependencies used in the app."""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from storage import Storage
from config import api_config
from roles import ROLE_PERMISSIONS, Permission
from crud.membership import MembershipCRUD
from crud.project import ProjectCRUD
from database import session_maker
from exceptions.exceptions import NoRequiredPermissionError, NotFoundError, NotMemberError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

storage = Storage()


async def get_db_session():
    """
    Provides session to an endpoint.

    Use as a dependency.

    Don't forget to use `session.commit()` when
    making changes in database.

    Otherwise changes will be lost.
    """
    async with session_maker() as session:
        yield session


def get_storage():
    """Get storage as a dependency"""
    return storage


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """
    Get current user ID using a JWT token
    """
    try:
        payload = jwt.decode(token,
                             api_config.JWT_SECRET_KEY,
                             algorithms=[api_config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError
        return int(user_id)
    except JWTError as exc:
        credentials_exception = HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception from exc


def require_workspace_permission(permission: Permission):
    """
    Require certain membership permission from user to access an endpoint.

    Uses workspace to validate permission.

    Requires membership in the workspace.

    You can use it instead of :func:`get_current_user_id` to
    protect an endpoint.
    """
    async def checker(
        workspace_id: int,
        user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session)
    ):
        membership = await MembershipCRUD.get_user_workspace_membership(
            user_id,
            workspace_id,
            session)

        if membership is None:
            raise NotMemberError()

        if permission not in ROLE_PERMISSIONS[membership.role]:
            raise NoRequiredPermissionError(permission.value)
        return membership
    return checker


def require_project_permission(permission: Permission):
    """
    Require certain membership permission from user to access an endpoint.

    Uses project to validate permission.

    Requires membership in the workspace.

    You can use it instead of :func:`get_current_user_id` to
    protect an endpoint.
    """
    async def checker(
        project_id: int,
        user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session)
    ):
        project = await ProjectCRUD.get_by_id(project_id, session=session)

        if project is None:
            raise NotFoundError("No project with this ID.")

        membership = await MembershipCRUD.get_user_workspace_membership(
            user_id,
            project.workspace_id,
            session)

        if membership is None:
            raise NotMemberError()

        if permission not in ROLE_PERMISSIONS[membership.role]:
            raise NoRequiredPermissionError(permission.value)
        return membership
    return checker
