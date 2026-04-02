from pydantic import BaseModel, Field
from typing import List, Any, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., example="user", description="Role of the message author: 'user' or 'assistant'")
    content: str = Field(..., example="Chi era San Francesco?", description="Text content of the message")

class ChatRequest(BaseModel):
    query: str = Field(..., example="Quali sono le radici bibliche della povertà?")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
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
