import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, func, Computed
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector
from app.db.base_class import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.text("gen_random_uuid()"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    
    # Vector Search (e.g., multilingual-e5-large uses 1024 dims)
    embedding = Column(Vector(1024))
    
    # Full Text Search (Generated Column)
    # Note: 'italian' language specified as per requirement
    fts_tokens = Column(
        TSVECTOR, 
        Computed("to_tsvector('italian', content)", persisted=True)
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
