"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.backend.database import get_db, User, Wardrobe
from app.backend.schemas import UserRegister, UserLogin, TokenResponse
from app.backend.security import hash_password, verify_password, create_access_token
from app.backend.session_manager import get_session_manager

router = APIRouter(prefix="/auth", tags=["authentication"])
session_manager = get_session_manager()


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and return authentication token."""
    
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    db.add(user)
    db.flush()  # Flush to get user.id without committing
    
    # Auto-create wardrobe for user
    wardrobe = Wardrobe(user_id=user.id)
    db.add(wardrobe)
    db.commit()
    db.refresh(user)
    db.refresh(wardrobe)
    
    # Generate token
    token = create_access_token(user.id, user.username)
    
    # Create persistent session
    session_manager.login(user.username, {
        "user_id": user.id,
        "token": token,
        "wardrobe_id": wardrobe.id
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        wardrobe_id=wardrobe.id
    )


@router.get("/health")
def auth_health_check():
    """Health check endpoint for auth service."""
    return {"status": "ok", "service": "auth"}


@router.post("/logout")
def logout(authorization: str = Header(None)):
    """Logout user and destroy session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Extract token to get username
        from jose import jwt
        from app.backend.security import SECRET_KEY, ALGORITHM
        
        token = authorization.replace("Bearer ", "", 1)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Logout from session manager
        session_manager.logout(username)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return authentication token."""
    
    # Find user
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Ensure user has a wardrobe (fallback in case it wasn't created)
    wardrobe = db.query(Wardrobe).filter(Wardrobe.user_id == user.id).first()
    if not wardrobe:
        wardrobe = Wardrobe(user_id=user.id)
        db.add(wardrobe)
        db.commit()
        db.refresh(wardrobe)
    
    # Generate token
    token = create_access_token(user.id, user.username)
    
    # Create persistent session (auto-logs out previous user if any)
    session_manager.login(user.username, {
        "user_id": user.id,
        "token": token,
        "wardrobe_id": wardrobe.id
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        wardrobe_id=wardrobe.id
    )


@router.get("/session/check", response_model=TokenResponse)
def check_session():
    """Check if there's an active session and return its data."""
    active_sessions = session_manager.get_all_active_sessions()
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    # Get the single logged-in user's session
    username, session = list(active_sessions.items())[0]
    session_data = session.get("data", {})
    
    return TokenResponse(
        access_token=session_data.get("token"),
        token_type="bearer",
        user_id=session_data.get("user_id"),
        username=username,
        wardrobe_id=session_data.get("wardrobe_id")
    )
