"""FastAPI"""
import logging

from fastapi import status
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import *


logger = logging.getLogger(__name__)


# handlers
# don't forget to put HTTP codes
async def handle_unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )


async def not_found_handler(request: Request, exc: NotFoundError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=404,
        content={"message": exc.message}
    )


async def not_member_handler(request: Request, exc: NotMemberError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=403,
        content={"message": exc.message}
    )


async def already_exists_handler(request: Request, exc: AlreadyExistsError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=409,
        content={"message": exc.message}
    )


async def no_required_permission_handler(request: Request, exc: NoRequiredPermissionError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=403,
        content={"message": exc.message}
    )


async def invalid_invitation_handler(request: Request, exc: InvalidInvitationError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=422,
        content={"message": exc.message}
    )


async def invalid_login_info_handler(request: Request, exc: InvalidLoginInfoError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=401,
        content={"message": exc.message}
    )


async def prohibited_workspace_action_handler(request: Request, exc: ProhibitedWorkspaceActionError):
    logger.exception(f"App exception: {exc}")
    return JSONResponse(
        status_code=409,
        content={"message": exc.message}
    )


def add_exception_handlers(app: FastAPI):
    """Registers exceptions handlers"""
    app.add_exception_handler(Exception, handle_unhandled_exception)
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(NotMemberError, not_member_handler)
    app.add_exception_handler(AlreadyExistsError, already_exists_handler)
    app.add_exception_handler(
        NoRequiredPermissionError, no_required_permission_handler)
    app.add_exception_handler(InvalidInvitationError,
                              invalid_invitation_handler)
    app.add_exception_handler(InvalidLoginInfoError,
                              invalid_login_info_handler)
    app.add_exception_handler(
        ProhibitedWorkspaceActionError, prohibited_workspace_action_handler)
