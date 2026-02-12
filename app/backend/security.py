"""JWT authentication and password hashing."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
import bcrypt
import os

# Get SECRET_KEY from environment, fallback to default for development
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
if SECRET_KEY == "your-secret-key-change-this-in-production":
    import warnings
    warnings.warn("⚠️  Using default SECRET_KEY! Set SECRET_KEY environment variable in production", stacklevel=2)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 720  # 30 days


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: int
    username: str


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Truncates to 72 bytes (bcrypt limit)."""
    # Bcrypt has a 72-byte limit for passwords
    password_bytes = password.encode('utf-8')[:72]
    password = password_bytes.decode('utf-8', errors='ignore')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(user_id: int, username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = {
        "user_id": user_id,
        "username": username,
    }
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token."""
    import logging
    logger = logging.getLogger("fashion_wardrobe_app")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        
        if user_id is None or username is None:
            logger.warning("Invalid token: missing user_id or username")
            return None
        
        return TokenData(user_id=user_id, username=username)
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None
