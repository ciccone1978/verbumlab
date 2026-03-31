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
    
    # 4. Extract Text and Chunk (Simple Page-based chunking for now)
    try:
        pdf = PdfReader(BytesIO(file_content))
        chunks = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
                
            # For each page, generate embeddings with 'passage: ' prefix for E5 models
            vector = await embedding_service.get_embeddings(text, prefix="passage: ")
            
            db_chunk = DocumentChunk(
                document_id=doc_id,
                content=text,
                page_number=i + 1,
                chunk_index=i,
                embedding=vector
            )
            db.add(db_chunk)
            
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
