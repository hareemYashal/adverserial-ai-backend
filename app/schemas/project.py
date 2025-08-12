from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Base Project schema
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

# Schema for creating a project
class ProjectCreate(ProjectBase):
    pass

# Schema for updating a project
class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# Schema for project response
class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

# Schema for project with documents
class ProjectWithDocuments(ProjectResponse):
    documents: List = []
    
    model_config = {"from_attributes": True}