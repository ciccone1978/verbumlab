from fastapi import APIRouter
from sqlalchemy import create_engine, text
from app.core.config import settings
import httpx

router = APIRouter()

@router.get("/test-db")
def test_db():
    """
    Check the connectivity to the PostgreSQL database.

    Returns:
        dict: Status message and the sanitized DATABASE_URL.
    """
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {
                "status": "Database is running",
                "database_url": settings.DATABASE_URL.replace(settings.POSTGRES_PASSWORD, "****")
            }
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

@router.get("/test-ollama")
async def test_ollama():
    """
    Check the connectivity to the locally running Ollama instance.

    Returns:
        dict: Status message and a list of available models.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return {
                    "status": "Ollama is running",
                    "models": response.json().get("models", [])
                }
            else:
                return {
                    "status": "Ollama returned an error",
                    "error": response.text
                }
    except Exception as e:
        return {"status": "Ollama connection failed", "error": str(e)}
