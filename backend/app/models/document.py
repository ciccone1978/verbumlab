import uuid
from sqlalchemy import Column, String, BigInteger, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base_class import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.text("gen_random_uuid()"))
    title = Column(Text, nullable=False)
    filename = Column(Text, nullable=False)
    s3_key = Column(Text, nullable=False, unique=True)
    mimetype = Column(Text, server_default="application/pdf")
    file_size_bytes = Column(BigInteger)
    meta = Column("metadata", JSONB, server_default=func.text("'{}'::jsonb"))
    status = Column(Text, server_default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
