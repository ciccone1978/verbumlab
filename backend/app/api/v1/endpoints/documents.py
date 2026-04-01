from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.document import (
    process_document_ingestion, 
    search_document_chunks_fts,
    search_document_chunks_hybrid,
    search_document_chunks_vector
)
from app.schemas.document import DocumentRead
from app.schemas.search import SearchResponse
import json

router = APIRouter()

@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    metadata: str = Form("{}"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF document and trigger the ingestion pipeline.
    
    The pipeline includes storage in MinIO and text/vector processing.

    Args:
        file (UploadFile): The PDF file to upload.
        title (str): Title of the document.
        metadata (str, optional): JSON string of additional metadata. Defaults to "{}".
        db (AsyncSession): Database session dependency.

    Returns:
        DocumentRead: The processed document metadata.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        metadata_dict = json.loads(metadata)
        content = await file.read()
        
        document = await process_document_ingestion(
            db=db,
            file_content=content,
            filename=file.filename,
            title=title,
            metadata=metadata_dict
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/search-fts", response_model=SearchResponse)
async def search_fts(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint for Full-Text Search on document chunks.
    """
    try:
        results = await search_document_chunks_fts(db, q, limit)
        return {
            "query": q,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search-hybrid", response_model=SearchResponse)
async def search_hybrid(
    q: str,
    limit: int = 10,
    min_score: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint for Hybrid Search (Vector 60% + FTS 40%).
    """
    try:
        results = await search_document_chunks_hybrid(db, q, limit, min_score)
        return {
            "query": q,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

@router.get("/search-vector", response_model=SearchResponse)
async def search_vector(
    q: str,
    limit: int = 10,
    min_score: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint for Semantic Vector Search.
    """
    try:
        results = await search_document_chunks_vector(db, q, limit, min_score)
        return {
            "query": q,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
