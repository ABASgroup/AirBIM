"""FastAPI related dependencies."""
import uuid
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from core.configs.api import api_config
from core.roles import ROLE_PERMISSIONS, Permission
from core.exceptions import NoRequiredPermissionError, NotFoundError, NotMemberError
from core.dependencies import get_session_maker

from services.membership import get_membership
from services.stage import get_stage_with_project
from services.project import get_project
from services.file import FileService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_db_session_dependency():
    """
    DEPRECATED: use :func:`core.dependencies.get_database_uow` instead.

    Provides session.

    Use as a dependency.

    DOES NOT COMMIT CHANGES AUTOMATICALLY.

    HAS NOT ANY SESSION CONTROL MECHANISMS.

    Don't forget to use `session.commit()` when
    making changes in database.

    Otherwise changes will be lost.
    """
    session_factory = get_session_maker()
    async with session_factory() as session:
        yield session


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """
    Get current user ID using a JWT token.

    Will work only if user is authenticated and provides a valid token.
    """
    try:
        payload = jwt.decode(token,
                             api_config.JWT_SECRET_KEY,
                             algorithms=[api_config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError
        # cast the type to user id matching the database ID type
        return uuid.UUID(user_id)
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
    """
    async def checker(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session_dependency)
    ):
        membership = await get_membership(
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
    """
    async def checker(
        project_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session_dependency)
    ):
        project = await get_project(project_id, session=session)

        membership = await get_membership(
            user_id,
            project.workspace_id,
            session)

        if membership is None:
            raise NotMemberError()

        if permission not in ROLE_PERMISSIONS[membership.role]:
            raise NoRequiredPermissionError(permission.value)
        return membership
    return checker


def require_stage_permission(permission: Permission):
    """
    Require certain membership permission from user to access an endpoint.

    Uses stage to validate permission.

    Requires membership in the workspace.
    """
    async def checker(
        stage_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session_dependency)
    ):
        stage = await get_stage_with_project(stage_id, session=session)

        membership = await get_membership(
            user_id,
            stage.project.workspace_id,
            session)

        if membership is None:
            raise NotMemberError()

        if permission not in ROLE_PERMISSIONS[membership.role]:
            raise NoRequiredPermissionError(permission.value)
        return membership
    return checker


def require_file_permission(permission: Permission):
    """
    Require certain membership permission from user to access an endpoint.

    Uses file to validate permission.

    Requires membership in the workspace.
    """
    async def checker(
        file_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session_dependency)
    ):
        file = await FileService.get_file(file_id, session=session)

        membership = await get_membership(
            user_id,
            file.workspace_id,
            session)

        if membership is None:
            raise NotMemberError()

        if permission not in ROLE_PERMISSIONS[membership.role]:
            raise NoRequiredPermissionError(permission.value)
        return membership
    return checker
