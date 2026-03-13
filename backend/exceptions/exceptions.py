"""Our custom app exceptions"""


class BaseAppError(Exception):
    """Base exception"""

    def __init__(self, message: str = "Unknown error"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(BaseAppError):
    """The requested entity is not found"""


class NotMemberError(BaseAppError):
    """User is not a part of workspace, no membership found"""

    def __init__(self):
        self.message = "No membership found, perhaps, you are not a member"
        super().__init__(self.message)


class AlreadyExistsError(BaseAppError):
    """Object already exists and duplication is prohibited"""

    def __init__(self, entity: str):
        message = f"This {entity} already exists"
        super().__init__(message)


class NoRequiredPermissionError(BaseAppError):
    """A client has no permission to perform the action"""

    def __init__(self, permission: str):
        message = f"You have no permission to perform this action: {permission}"
        super().__init__(message)


class InvalidInvitationError(BaseAppError):
    """Invitation is invalid, expired or fake"""


class InvalidLoginInfoError(BaseAppError):
    """Email or password is invalid"""


class ProhibitedWorkspaceAction(BaseAppError):
    """Workspace prohibits this behavior or action"""

    def __init__(self, action: str):
        message = f"Workspace doesn't allow this: {action}"
        super().__init__(message)
