"""API-specific pytest fixtures."""

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Role
from core.security import create_access_token

from tests.helpers import (
    create_test_membership,
    create_test_user,
    create_test_workspace,
)


@dataclass(frozen=True)
class AuthContext:
    """Authenticated user with workspace membership and Bearer token."""

    access_token: str
    user_id: UUID
    workspace_id: UUID
    role: Role

    @property
    def headers(self) -> dict[str, str]:
        """Get headers for authentication."""
        return {"Authorization": f"Bearer {self.access_token}"}


@pytest_asyncio.fixture(
    params=list(Role),
    ids=[role.value for role in Role],
)
async def auth_context_with_role(
    request: pytest.FixtureRequest,
    db_session: AsyncSession,
) -> AuthContext:
    """User with workspace membership for each role."""
    role: Role = request.param
    suffix = uuid4().hex[:8]

    workspace = await create_test_workspace(db_session)
    user = await create_test_user(
        db_session,
        email=f"file-api-{role.value}-{suffix}@example.com",
        username=f"file-api-{role.value}-{suffix}",
    )
    await create_test_membership(db_session, workspace.id, user.id, role)
    await db_session.commit()

    token = create_access_token(user.id)
    return AuthContext(
        access_token=token,
        user_id=user.id,
        workspace_id=workspace.id,
        role=role,
    )


@pytest_asyncio.fixture
async def auth_context(
    db_session: AsyncSession,
) -> AuthContext:
    """Workspace owner with full permissions for functional API tests."""
    workspace = await create_test_workspace(db_session)
    user = await create_test_user(
        db_session,
        email="file-api-owner@example.com",
        username="file-api-owner",
    )
    await create_test_membership(db_session, workspace.id, user.id, Role.OWNER)
    await db_session.commit()

    token = create_access_token(user.id)
    return AuthContext(
        access_token=token,
        user_id=user.id,
        workspace_id=workspace.id,
        role=Role.OWNER,
    )
