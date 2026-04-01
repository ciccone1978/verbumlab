from pydantic import BaseModel, Field
from typing import List, Any, Optional

class ChatRequest(BaseModel):
    query: str = Field(..., example="Quali sono le radici bibliche della povertà?")
    limit: int = Field(default=5, ge=1, le=10)
    min_score: float = Field(default=0.65, ge=0.0, le=1.0)

class ChatContextChunk(BaseModel):
    content: str
    document_title: str
    page_number: Optional[int]
    score: float

class ChatResponse(BaseModel):
    answer: str
    context_used: List[ChatContextChunk]
    model: str
