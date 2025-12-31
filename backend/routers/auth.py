from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from models import User
from schemas import Token, UserResponse, RefreshTokenRequest
from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
    get_user_by_username
)
from config import settings
from rate_limiter import limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Registration endpoint removed - admin user is created automatically during setup


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token and refresh token"""
    from datetime import datetime
    from auth import create_refresh_token
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(data={"sub": user.username})
    refresh_token_expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    # Store refresh token in database
    user.refresh_token = refresh_token
    user.refresh_token_expires = refresh_token_expires
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    from datetime import datetime
    from auth import verify_refresh_token, create_refresh_token
    
    refresh_token = token_data.refresh_token
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Get user and verify refresh token matches
    user = get_user_by_username(db, username=username)
    if not user or user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Check if refresh token is expired
    if user.refresh_token_expires and user.refresh_token_expires < datetime.utcnow():
        # Clear expired token
        user.refresh_token = None
        user.refresh_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Optionally rotate refresh token (create new one)
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    new_refresh_token_expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    # Update refresh token in database
    user.refresh_token = new_refresh_token
    user.refresh_token_expires = new_refresh_token_expires
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout and invalidate refresh token"""
    current_user.refresh_token = None
    current_user.refresh_token_expires = None
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.put("/change-password")
@limiter.limit("10/hour")
async def change_password(
    request: Request,
    password_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    from auth import verify_password, get_password_hash
    
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password and new password are required"
        )
    
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Validate new password length
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.put("/me")
@limiter.limit("20/minute")
async def update_me(
    request: Request,
    user_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's information (email, username)"""
    # Check if username is being changed and if it already exists
    if "username" in user_data and user_data["username"] != current_user.username:
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        current_user.username = user_data["username"]
    
    # Check if email is being changed and if it already exists
    if "email" in user_data and user_data["email"] != current_user.email:
        existing_email = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        current_user.email = user_data["email"]
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/forgot-password")
@limiter.limit("5/hour")
async def forgot_password(request: Request, email: str, db: Session = Depends(get_db)):
    """Request password reset"""
    from datetime import datetime, timedelta
    import secrets
    from email_notifications import send_password_reset_email
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if user exists for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires
    db.commit()
    
    # Send email with reset link
    email_sent = send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        username=user.username
    )
    
    if email_sent:
        logger.info(f"Password reset email sent to {email}")
    else:
        logger.warning(f"Failed to send password reset email to {email}. Token: {reset_token}")
        # In development, if email is not configured, log the token
        # In production, this should never happen
        if not settings.alert_email_enabled:
            logger.warning("Email is not configured. Password reset token (for development only):")
            logger.warning(f"Token: {reset_token}")
    
    # Always return the same message for security (don't reveal if user exists)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit("10/hour")
async def reset_password(
    request: Request,
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    from datetime import datetime
    
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if user.reset_token_expires < datetime.utcnow():
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Password has been reset successfully"}

