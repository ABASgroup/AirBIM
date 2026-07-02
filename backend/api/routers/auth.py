from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserRegisterRequest, UserUpdate, UserResponse
from schemas.token import TokenResponse
from schemas.membership import MembershipModel
from schemas.workspace import WorkspaceModel
from core.roles import Role, Permission
from core.dependencies import get_database_uow, DatabaseSessionUOW
from api.dependencies import get_current_user_id_from_refresh_token, get_current_user_id
from models.workspace import WorkspaceType
from services.auth import AuthService
from services.workspace import WorkspaceService
from services import membership as membership_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegisterRequest, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Registers a new user and creates their personal workspace.
    """
    async with uow:
        user = await AuthService.register_user(data, uow.session)

        workspace = WorkspaceModel(
            name=data.workspace_name, type=WorkspaceType.PERSONAL)
        workspace = await WorkspaceService.create_workspace(workspace, uow.session)

        membership = MembershipModel(
            workspace_id=workspace.id,
            user_id=user.id,
            role=Role.OWNER
        )

        await membership_service.create_membership(membership, uow.session)

        access_token, refresh_token = await AuthService.create_tokens(
            user_id=user.id,
            session=uow.session
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Logs user in, provides access token.

    Login data is `email` and `password`, not username.
    """
    async with uow:
        user = await AuthService.authenticate_user(data.username, data.password, uow.session)
        access_token, refresh_token = await AuthService.create_tokens(
            user.id,
            session=uow.session
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/tokens/refresh", response_model=TokenResponse)
async def refresh_tokens(
    user_id: UUID = Depends(get_current_user_id_from_refresh_token),
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Get new access and refresh tokens using old refresh token.

    Requires user to be authorized.
    """
    async with uow:
        access_token, refresh_token = await AuthService.update_tokens(
            user_id,
            session=uow.session
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.patch("", response_model=UserResponse)
async def edit_user(
    user_id: UUID = Depends(get_current_user_id),
    user_data: UserUpdate = Depends(),
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Update current user info.
    """
    async with uow:
        user = await AuthService.update_user(user_id, user_data, uow.session)

    return user


@router.get("/permissions")
async def permissions():
    """
    Get all possible permissions in the system.

    Useful for client to know what users can do.
    """
    return [member.value for member in Permission]


@router.get("/roles")
async def roles():
    """
    Get all possible roles in the system.

    Useful for client to know what users can be.
    """
    return [member.value for member in Role]
