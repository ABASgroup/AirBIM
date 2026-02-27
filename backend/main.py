"""Entry point to the app."""
from typing import Annotated
import uvicorn
from fastapi import Depends, FastAPI
from config import api_config
from dependencies import oauth2_scheme
from routers.auth import router as auth_router

app = FastAPI()

# include routers here
app.include_router(auth_router)


@app.get('/test/')
async def test(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

# launch
if __name__ == "__main__":
    uvicorn.run("main:app",
                host=api_config.API_HOST,
                port=api_config.API_PORT,
                reload=True)
