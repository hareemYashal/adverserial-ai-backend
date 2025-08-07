from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Base User schema
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Schema for creating a user
class UserCreate(UserBase):
    password: str

# Schema for user login
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for updating user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

# Schema for user response (without password)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schema for user with projects
class UserWithProjects(UserResponse):
    projects: List["ProjectResponse"] = []
    
    class Config:
        from_attributes = True

# For token response
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None