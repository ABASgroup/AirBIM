"""API integration tests for workspace endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import InviteableRole, Permission, Role
from core.security import create_access_token

from schemas.workspace import WorkspaceType

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    create_team_workspace_via_api,
    gather_responses,
    get_personal_workspace_via_api,
    get_user_workspaces_via_api,
    register_user_via_api,
    role_has_permission,
)
from tests.helpers import (
    create_test_membership,
    create_test_user,
    create_test_workspace,
)


# ---------------------------------------------------------------------------
# Personal workspace created on registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_personal_workspace(api_client: AsyncClient) -> None:
    """Registration should create exactly one personal workspace for the user."""
    user = await register_user_via_api(
        api_client,
        workspace_name="My Personal Space",
    )

    workspaces = await get_user_workspaces_via_api(api_client, user.headers)
    assert len(workspaces) == 1
    assert workspaces[0]["name"] == "My Personal Space"
    assert workspaces[0]["type"] == WorkspaceType.PERSONAL.value


@pytest.mark.asyncio
async def test_personal_workspace_cannot_be_deleted(api_client: AsyncClient) -> None:
    """Owner should not be able to delete their personal workspace."""
    user = await register_user_via_api(api_client)
    personal_workspace = await get_personal_workspace_via_api(api_client, user.headers)

    response = await api_client.delete(
        f"/workspaces/{personal_workspace['id']}",
        headers=user.headers,
    )

    assert response.status_code == 409
    assert "personal workspace" in response.json().get("message", "").lower()

    workspaces = await get_user_workspaces_via_api(api_client, user.headers)
    assert any(workspace["id"] == personal_workspace["id"] for workspace in workspaces)


@pytest.mark.asyncio
async def test_personal_workspace_cannot_create_invite_link(
    api_client: AsyncClient,
) -> None:
    """Personal workspace should not allow generating invite links."""
    user = await register_user_via_api(api_client)
    personal_workspace = await get_personal_workspace_via_api(api_client, user.headers)

    response = await api_client.post(
        f"/workspaces/{personal_workspace['id']}/invites",
        json={"role": InviteableRole.MEMBER.value},
        headers=user.headers,
    )

    assert response.status_code == 409
    assert "personal workspace" in response.json().get("message", "").lower()


# ---------------------------------------------------------------------------
# Team workspace lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_team_workspace_makes_current_user_owner(
    api_client: AsyncClient,
) -> None:
    """POST /workspaces should create a team workspace owned by the caller."""
    user = await register_user_via_api(api_client)
    team_workspace = await create_team_workspace_via_api(
        api_client, user.headers, name="Engineering Team"
    )

    assert team_workspace["name"] == "Engineering Team"
    assert team_workspace["type"] == WorkspaceType.TEAM.value

    access_response = await api_client.get(
        f"/workspaces/{team_workspace['id']}/access",
        headers=user.headers,
    )
    assert access_response.status_code == 200
    access = access_response.json()
    assert access["role"] == Role.OWNER.value
    assert Permission.WORKSPACE_DELETE.value in access["permissions"]


@pytest.mark.asyncio
async def test_get_my_workspaces_returns_personal_and_team(
    api_client: AsyncClient,
) -> None:
    """GET /workspaces/my should list all workspaces the user belongs to."""
    user = await register_user_via_api(api_client)
    team_workspace = await create_team_workspace_via_api(
        api_client, user.headers, name="Design Team"
    )

    workspaces = await get_user_workspaces_via_api(api_client, user.headers)
    workspace_ids = {workspace["id"] for workspace in workspaces}
    workspace_types = {workspace["type"] for workspace in workspaces}

    assert len(workspaces) == 2
    assert team_workspace["id"] in workspace_ids
    assert workspace_types == {WorkspaceType.PERSONAL.value, WorkspaceType.TEAM.value}


@pytest.mark.asyncio
async def test_get_workspace_returns_workspace_data(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """GET /workspaces/{id} should return workspace metadata."""
    response = await api_client.get(
        f"/workspaces/{auth_context.workspace_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(auth_context.workspace_id)
    assert body["type"] == WorkspaceType.TEAM.value
    assert isinstance(body["name"], str)


@pytest.mark.asyncio
async def test_delete_team_workspace_removes_workspace(
    api_client: AsyncClient,
) -> None:
    """DELETE /workspaces/{id} should remove a team workspace."""
    user = await register_user_via_api(api_client)
    team_workspace = await create_team_workspace_via_api(
        api_client, user.headers, name="Temporary Team"
    )
    workspace_id = team_workspace["id"]

    delete_response = await api_client.delete(
        f"/workspaces/{workspace_id}",
        headers=user.headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["id"] == workspace_id

    get_response = await api_client.get(
        f"/workspaces/{workspace_id}",
        headers=user.headers,
    )
    assert get_response.status_code == 403

    workspaces = await get_user_workspaces_via_api(api_client, user.headers)
    assert all(workspace["id"] != workspace_id for workspace in workspaces)


@pytest.mark.asyncio
async def test_get_workspace_access_returns_role_and_permissions(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """GET /workspaces/{id}/access should expose membership role and permissions."""
    response = await api_client.get(
        f"/workspaces/{auth_context.workspace_id}/access",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["workspace_id"] == str(auth_context.workspace_id)
    assert body["user_id"] == str(auth_context.user_id)
    assert body["role"] == auth_context.role.value
    assert Permission.WORKSPACE_VIEW.value in body["permissions"]


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_workspace_members_lists_members(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /workspaces/{id}/memberships/ should return workspace members."""
    member = await create_test_user(
        db_session,
        email="member@example.com",
        username="member",
    )
    await create_test_membership(
        db_session, auth_context.workspace_id, member.id, Role.MEMBER
    )
    await db_session.commit()

    response = await api_client.get(
        f"/workspaces/{auth_context.workspace_id}/memberships/",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    members = response.json()
    member_ids = {entry["user"]["id"] for entry in members}
    assert str(auth_context.user_id) in member_ids
    assert str(member.id) in member_ids


@pytest.mark.asyncio
async def test_remove_member_from_team_workspace(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """DELETE /workspaces/{id}/memberships/{user_id} should remove a non-owner member."""
    member = await create_test_user(
        db_session,
        email="removable@example.com",
        username="removable",
    )
    await create_test_membership(
        db_session, auth_context.workspace_id, member.id, Role.MEMBER
    )
    await db_session.commit()

    response = await api_client.delete(
        f"/workspaces/{auth_context.workspace_id}/memberships/{member.id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == str(member.id)

    members_response = await api_client.get(
        f"/workspaces/{auth_context.workspace_id}/memberships/",
        headers=auth_context.headers,
    )
    member_ids = {entry["user"]["id"] for entry in members_response.json()}
    assert str(member.id) not in member_ids


@pytest.mark.asyncio
async def test_cannot_remove_owner_from_workspace(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Owner removal should be rejected."""
    response = await api_client.delete(
        f"/workspaces/{auth_context.workspace_id}/memberships/{auth_context.user_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 409
    assert "owner" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_change_member_role_updates_membership(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """PATCH /workspaces/{id}/memberships/{user_id}/role should update member role."""
    member = await create_test_user(
        db_session,
        email="role-change@example.com",
        username="role-change",
    )
    await create_test_membership(
        db_session, auth_context.workspace_id, member.id, Role.MEMBER
    )
    await db_session.commit()

    response = await api_client.patch(
        f"/workspaces/{auth_context.workspace_id}/memberships/{member.id}/role",
        params={"role": Role.VIEWER.value},
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == Role.VIEWER.value


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_list_workspace_projects(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Workspace project endpoints should create and list projects."""
    create_response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/projects",
        json={
            "name": "HQ Building",
            "description": "Main construction project",
        },
        headers=auth_context.headers,
    )
    assert create_response.status_code == 200
    created_project = create_response.json()
    assert created_project["name"] == "HQ Building"
    assert created_project["workspace_id"] == str(auth_context.workspace_id)

    list_response = await api_client.get(
        f"/workspaces/{auth_context.workspace_id}/projects",
        headers=auth_context.headers,
    )
    assert list_response.status_code == 200
    projects = list_response.json()
    assert any(project["id"] == created_project["id"] for project in projects)


# ---------------------------------------------------------------------------
# Invites (team workspace)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_invite_link_for_team_workspace(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """POST /workspaces/{id}/invites should return a token for team workspaces."""
    response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/invites",
        json={"role": InviteableRole.MEMBER.value},
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["token"], str)
    assert body["token"]
    assert body["workspace"]["id"] == str(auth_context.workspace_id)
    assert body["created_by"]["id"] == str(auth_context.user_id)


@pytest.mark.asyncio
async def test_revoke_invite_links_for_team_workspace(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """POST /workspaces/{id}/invites/revoke should succeed for team workspaces."""
    create_response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/invites",
        json={"role": InviteableRole.VIEWER.value},
        headers=auth_context.headers,
    )
    assert create_response.status_code == 200

    revoke_response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/invites/revoke",
        headers=auth_context.headers,
    )
    assert revoke_response.status_code == 200


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_workspace_tasks_returns_list(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """POST /workspaces/{id}/tasks should return workspace tasks list."""
    response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/tasks",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_workspace_members_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
) -> None:
    """Members list should require MEMBERS_VIEW permission."""
    response = await api_client.get(
        f"/workspaces/{auth_context_with_role.workspace_id}/memberships/",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.MEMBERS_VIEW):
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_project_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
) -> None:
    """Project creation should require PROJECT_CREATE permission."""
    response = await api_client.post(
        f"/workspaces/{auth_context_with_role.workspace_id}/projects",
        json={"name": "Restricted Project", "description": "Test"},
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.PROJECT_CREATE):
        assert response.status_code == 200
        assert response.json()["name"] == "Restricted Project"
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_workspace_endpoints_return_401_without_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Workspace endpoints should reject unauthenticated requests."""
    workspace = await create_test_workspace(db_session)
    protected_requests = [
        api_client.get(f"/workspaces/{workspace.id}"),
        api_client.get(f"/workspaces/{workspace.id}/memberships/"),
        api_client.post(f"/workspaces/{workspace.id}/projects"),
        api_client.post(f"/workspaces/{workspace.id}/invites"),
        api_client.post(f"/workspaces/{workspace.id}/invites/revoke"),
        api_client.post(f"/workspaces/{workspace.id}/tasks"),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_workspace_endpoints_return_403_for_non_member(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Workspace endpoints should reject users who are not members."""
    workspace = await create_test_workspace(db_session)
    outsider = await create_test_user(
        db_session,
        email="workspace-outsider@example.com",
        username="workspace-outsider",
    )
    other_workspace = await create_test_workspace(db_session)
    await create_test_membership(
        db_session, other_workspace.id, outsider.id, Role.OWNER
    )
    await db_session.commit()

    outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

    protected_requests = [
        api_client.get(f"/workspaces/{workspace.id}", headers=outsider_headers),
        api_client.get(
            f"/workspaces/{workspace.id}/memberships/", headers=outsider_headers
        ),
        api_client.post(
            f"/workspaces/{workspace.id}/projects", headers=outsider_headers
        ),
        api_client.post(
            f"/workspaces/{workspace.id}/invites", headers=outsider_headers
        ),
        api_client.post(
            f"/workspaces/{workspace.id}/invites/revoke", headers=outsider_headers
        ),
        api_client.post(f"/workspaces/{workspace.id}/tasks", headers=outsider_headers),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_workspace_endpoints_returns_403_for_unrelated_workspace(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /workspaces/{id} should reject users who are not workspace members."""
    other_workspace = await create_test_workspace(db_session)
    await db_session.commit()

    requests = [
        api_client.get(
            f"/workspaces/{other_workspace.id}", headers=auth_context.headers
        ),
        api_client.get(
            f"/workspaces/{other_workspace.id}/memberships/",
            headers=auth_context.headers,
        ),
        api_client.post(
            f"/workspaces/{other_workspace.id}/projects", headers=auth_context.headers
        ),
        api_client.post(
            f"/workspaces/{other_workspace.id}/invites", headers=auth_context.headers
        ),
        api_client.post(
            f"/workspaces/{other_workspace.id}/invites/revoke",
            headers=auth_context.headers,
        ),
        api_client.post(
            f"/workspaces/{other_workspace.id}/tasks", headers=auth_context.headers
        ),
    ]

    for response in await gather_responses(list(requests)):
        assert response.status_code == 403
