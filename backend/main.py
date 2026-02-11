"""Entry point to the app."""
from fastapi import FastAPI
import uvicorn


app = FastAPI()

# include routers here

# launch
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
