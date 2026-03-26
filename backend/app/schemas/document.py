from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class DocumentBase(BaseModel):
    title: str
    metadata: Optional[Dict[str, Any]] = {}

class DocumentCreate(DocumentBase):
    filename: str

class DocumentRead(DocumentBase):
    id: UUID
    filename: str
    s3_key: str
    mimetype: str
    file_size_bytes: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
