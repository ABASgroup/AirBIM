"""API integration tests for invite endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import InviteableRole, Permission, Role
from core.security import create_access_token

from main import app

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    create_invite_link_via_api,
    create_team_workspace_via_api,
    get_user_workspaces_via_api,
    register_user_via_api,
)
from tests.helpers import create_test_membership, create_test_user


# ---------------------------------------------------------------------------
# GET /invites/{token}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_invite_link_returns_workspace_info(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """GET /invites/{token} should return workspace and creator for a valid token."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
        role=InviteableRole.MEMBER,
    )

    response = await api_client.get(f"/invites/{invite['token']}")

    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["id"] == str(auth_context.workspace_id)
    assert body["workspace"]["type"] == "team"
    assert body["created_by"]["id"] == str(auth_context.user_id)


@pytest.mark.asyncio
async def test_validate_invite_link_does_not_require_authentication(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Invite validation should be accessible without Bearer token."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
    )

    response = await api_client.get(f"/invites/{invite['token']}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_validate_invite_link_returns_422_for_invalid_token(
    api_client: AsyncClient,
) -> None:
    """GET /invites/{token} should reject unknown tokens."""
    response = await api_client.get("/invites/not-a-valid-token")

    assert response.status_code == 422
    assert "invalid" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_validate_invite_link_returns_422_after_revocation(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Revoked invite links should no longer validate."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
    )

    revoke_response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/invites/revoke",
        headers=auth_context.headers,
    )
    assert revoke_response.status_code == 200

    response = await api_client.get(f"/invites/{invite['token']}")

    assert response.status_code == 422
    assert "invalid" in response.json().get("message", "").lower()


# ---------------------------------------------------------------------------
# POST /invites/{token}/accept
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accept_invite_requires_authentication(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """POST /invites/{token}/accept should reject unauthenticated requests."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
    )

    response = await api_client.post(f"/invites/{invite['token']}/accept")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_accept_invite_adds_user_to_workspace(
    api_client: AsyncClient,
) -> None:
    """Accepting an invite should create membership in the target workspace."""
    owner = await register_user_via_api(api_client)
    team_workspace = await create_team_workspace_via_api(
        api_client, owner.headers, name="Collaboration Team"
    )
    invite = await create_invite_link_via_api(
        api_client,
        team_workspace["id"],
        owner.headers,
        role=InviteableRole.MEMBER,
    )

    invitee = await register_user_via_api(api_client)
    workspaces_before = await get_user_workspaces_via_api(api_client, invitee.headers)
    assert len(workspaces_before) == 1

    validate_response = await api_client.get(f"/invites/{invite['token']}")
    assert validate_response.status_code == 200

    accept_response = await api_client.post(
        f"/invites/{invite['token']}/accept",
        headers=invitee.headers,
    )

    assert accept_response.status_code == 200
    membership = accept_response.json()
    assert membership["workspace_id"] == team_workspace["id"]
    assert membership["role"] == Role.MEMBER.value
    assert Permission.PROJECT_VIEW.value in membership["permissions"]

    workspaces_after = await get_user_workspaces_via_api(api_client, invitee.headers)
    workspace_ids = {workspace["id"] for workspace in workspaces_after}
    assert team_workspace["id"] in workspace_ids
    assert len(workspaces_after) == 2

    access_response = await api_client.get(
        f"/workspaces/{team_workspace['id']}/access",
        headers=invitee.headers,
    )
    assert access_response.status_code == 200
    assert access_response.json()["role"] == Role.MEMBER.value


@pytest.mark.asyncio
async def test_accept_invite_assigns_viewer_role_from_link(
    api_client: AsyncClient,
) -> None:
    """Invite role should be applied to the membership created on accept."""
    owner = await register_user_via_api(api_client)
    team_workspace = await create_team_workspace_via_api(api_client, owner.headers)
    invite = await create_invite_link_via_api(
        api_client,
        team_workspace["id"],
        owner.headers,
        role=InviteableRole.VIEWER,
    )
    invitee = await register_user_via_api(api_client)

    response = await api_client.post(
        f"/invites/{invite['token']}/accept",
        headers=invitee.headers,
    )

    assert response.status_code == 200
    membership = response.json()
    assert membership["role"] == Role.VIEWER.value
    assert Permission.FILES_VIEW.value in membership["permissions"]
    assert Permission.PROJECT_CREATE.value not in membership["permissions"]


@pytest.mark.asyncio
async def test_accept_invite_returns_422_for_invalid_token(
    api_client: AsyncClient,
) -> None:
    """POST /invites/{token}/accept should reject invalid tokens."""
    user = await register_user_via_api(api_client)

    response = await api_client.post(
        "/invites/invalid-token/accept",
        headers=user.headers,
    )

    assert response.status_code == 422
    assert "invalid" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_accept_invite_returns_422_after_revocation(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Revoked invite links should not be acceptable."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
    )
    invitee = await register_user_via_api(api_client)

    revoke_response = await api_client.post(
        f"/workspaces/{auth_context.workspace_id}/invites/revoke",
        headers=auth_context.headers,
    )
    assert revoke_response.status_code == 200

    response = await api_client.post(
        f"/invites/{invite['token']}/accept",
        headers=invitee.headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_accept_invite_returns_error_when_already_member(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """Accepting an invite for a workspace the user already belongs to should fail."""
    invite = await create_invite_link_via_api(
        api_client,
        auth_context.workspace_id,
        auth_context.headers,
    )
    existing_member = await create_test_user(
        db_session,
        email="existing-member@example.com",
        username="existing-member",
    )
    await create_test_membership(
        db_session,
        auth_context.workspace_id,
        existing_member.id,
        Role.MEMBER,
    )
    await db_session.commit()

    member_headers = {
        "Authorization": f"Bearer {create_access_token(existing_member.id)}"
    }

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/invites/{invite['token']}/accept",
            headers=member_headers,
        )

    assert response.status_code == 500
