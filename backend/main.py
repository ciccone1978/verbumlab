from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(title="VerbumLab API", version="0.1.0")

@app.get("/")
def read_root():
    """
    Root endpoint to welcome users to the VerbumLab API.
    """
    return {"message": "Welcome to VerbumLab API"}

app.include_router(api_router, prefix="/api/v1")