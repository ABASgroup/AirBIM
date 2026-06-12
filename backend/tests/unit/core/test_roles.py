"""Unit tests for core.roles, ensuring that each role has the correct permissions assigned."""

from core.roles import Permission, Role, get_role_permissions


def test_role_permissions() -> None:
    """Test that each role has the correct permissions assigned."""
    viewer_perms = get_role_permissions(Role.VIEWER)
    member_perms = get_role_permissions(Role.MEMBER)
    admin_perms = get_role_permissions(Role.ADMIN)
    owner_perms = get_role_permissions(Role.OWNER)

    # Check that viewer has only view permissions
    assert Permission.WORKSPACE_VIEW in viewer_perms
    assert Permission.PROJECT_VIEW in viewer_perms
    assert Permission.STAGE_VIEW in viewer_perms
    assert Permission.FILES_VIEW in viewer_perms
    assert Permission.FILES_DOWNLOAD in viewer_perms
    assert Permission.RECORDING_RESULT_VIEW in viewer_perms
    assert len(viewer_perms) == 6

    # Check that member has all viewer permissions plus edit/upload permissions
    for perm in viewer_perms:
        assert perm in member_perms
    assert Permission.PROJECT_EDIT in member_perms
    assert Permission.STAGE_CREATE in member_perms
    assert Permission.STAGE_EDIT in member_perms
    assert Permission.FILES_UPLOAD in member_perms
    assert Permission.MEMBERS_INVITE in member_perms
    assert Permission.MEMBERS_VIEW in member_perms
    assert Permission.RECORDING_RESULT_DELETE in member_perms

    # Check that admin has all member permissions plus delete and invite/remove permissions
    for perm in member_perms:
        assert perm in admin_perms
    assert Permission.PROJECT_CREATE in admin_perms
    assert Permission.PROJECT_DELETE in admin_perms
    assert Permission.STAGE_DELETE in admin_perms
    assert Permission.FILES_DELETE in admin_perms
    assert Permission.MEMBERS_REMOVE in admin_perms
    assert Permission.MEMBERS_EDIT_ROLE in admin_perms

    # Check that owner has all permissions (same as admin but also includes MEMBERS_VIEW)
    for perm in admin_perms:
        assert perm in owner_perms
