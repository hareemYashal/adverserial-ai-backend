from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

# Base Persona schema
class PersonaBase(BaseModel):
    name: str
    description: Optional[str] = None
    personality_traits: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

# Schema for creating a persona
class PersonaCreate(PersonaBase):
    pass

# Schema for updating a persona
class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality_traits: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for persona response
class PersonaResponse(PersonaBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True