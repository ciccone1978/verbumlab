import uuid
from sqlalchemy import Column, String, DateTime, func, Text, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base_class import Base

class ChatMessage(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.text("gen_random_uuid()"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Text, nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    query_standalone = Column(Text)
    sources = Column(JSONB, server_default=func.text("'[]'::jsonb"))
    model_name = Column(Text)
    tokens_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # role CHECK constraint can be added in __table_args__
    __table_args__ = (
        Index('idx_messages_conversation', "conversation_id", "created_at"),
    )
