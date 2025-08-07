from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate, UserWithProjects

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}},
)

@router.get("/", response_model=List[UserResponse], summary="Get all users")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all users with pagination support.
    
    - **skip**: Number of users to skip (for pagination)
    - **limit**: Maximum number of users to return
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific user by their ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

@router.get("/{user_id}/with-projects", response_model=UserWithProjects, summary="Get user with projects")
async def get_user_with_projects(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a user with all their associated projects.
    
    - **user_id**: The ID of the user to retrieve
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

@router.get("/by-username/{username}", response_model=UserResponse, summary="Get user by username")
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by their username.
    
    - **username**: The username of the user to retrieve
    """
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found"
        )
    return user

@router.get("/by-email/{email}", response_model=UserResponse, summary="Get user by email")
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by their email address.
    
    - **email**: The email address of the user to retrieve
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create new user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    
    - **user**: User data to create
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (password hashing should be implemented in a service layer)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=user.password  # TODO: Hash password before storing
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing user.
    
    - **user_id**: The ID of the user to update
    - **user_update**: Updated user data
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields if provided
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(db_user, "hashed_password", value)  # TODO: Hash password
        else:
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user.
    
    - **user_id**: The ID of the user to delete
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    db.delete(db_user)
    db.commit()
    return None

@router.get("/active/count", summary="Get count of active users")
async def get_active_users_count(db: Session = Depends(get_db)):
    """
    Get the count of active users.
    """
    count = db.query(User).filter(User.is_active == True).count()
    return {"active_users_count": count} 