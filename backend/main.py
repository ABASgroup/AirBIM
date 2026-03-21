"""Entry point to the app."""
from typing import Annotated
import uvicorn

from fastapi import Depends, FastAPI, UploadFile

from config import api_config
from dependencies import oauth2_scheme
from exceptions.handlers import add_exception_handlers

from routers.auth import router as auth_router
from routers.workspace import router as workspace_router

from storage import Storage
from dependencies import get_storage

# This app is published behind a proxy under "/api" (for users: https://example.com/api/...).
# The proxy removes (strips) "/api" before sending the request to FastAPI, so our real routes stay like "/test", "/users", etc.
# root_path="/api" tells FastAPI/Swagger: "externally the app lives under /api", so docs and OpenAPI links will use "/api/...".
# So write your routes as normal (without /api and don't name it /api) and it will work both in development and production.
app = FastAPI(root_path="/api")

# include routers here
app.include_router(auth_router)
app.include_router(workspace_router)

# add exception handlers
add_exception_handlers(app)


@app.get('/test/')
async def test(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


# launch
if __name__ == "__main__":
    uvicorn.run("main:app",
                host=api_config.API_HOST,
                port=api_config.API_PORT,
                reload=True)
