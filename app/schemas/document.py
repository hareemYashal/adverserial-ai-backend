from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base Document schema
class DocumentBase(BaseModel):
    filename: str
    content: Optional[str] = None
    file_type: Optional[str] = None

# Schema for creating a document
class DocumentCreate(DocumentBase):
    project_id: int

# Schema for updating a document
class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None
    file_type: Optional[str] = None

# Schema for document response
class DocumentResponse(DocumentBase):
    id: int
    project_id: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True