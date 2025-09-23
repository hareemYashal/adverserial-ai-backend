"""
File upload router for handling document uploads with text extraction.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.document import DocumentUploadResponse, DocumentProcessingStatus
from app.services.file_service import file_service

router = APIRouter(
    prefix="/upload",
    tags=["file-upload"],
    responses={404: {"description": "Not found"}},
)

async def process_document_text(document_id: int, db: Session):
    """Background task to extract text from uploaded document."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document or not document.file_path:
            return
        
        # Extract text content asynchronously
        import asyncio
        extracted_text = await asyncio.to_thread(
            file_service.extract_text, document.file_path, document.file_type
        )
        
        # Update document with extracted text
        document.content = extracted_text
        document.is_processed = True
        document.processed_at = datetime.now(timezone.utc)
        document.processing_error = None
        
        db.commit()
        
    except Exception as e:
        # Update document with error status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.is_processed = False
            document.processing_error = str(e)
            document.processed_at = datetime.now(timezone.utc)
            db.commit()

@router.post("/document", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document file and extract text content.
    
    - **project_id**: ID of the project to associate the document with
    - **file**: The document file to upload (PDF, DOCX, TXT, etc.)
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    try:
        # Save file using file service
        file_metadata = await file_service.save_file(file, project_id)
        
        # Create document record
        document = Document(
            filename=file_metadata['filename'],
            unique_filename=file_metadata['unique_filename'],
            file_path=file_metadata['file_path'],
            file_type=file_metadata['file_type'],
            file_size=file_metadata['file_size'],
            project_id=project_id,
            is_processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Add background task for text extraction
        background_tasks.add_task(process_document_text, document.id, db)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.post("/documents/batch", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    project_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple document files at once.
    
    - **project_id**: ID of the project to associate the documents with
    - **files**: List of document files to upload
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files can be uploaded at once"
        )
    
    uploaded_documents = []
    
    for file in files:
        try:
            # Save file using file service
            file_metadata = await file_service.save_file(file, project_id)
            
            # Create document record
            document = Document(
                filename=file_metadata['filename'],
                unique_filename=file_metadata['unique_filename'],
                file_path=file_metadata['file_path'],
                file_type=file_metadata['file_type'],
                file_size=file_metadata['file_size'],
                project_id=project_id,
                is_processed=False
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Add background task for text extraction
            background_tasks.add_task(process_document_text, document.id, db)
            
            uploaded_documents.append(document)
            
        except Exception as e:
            # Continue with other files if one fails
            continue
    
    if not uploaded_documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were successfully uploaded"
        )
    
    return uploaded_documents

@router.get("/document/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_document_processing_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the processing status of an uploaded document.
    
    - **document_id**: ID of the document to check status for
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Create content preview if available
    content_preview = None
    if document.content:
        content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
    
    return DocumentProcessingStatus(
        id=document.id,
        filename=document.filename,
        is_processed=document.is_processed,
        processing_error=document.processing_error,
        processed_at=document.processed_at,
        content_preview=content_preview
    )

@router.post("/document/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reprocess a document to extract text content again.
    
    - **document_id**: ID of the document to reprocess
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    if not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no associated file to process"
        )
    
    # Reset processing status
    document.is_processed = False
    document.processing_error = None
    document.processed_at = None
    db.commit()
    
    # Add background task for text extraction
    background_tasks.add_task(process_document_text, document.id, db)
    
    return {"message": "Document reprocessing started", "document_id": document_id}

@router.get("/supported-types")
async def get_supported_file_types():
    """Get list of supported file types for upload."""
    return {
        "supported_types": list(file_service.supported_types.keys()),
        "max_file_size": file_service.max_file_size,
        "max_file_size_mb": file_service.max_file_size / (1024 * 1024)
    }

@router.get("/project/{project_id}/processing-status")
async def get_project_processing_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get processing status summary for all documents in a project.
    
    - **project_id**: ID of the project
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Get document statistics
    total_docs = db.query(Document).filter(Document.project_id == project_id).count()
    processed_docs = db.query(Document).filter(
        Document.project_id == project_id,
        Document.is_processed == True
    ).count()
    error_docs = db.query(Document).filter(
        Document.project_id == project_id,
        Document.processing_error.isnot(None)
    ).count()
    
    return {
        "project_id": project_id,
        "total_documents": total_docs,
        "processed_documents": processed_docs,
        "error_documents": error_docs,
        "processing_complete": total_docs == processed_docs,
        "processing_percentage": (processed_docs / total_docs * 100) if total_docs > 0 else 0
    }
