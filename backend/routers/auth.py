from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db_session
from schemas.user import UserRegister
from schemas.token import Token
from schemas.membership import MembershipCreate
from schemas.workspace import WorkspaceCreate
from security import create_access_token
from models.membership import Role
from models.workspace import WorkspaceType
from services import user as user_service
from services import workspace as workspace_service
from services import membership as membership_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(data: UserRegister, session: AsyncSession = Depends(get_db_session)):
    user_registered = await user_service.is_user_registered(data, session)

    if user_registered:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await user_service.create_user(data, session)

    workspace = WorkspaceCreate(
        name=data.workspace_name, type=WorkspaceType.PERSONAL)
    workspace = await workspace_service.create_workspace(workspace, session)

    membership = MembershipCreate(workspace_id=workspace.id,
                                  user_id=user.id, role=Role.OWNER)
    await membership_service.create_membership(membership, session)

    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db_session)):
    user = await user_service.authenticate_user(data.username, data.password, session)
    token = create_access_token(user.id)
    return Token(access_token=token)
