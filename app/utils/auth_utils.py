"""Authentication utilities for route handlers."""
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.backend.database import User, get_db
from app.backend.security import verify_token
from app.backend.session_manager import get_session_manager


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """
    Extract and verify current user from JWT token, and validate session is active.
    
    Args:
        authorization: Bearer token from Authorization header
        db: SQLAlchemy database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If authorization is invalid, session expired, or user not found
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database session not provided")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Validate session is still active
    session_manager = get_session_manager()
    if not session_manager.is_logged_in(token_data.username):
        raise HTTPException(status_code=401, detail="Session expired or user not logged in")
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
