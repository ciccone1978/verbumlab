from fastapi import APIRouter
from app.api.v1.endpoints import utils, llm, documents, chat

api_router = APIRouter()
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
