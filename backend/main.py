"""Entry point to the app."""
import uvicorn
from fastapi import FastAPI
from config import api_config

app = FastAPI()

# include routers here

# launch
if __name__ == "__main__":
    uvicorn.run("main:app",
                host=api_config.API_HOST,
                port=api_config.API_PORT,
                reload=True)
