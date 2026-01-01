from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User
from config import settings

# Initialize CryptContext with error handling for bcrypt initialization issues
# Some bcrypt versions have issues with passlib's wrap bug detection
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Force initialization by attempting to hash a short test password
    # This will trigger any initialization errors early
    _test_hash = pwd_context.hash("test123")
except Exception as e:
    # If passlib fails during initialization, use bcrypt directly
    import bcrypt
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Passlib initialization failed ({e}), using bcrypt directly")
    
    class DirectBcryptContext:
        """Direct bcrypt wrapper when passlib fails"""
        @staticmethod
        def hash(password: str) -> str:
            # Ensure password is bytes and not too long (bcrypt limit: 72 bytes)
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        
        @staticmethod
        def verify(plain_password: str, hashed_password: str) -> bool:
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    pwd_context = DirectBcryptContext()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Try with current pwd_context first
        result = pwd_context.verify(plain_password, hashed_password)
        if result:
            return True
        
        # If verification failed and we're using DirectBcryptContext,
        # the hash might have been created with passlib. Try passlib directly.
        if hasattr(pwd_context, '__class__') and 'DirectBcryptContext' in str(pwd_context.__class__):
            try:
                from passlib.context import CryptContext
                passlib_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                result = passlib_context.verify(plain_password, hashed_password)
                if result:
                    logger.info("Password verified using passlib (hash was created with passlib)")
                    return True
            except Exception as passlib_error:
                logger.debug(f"Passlib verification also failed: {passlib_error}")
        
        return False
    except Exception as e:
        logger.error(f"Error in verify_password: {e}")
        # Try alternative verification methods
        try:
            import bcrypt
            # Try direct bcrypt verification
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            result = bcrypt.checkpw(password_bytes, hashed_bytes)
            if result:
                logger.info("Password verified using direct bcrypt")
                return True
        except Exception as bcrypt_error:
            logger.error(f"Direct bcrypt verification also failed: {bcrypt_error}")
        
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Ensure password is not too long for bcrypt (72 bytes max)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    import secrets
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    # Add random jti (JWT ID) for additional security
    to_encode.update({"jti": secrets.token_urlsafe(32)})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify refresh token and return payload"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = get_user_by_username(db, username)
    if not user:
        logger.warning(f"User '{username}' not found")
        return None
    
    # Verify password
    try:
        password_valid = verify_password(password, user.hashed_password)
        if not password_valid:
            logger.warning(f"Password verification failed for user '{username}'")
            return None
        logger.debug(f"Password verified successfully for user '{username}'")
    except Exception as e:
        logger.error(f"Error verifying password for user '{username}': {e}")
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

