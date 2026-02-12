# Developer Guide - Authentication

User authentication, authorization, and security implementation.

## Authentication Architecture

### JWT (JSON Web Token) Implementation

**Token Flow:**
```
1. User Login
   ↓
2. Credentials Verified
   ├─ Username lookup
   └─ Password hash comparison
   ↓
3. JWT Generated
   ├─ Header: Algorithm (HS256)
   ├─ Payload: User ID, username, expiration
   └─ Signature: HMAC-SHA256
   ↓
4. Token Returned to Client
   ↓
5. Client Stores Token
   └─ In memory, HttpOnly cookie, or secure storage
   ↓
6. Client Sends Token in Headers
   └─ Authorization: Bearer {token}
   ↓
7. Server Validates Token
   ├─ Signature verification
   ├─ Expiration check
   └─ User lookup
   ↓
8. Request Processed
```

### JWT Token Structure

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZXhwIjoxNzA0MTA2NDAwLCJpYXQiOjE3MDQwMjAwMDB9.
signature

┌────────────────────────────────────────────────────┐
│ HEADER                                             │
├────────────────────────────────────────────────────┤
│ {                                                  │
│   "alg": "HS256",                                  │
│   "typ": "JWT"                                     │
│ }                                                  │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│ PAYLOAD                                            │
├────────────────────────────────────────────────────┤
│ {                                                  │
│   "sub": "550e8400-e29b-41d4-a716-446655440000",  │
│   "username": "john_doe",                          │
│   "exp": 1704106400,  (expiration timestamp)       │
│   "iat": 1704020000,  (issued at timestamp)        │
│   "type": "access"                                 │
│ }                                                  │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│ SIGNATURE                                          │
├────────────────────────────────────────────────────┤
│ HMACSHA256(                                        │
│   base64(header) + "." + base64(payload),          │
│   secret_key                                       │
│ )                                                  │
└────────────────────────────────────────────────────┘
```

---

## Implementation

### Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import os

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme for Swagger docs
security = HTTPBearer()
```

### Password Hashing

```python
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

# Example usage
hashed = hash_password("SecurePass123!")
is_valid = verify_password("SecurePass123!", hashed)  # True
is_valid = verify_password("WrongPass", hashed)      # False
```

### Token Creation

```python
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt

# Example usage
token = create_access_token(
    data={"sub": str(user.id), "username": user.username}
)
```

### Token Verification

```python
def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return payload
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )
```

### Dependency for Current User

```python
async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that:
    1. Extracts token from header
    2. Validates token
    3. Retrieves user from database
    4. Returns user or raises exception
    """
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
```

### Login Endpoint

```python
@router.post("/auth/login")
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token
    """
    
    # Find user by username
    user = db.query(User).filter(
        User.username == credentials.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    }
```

### Registration Endpoint

```python
@router.post("/auth/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new user
    """
    
    # Check username uniqueness
    existing = db.query(User).filter(
        User.username == request.username
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate password
    if not is_strong_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements"
        )
    
    # Create user
    user = User(
        username=request.username,
        password_hash=hash_password(request.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at
    }
```

---

## Password Security

### Requirements

```python
import re

def is_strong_password(password: str) -> bool:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    
    if len(password) < 8:
        return False
    
    if not re.search(r"[A-Z]", password):
        return False
    
    if not re.search(r"[a-z]", password):
        return False
    
    if not re.search(r"\d", password):
        return False
    
    return True

# Test passwords
is_strong_password("weak")              # False
is_strong_password("NoDigits!")         # False
is_strong_password("noupppercase1")     # False
is_strong_password("MyPassword123!")    # True
```

### Password Hashing Details

```python
from passlib.context import CryptContext

# Configure bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Iteration count (higher = more secure but slower)
)

# Hashing is CPU-intensive
# ~0.3 seconds per hash with rounds=12
# This is intentional to prevent brute-force attacks

# Example timing
import time
start = time.time()
hash1 = pwd_context.hash("MyPassword123!")
elapsed = time.time() - start
print(f"Hashing took {elapsed:.2f} seconds")  # ~0.3s
```

---

## Protected Routes

### Using Current User Dependency

```python
@router.get("/wardrobes")
async def get_wardrobes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all wardrobes for authenticated user
    
    Security:
    - Requires valid JWT token
    - User identity verified
    - User can only access their data
    """
    
    wardrobes = db.query(Wardrobe).filter(
        Wardrobe.user_id == current_user.id
    ).all()
    
    return wardrobes
```

