"""
Authentication router for user registration, login, and token management.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, ForgetPassword, ForgotPasswordRequest, ResetPassword
from app.services.email_service import email_service
import secrets
import random
import uuid
from datetime import datetime, timedelta
from app.services.auth_service import auth_service, get_current_active_user
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username for the user
    - **email**: Unique email address for the user  
    - **password**: User's password (will be hashed)
    
    Returns the created user information (without password).
    """
    # Check if username already exists
    existing_user = auth_service.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = auth_service.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = auth_service.get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT access token for authenticated requests.
    """
    user = auth_service.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh the access token for current user.
    
    Requires valid JWT token in Authorization header.
    Returns a new JWT access token.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """
    Logout current user.
    
    Note: Since JWT tokens are stateless, this endpoint mainly serves 
    as a confirmation. The client should discard the token.
    """
    return {"message": f"User {current_user.username} logged out successfully"}

@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify if the provided token is valid and not expired.
    
    Returns user information if token is valid.
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_active": current_user.is_active
        }
    }

# In-memory storage for reset tokens (use Redis in production)
reset_tokens = {}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Send password reset email to user.
    
    - **email**: User's email address
    """
    # Find user by email
    user = auth_service.get_user_by_email(db, request.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If email exists, password reset instructions have been sent"}
    
    # Generate 4-digit OTP
    reset_token = str(random.randint(1000, 9999))
    
    # Store OTP with user email and expiration (15 minutes)
    reset_tokens[reset_token] = {
        "email": request.email,
        "user_id": user.id,
        "expires_at": datetime.utcnow() + timedelta(minutes=15)
    }
    
    # Send email
    email_sent = email_service.send_password_reset_email(
        to_email=request.email,
        username=user.username,
        reset_token=reset_token
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email"
        )
    
    return {"message": "Password reset instructions have been sent to your email"}

@router.post("/reset-password")
async def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """
    Reset password using OTP only.
    
    - **otp**: 4-digit OTP from email
    - **new_password**: New password to set
    """
    # Validate OTP
    if request.otp not in reset_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    token_data = reset_tokens[request.otp]
    
    # Check if OTP expired
    if datetime.utcnow() > token_data["expires_at"]:
        del reset_tokens[request.otp]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
    
    # Find user by stored email
    user = auth_service.get_user_by_email(db, token_data["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    new_hashed_password = auth_service.get_password_hash(request.new_password)
    user.hashed_password = new_hashed_password
    
    db.commit()
    db.refresh(user)
    
    # Remove used OTP
    del reset_tokens[request.otp]
    
    return {"message": "Password has been reset successfully"}

@router.post("/forget-password")
async def forget_password(forget_data: ForgetPassword, db: Session = Depends(get_db)):
    """
    Change password by verifying username and old password.
    
    - **username**: User's username
    - **old_password**: Current password for verification
    - **new_password**: New password to set
    """
    # Get user by username
    user = auth_service.get_user_by_username(db, forget_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not auth_service.verify_password(forget_data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )
    
    # Update password
    new_hashed_password = auth_service.get_password_hash(forget_data.new_password)
    user.hashed_password = new_hashed_password
    
    db.commit()
    db.refresh(user)
    
    return {"message": "Password updated successfully"}
