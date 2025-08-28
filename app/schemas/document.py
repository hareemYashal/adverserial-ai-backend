from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base Document schema
class DocumentBase(BaseModel):
    filename: str
    content: Optional[str] = None
    file_type: Optional[str] = None

# Schema for creating a document via text input
class DocumentCreate(DocumentBase):
    project_id: int

# Schema for file upload response
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    unique_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    project_id: int
    is_processed: bool = False
    processing_error: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# Schema for updating a document
class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None
    file_type: Optional[str] = None

# Schema for document response
class DocumentResponse(DocumentBase):
    id: int
    project_id: int
    unique_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    is_processed: bool = False
    processing_error: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# Schema for file processing status
class DocumentProcessingStatus(BaseModel):
    id: int
    filename: str
    is_processed: bool
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    content_preview: Optional[str] = None  # First 200 characters
    
    model_config = {"from_attributes": True}