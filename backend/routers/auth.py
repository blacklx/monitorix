from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from models import User
from schemas import Token, UserResponse
from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user
)
from config import settings
from rate_limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Registration endpoint removed - admin user is created automatically during setup


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
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

