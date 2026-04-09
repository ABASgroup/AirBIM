from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db_session
from schemas.user import UserRegisterRequest
from schemas.token import TokenResponse
from schemas.membership import MembershipModel
from schemas.workspace import WorkspaceModel
from security import create_access_token
from roles import Role, Permission
from models.workspace import WorkspaceType
from services import user as user_service
from services import workspace as workspace_service
from services import membership as membership_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegisterRequest, session: AsyncSession = Depends(get_db_session)):
    """
    Registers user and creates their personal workspace.
    """
    user = await user_service.register_user(data, session)

    workspace = WorkspaceModel(
        name=data.workspace_name, type=WorkspaceType.PERSONAL)
    workspace = await workspace_service.create_workspace(workspace, session)

    membership = MembershipModel(workspace_id=workspace.id,
                                 user_id=user.id, role=Role.OWNER)
    await membership_service.create_membership(membership, session)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Logs user in, provides access token.

    Login data is email and password.
    """
    user = await user_service.authenticate_user(data.username, data.password, session)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/permissions")
async def permissions():
    """
    Get all possible permissions in the system
    """
    return [member.value for member in Permission]


@router.get("/roles")
async def roles():
    """
    Get all possible roles in the system
    """
    return [member.value for member in Role]