### Authorization Checks

```python
@router.get("/wardrobes/{wardrobe_id}")
async def get_wardrobe(
    wardrobe_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific wardrobe with ownership check
    """
    
    wardrobe = db.query(Wardrobe).filter(
        Wardrobe.id == wardrobe_id
    ).first()
    
    if not wardrobe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wardrobe not found"
        )
    
    # Authorization check
    if wardrobe.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    
    return wardrobe
```

---

## Session Management

### Creating Sessions

```python
async def create_session(
    user_id: UUID,
    username: str,
    access_token: str
):
    """Save session to file"""
    
    session_data = {
        "user_id": str(user_id),
        "username": username,
        "access_token": access_token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    
    session_path = SESSIONS_PATH / f"{username}.json"
    
    with open(session_path, "w") as f:
        json.dump(session_data, f, indent=2)
```

### Validating Sessions

```python
async def validate_session(token: str) -> dict:
    """Validate token and return session data"""
    
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            return None  # Token expired
        
        return payload
    
    except JWTError:
        return None  # Invalid token
```

### Logout

```python
@router.post("/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (client-side token deletion)
    """
    
    # Remove session file
    session_path = SESSIONS_PATH / f"{current_user.username}.json"
    session_path.unlink(missing_ok=True)
    
    return {"message": "Logged out successfully"}
```

---

## Security Best Practices

### Do's ✅

```python
# ✅ Hash passwords with bcrypt
user.password_hash = hash_password(password)

# ✅ Validate token expiration
if payload.get("exp") < datetime.utcnow():
    raise HTTPException(status_code=401)

# ✅ Check user ownership of resources
if resource.user_id != current_user.id:
    raise HTTPException(status_code=403)

# ✅ Use HTTPS in production
# Configuration in app setup

# ✅ Validate input data with Pydantic
class LoginRequest(BaseModel):
    username: str
    password: str

# ✅ Return generic error messages
raise HTTPException(detail="Invalid credentials")  # Don't say "user not found"

# ✅ Log security events
logger.warning(f"Failed login attempt for username: {username}")
```

### Don'ts ❌

```python
# ❌ Never store plain text passwords
user.password = password  # WRONG!

# ❌ Never expose sensitive data
return {"detail": "User john_doe not found"}  # WRONG! (reveals usernames)

# ❌ Don't trust client claims without verification
user_id = request.user_id  # WRONG! Use token

# ❌ Don't send passwords over HTTP
# Always use HTTPS

# ❌ Don't hardcode secret keys
SECRET_KEY = "my-secret-key"  # WRONG!
# Use environment variables

# ❌ Don't log passwords or tokens
logger.info(f"User password: {password}")  # WRONG!
logger.info(f"Token: {token}")  # WRONG!
```

---

## Token Expiration & Refresh

### Current Implementation

**Token Duration:** 24 hours
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
```

### Refresh Token (Future)

**Planned Implementation:**
```python
# Create both access and refresh tokens
def create_tokens(user_id: UUID):
    access_token = create_access_token(
        {"sub": str(user_id)},
        expires_delta=timedelta(minutes=15)  # Short-lived
    )
    
    refresh_token = create_access_token(
        {"sub": str(user_id), "type": "refresh"},
        expires_delta=timedelta(days=7)  # Long-lived
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Refresh endpoint
@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    # Validate refresh token
    # Generate new access token
    # Return new token
    pass
```

---

## Error Handling

### Authentication Errors

```python
# Unauthorized (401)
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

# Forbidden (403)
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions"
)

# Bad Request (400)
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid input"
)

# Not Found (404)
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)
```

---

## Security Testing

### Unit Tests

```python
def test_password_hashing():
    """Test password hashing"""
    password = "MyPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_strong_password():
    """Test password strength validation"""
    assert not is_strong_password("weak")
    assert not is_strong_password("NoDigits!")
    assert is_strong_password("MyPassword123!")

def test_token_creation():
    """Test JWT creation and validation"""
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    token = create_access_token({"sub": str(user_id)})
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user_id)

def test_token_expiration():
    """Test token expiration"""
    expires_delta = timedelta(seconds=-1)  # Already expired
    token = create_access_token({"sub": "user_id"}, expires_delta)
    
    with pytest.raises(HTTPException):
        verify_token(token)
```

---

## Next Steps

- Learn about [Machine Learning](machine-learning.md)
- Explore [Testing](testing.md)
- Read [Code Style](code-style.md)
