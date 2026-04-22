"""Entry point to the app."""
from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI

from core.configs.api import api_config
from api.handlers import add_exception_handlers

from api.routers.auth import router as auth_router
from api.routers.workspace import router as workspace_router
from api.routers.project import router as project_router
from api.routers.stage import router as stage_router
from api.routers.invite import router as invite_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: resource initialization

    yield

    # shutdown: resource cleanup


# This app is published behind a proxy under "/api" (for users: https://example.com/api/...).
# The proxy removes (strips) "/api" before sending the request to FastAPI, so our real routes stay like "/test", "/users", etc.
# root_path="/api" tells FastAPI/Swagger: "externally the app lives under /api", so docs and OpenAPI links will use "/api/...".
# So write your routes as normal (without /api and don't name it /api) and it will work both in development and production.
app = FastAPI(root_path="/api", lifespan=lifespan)

# include routers here
app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(project_router)
app.include_router(stage_router)
app.include_router(invite_router)

# add exception handlers
add_exception_handlers(app)


@app.get('/ping')
async def ping():
    """Simple API check endpoint."""
    return {"message": "I'm fine, thank you!"}


# launch
if __name__ == "__main__":
    uvicorn.run("main:app",
                host=api_config.API_HOST,
                port=api_config.API_PORT,
                reload=True)
