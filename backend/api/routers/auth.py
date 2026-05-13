from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserRegisterRequest
from schemas.token import TokenResponse
from schemas.membership import MembershipModel
from schemas.workspace import WorkspaceModel
from core.security import create_access_token
from core.roles import Role, Permission
from core.dependencies import get_database_uow, DatabaseSessionUOW
from models.workspace import WorkspaceType
from services import user as user_service
from services import workspace as workspace_service
from services import membership as membership_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegisterRequest, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Registers a new user and creates their personal workspace.
    """
    async with uow:
        user = await user_service.register_user(data, uow.session)

        workspace = WorkspaceModel(
            name=data.workspace_name, type=WorkspaceType.PERSONAL)
        workspace = await workspace_service.create_workspace(workspace, uow.session)

        membership = MembershipModel(workspace_id=workspace.id,
                                    user_id=user.id, role=Role.OWNER)
        await membership_service.create_membership(membership, uow.session)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer")


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
        user = await user_service.authenticate_user(data.username, data.password, uow.session)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


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
