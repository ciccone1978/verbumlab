from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import chat_service

router = APIRouter()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question based on retrieved document context.
    
    This endpoint:
    1. Performs high-quality retrieval using hybrid search.
    2. Formats context with document and page citations.
    3. Generates a grounded response using the configured LLM.
    """
    try:
        result = await chat_service.ask_question(
            db=db,
            query=request.query,
            limit=request.limit,
            min_score=request.min_score
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Chat generation failed: {str(e)}"
        )
