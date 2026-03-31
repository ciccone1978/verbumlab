"""update vector dimension

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-27 11:44:02.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop existing HNSW index
    op.drop_index('idx_chunks_embedding', table_name='document_chunks', postgresql_using='hnsw')
    
    # 2. Alter column type to 1024 dimensions
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024);")
    
    # 3. Re-create HNSW index
    op.create_index(
        'idx_chunks_embedding', 
        'document_chunks', 
        ['embedding'], 
        unique=False, 
        postgresql_using='hnsw', 
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )


def downgrade():
    # 1. Drop 1024-dim index
    op.drop_index('idx_chunks_embedding', table_name='document_chunks', postgresql_using='hnsw')
    
    # 2. Revert to 1536 dimensions
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536);")
    
    # 3. Re-create index
    op.create_index(
        'idx_chunks_embedding', 
        'document_chunks', 
        ['embedding'], 
        unique=False, 
        postgresql_using='hnsw', 
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )
