from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.document import DocumentResponse, DocumentCreate, DocumentUpdate

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Document not found"}},
)

@router.get("/", response_model=List[DocumentResponse], summary="Get all documents")
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    file_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all documents with optional filtering.
    
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    - **project_id**: Filter documents by project ID (optional)
    - **file_type**: Filter documents by file type (optional)
    """
    query = db.query(Document)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    if file_type:
        query = query.filter(Document.file_type == file_type)
    
    documents = query.offset(skip).limit(limit).all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse, summary="Get document by ID")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific document by its ID.
    
    - **document_id**: The ID of the document to retrieve
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return document

@router.get("/project/{project_id}", response_model=List[DocumentResponse], summary="Get documents by project")
async def get_documents_by_project(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all documents for a specific project.
    
    - **project_id**: The ID of the project whose documents to retrieve
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    documents = db.query(Document).filter(Document.project_id == project_id).offset(skip).limit(limit).all()
    return documents

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Create new document")
async def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a new document.
    
    - **document**: Document data to create
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == document.project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {document.project_id} not found"
        )
    
    db_document = Document(
        filename=document.filename,
        content=document.content,
        file_type=document.file_type,
        project_id=document.project_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.put("/{document_id}", response_model=DocumentResponse, summary="Update document")
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing document.
    
    - **document_id**: The ID of the document to update
    - **document_update**: Updated document data
    """
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Update fields if provided
    update_data = document_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)
    
    db.commit()
    db.refresh(db_document)
    return db_document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete document")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document.
    
    - **document_id**: The ID of the document to delete
    """
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    db.delete(db_document)
    db.commit()
    return None

@router.get("/search/{filename}", response_model=List[DocumentResponse], summary="Search documents by filename")
async def search_documents_by_filename(
    filename: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search documents by filename (case-insensitive partial match).
    
    - **filename**: Filename to search for
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    """
    documents = db.query(Document).filter(
        Document.filename.ilike(f"%{filename}%")
    ).offset(skip).limit(limit).all()
    return documents

@router.get("/by-type/{file_type}", response_model=List[DocumentResponse], summary="Get documents by file type")
async def get_documents_by_type(
    file_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve documents by file type.
    
    - **file_type**: The file type to filter by
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    """
    documents = db.query(Document).filter(Document.file_type == file_type).offset(skip).limit(limit).all()
    return documents

@router.get("/project/{project_id}/count", summary="Get document count for project")
async def get_project_document_count(project_id: int, db: Session = Depends(get_db)):
    """
    Get the count of documents for a specific project.
    
    - **project_id**: The ID of the project
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    count = db.query(Document).filter(Document.project_id == project_id).count()
    return {"project_id": project_id, "document_count": count}

@router.get("/stats/file-types", summary="Get document statistics by file type")
async def get_document_stats_by_type(db: Session = Depends(get_db)):
    """
    Get statistics about documents grouped by file type.
    """
    from sqlalchemy import func
    
    stats = db.query(
        Document.file_type,
        func.count(Document.id).label('count')
    ).group_by(Document.file_type).all()
    
    return [
        {"file_type": stat.file_type, "count": stat.count}
        for stat in stats
    ] 