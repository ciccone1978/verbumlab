import uuid
from typing import List
from io import BytesIO
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.s3 import s3_service
from app.services.embeddings import embedding_service
import logging

logger = logging.getLogger(__name__)

async def search_document_chunks_vector(
    db: AsyncSession,
    query: str,
    limit: int = 10
) -> List[dict]:
    """
    Perform a Semantic Vector Search on document chunks.

    Args:
        db (AsyncSession): Database session.
        query (str): The search query string.
        limit (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        List[dict]: A list of semantically similar chunks with their similarity scores.
    """
    # 1. Generate Query Vector (mxbai search instruction)
    query_vector = await embedding_service.get_embeddings(
        query, 
        prefix="Represent this sentence for searching relevant passages: "
    )
    
    # 2. Perform Vector Search Query
    # 1 - (embedding <=> :query_vec) converts cosine distance to similarity score (0 to 1)
    sql_query = text(
        """
        SELECT 
            id, document_id, content, page_number, chunk_index, created_at,
            (1 - (embedding <=> CAST(:query_vec AS vector))) as score
        FROM document_chunks
        ORDER BY embedding <=> CAST(:query_vec AS vector)
        LIMIT :limit
        """
    )
    
    result = await db.execute(sql_query, {"query_vec": str(query_vector), "limit": limit})
    rows = result.mappings().all()
    return rows

async def search_document_chunks_hybrid(
    db: AsyncSession,
    query: str,
    limit: int = 10
) -> List[dict]:
    """
    Perform a Hybrid Search combining Vector Search and Full-Text Search.
    Weighting: 60% Vector, 40% FTS.

    Args:
        db (AsyncSession): Database session.
        query (str): The search query string.
        limit (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        List[dict]: A list of matching chunks with their combined relevance scores.
    """
    # 1. Generate Query Vector (mxbai search instruction)
    query_vector = await embedding_service.get_embeddings(
        query, 
        prefix="Represent this sentence for searching relevant passages: "
    )
    
    # 2. Perform Hybrid Search Query
    # We use a CTE approach to calculate both scores and then combine them.
    # Note: Vector similarity is (1 - distance). FTS rank is normalized.
    sql_query = text(
        """
        WITH vector_results AS (
            SELECT 
                id, 
                1 - (embedding <=> CAST(:query_vec AS vector)) as vec_score
            FROM document_chunks
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit * 4
        ),
        text_results AS (
            SELECT 
                id, 
                ts_rank_cd(fts_tokens, to_tsquery('italian', :query_text)) as fts_score
            FROM document_chunks
            WHERE fts_tokens @@ to_tsquery('italian', :query_text)
            LIMIT :limit * 4
        )
        SELECT 
            c.id, c.document_id, c.content, c.page_number, c.chunk_index, c.created_at,
            (COALESCE(v.vec_score, 0) * 0.6) + (COALESCE(t.fts_score, 0) * 0.4) as score,
            v.vec_score,
            t.fts_score
        FROM document_chunks c
        LEFT JOIN vector_results v ON c.id = v.id
        LEFT JOIN text_results t ON c.id = t.id
        WHERE v.id IS NOT NULL OR t.id IS NOT NULL
        ORDER BY score DESC
        LIMIT :limit
        """
    )
    
    # Convert query to boolean & for better FTS matches
    fts_query = query.replace(" ", " & ")
    
    result = await db.execute(
        sql_query, 
        {
            "query_vec": str(query_vector), 
            "query_text": fts_query, 
            "limit": limit
        }
    )
    rows = result.mappings().all()
    return rows

async def search_document_chunks_fts(
    db: AsyncSession,
    query: str,
    limit: int = 10
) -> List[dict]:
    """
    Perform a Full-Text Search (FTS) on document chunks using PostgreSQL TSVECTOR.

    Args:
        db (AsyncSession): Database session.
        query (str): The search query string.
        limit (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        List[dict]: A list of matching chunks with their relevance scores.
    """
    from sqlalchemy import select, desc
    
    # We use raw SQL for FTS ranking to get the relevance score
    # ts_rank returns a float representing relevance
    sql_query = text(
        """
        SELECT 
            id, document_id, content, page_number, chunk_index, created_at,
            ts_rank(fts_tokens, to_tsquery('italian', :query)) as score
        FROM document_chunks
        WHERE fts_tokens @@ to_tsquery('italian', :query)
        ORDER BY score DESC
        LIMIT :limit
        """
    )
    
    result = await db.execute(sql_query, {"query": query.replace(" ", " & "), "limit": limit})
    rows = result.mappings().all()
    return rows

async def process_document_ingestion(
    db: AsyncSession,
    file_content: bytes,
    filename: str,
    title: str,
    metadata: dict = {}
):
    """
    Orchestrate the complete document ingestion pipeline.
    
    This includes:
    1. Uploading the raw PDF to S3/MinIO.
    2. Creating a record in the 'documents' table.
    3. Extracting text from PDF pages.
    4. Generating embeddings for each page/chunk.
    5. Storing chunks and vectors in the 'document_chunks' table.

    Args:
        db (AsyncSession): Database session.
        file_content (bytes): Raw binary content of the PDF.
        filename (str): Original filename.
        title (str): Document title.
        metadata (dict, optional): Additional JSON metadata. Defaults to {}.

    Returns:
        Document: The created and processed Document model instance.
    """
    # 1. Generate unique key for S3
    doc_id = uuid.uuid4()
    s3_key = f"documents/{doc_id}/{filename}"
    
    # 2. Upload to MinIO
    await s3_service.upload_file(file_content, s3_key)
    
    # 3. Create Document record
    db_document = Document(
        id=doc_id,
        title=title,
        filename=filename,
        s3_key=s3_key,
        file_size_bytes=len(file_content),
        metadata=metadata,
        status="processing"
    )
    db.add(db_document)
    await db.flush() # Get the ID if needed
    
    # 4. Extract Text and Chunk with Sliding Window
    try:
        pdf = PdfReader(BytesIO(file_content))
        chunk_idx = 0
        
        # Hyperparameters for chunking
        CHUNK_SIZE = 150  # Words (extremely safe for 512-token models)
        CHUNK_OVERLAP = 30 # Words
        
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if not page_text or not page_text.strip():
                continue
            
            # Split page into words for simple but effective chunking
            words = page_text.split()
            
            # If the page is small, treat as a single chunk
            if len(words) <= CHUNK_SIZE:
                page_chunks = [page_text]
            else:
                # Create overlapping chunks
                page_chunks = []
                for start in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
                    end = start + CHUNK_SIZE
                    chunk_words = words[start:end]
                    page_chunks.append(" ".join(chunk_words))
                    if end >= len(words):
                        break
            
            for sub_text in page_chunks:
                # For each chunk, generate embeddings (no prefix for mxbai)
                vector = await embedding_service.get_embeddings(sub_text, prefix="")
                
                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    content=sub_text,
                    page_number=i + 1,
                    chunk_index=chunk_idx,
                    embedding=vector
                )
                db.add(db_chunk)
                chunk_idx += 1
            
        # 5. Finalize
        db_document.status = "completed"
        await db.commit()
        await db.refresh(db_document)
        return db_document
        
    except Exception as e:
        logger.error(f"Failed to process streaks: {e}")
        db_document.status = "error"
        db_document.metadata["error"] = str(e)
        await db.commit()
        raise
