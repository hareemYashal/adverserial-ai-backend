from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, Union, List

# Base Persona schema
class PersonaBase(BaseModel):
    name: str
    description: Optional[str] = None
    personality_traits: Optional[Union[Dict[str, Any], List[str]]] = None
    system_prompt: Optional[str] = None

# Schema for creating a persona
class PersonaCreate(PersonaBase):
    pass

# Schema for updating a persona
class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality_traits: Optional[Union[Dict[str, Any], List[str]]] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for persona response
class PersonaResponse(PersonaBase):
    id: int
    user_id: Optional[int] = None
    is_default: bool = False
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}