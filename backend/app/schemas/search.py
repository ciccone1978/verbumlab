from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class SearchResult(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    page_number: Optional[int]
    chunk_index: Optional[int]
    score: float
    created_at: datetime

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
