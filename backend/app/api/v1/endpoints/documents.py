from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from services.document import process_document_ingestion
from schemas.document import DocumentRead
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
