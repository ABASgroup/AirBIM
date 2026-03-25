"""Entry point to the app."""
import uvicorn

from fastapi import FastAPI

from config import api_config
from exceptions.handlers import add_exception_handlers

from routers.auth import router as auth_router
from routers.workspace import router as workspace_router
from routers.project import router as project_router

# This app is published behind a proxy under "/api" (for users: https://example.com/api/...).
# The proxy removes (strips) "/api" before sending the request to FastAPI, so our real routes stay like "/test", "/users", etc.
# root_path="/api" tells FastAPI/Swagger: "externally the app lives under /api", so docs and OpenAPI links will use "/api/...".
# So write your routes as normal (without /api and don't name it /api) and it will work both in development and production.
app = FastAPI(root_path="/api")

# include routers here
app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(project_router)

# add exception handlers
add_exception_handlers(app)


@app.get('/ping')
async def ping():
    return {"message": "I'm fine, thank you!"}


# launch
if __name__ == "__main__":
    uvicorn.run("main:app",
                host=api_config.API_HOST,
                port=api_config.API_PORT,
                reload=True)
