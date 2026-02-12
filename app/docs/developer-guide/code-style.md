# Developer Guide - Code Style

Code standards, style conventions, and quality guidelines.

## Python Style Standards

### PEP 8 Compliance

The project follows PEP 8 with some exceptions. Use tools to maintain consistency.

**Key PEP 8 Rules:**
- 4 spaces for indentation (not tabs)
- Maximum line length: 88 characters (Black formatter)
- Two blank lines between top-level definitions
- One blank line between method definitions
- Imports at the top of file

### Tools & Configuration

**File:** `.flake8`

```ini
[flake8]
max-line-length = 88
exclude = .git,__pycache__,venv,build,dist
ignore = E203,W503
```

**File:** `pyproject.toml`

```toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_mode = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
```

### Running Code Style Tools

```bash
# Format code (Black)
black app/ tests/

# Sort imports (isort)
isort app/ tests/

# Check style (Flake8)
flake8 app/ tests/

# Type checking (Mypy)
mypy app/

# All checks together
black --check app/
isort --check app/
flake8 app/
```

---

## Import Organization

### Import Order

```python
# 1. Standard library imports
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# 2. Third-party imports
import numpy as np
import torch
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 3. Local application imports
from app.backend.database import Base, get_db
from app.backend.security import create_access_token
from app.models.base import BaseModel
```

### Absolute vs Relative Imports

**Use absolute imports (preferred):**

```python
# Good
from app.backend.database import User
from app.utils.security import hash_password

# Avoid relative imports
from ...backend.database import User  # Confusing
```

### Wildcard Imports (Avoid)

```python
# Don't do this
from app.backend.database import *

# Instead, be explicit
from app.backend.database import User, Wardrobe, Item
```

---

## Type Hints

### Type Annotation Standards

**Always annotate:**
- Function parameters
- Function return types
- Class attributes (when not obvious)

```python
from typing import Optional, List, Dict, Tuple

# Good
def create_user(
    username: str,
    password: str,
    email: Optional[str] = None
) -> User:
    """Create a new user."""
    pass

# Bad
def create_user(username, password, email=None):
    pass
```

### Common Type Patterns

```python
from typing import Optional, List, Dict, Union, Any

# Optional types
def get_user(user_id: Optional[int] = None) -> Optional[User]:
    pass

# Collections
def get_items(ids: List[int]) -> Dict[int, Item]:
    pass

# Multiple types
def process(data: Union[str, bytes]) -> str:
    pass

# Any (use sparingly)
def parse_config(config: Dict[str, Any]) -> None:
    pass

# Generics
from typing import TypeVar, Generic
T = TypeVar('T')
class Repository(Generic[T]):
    def get(self, id: int) -> T:
        pass
```

### Pydantic Model Types

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!",
                "email": "john@example.com"
            }
        }
```

---

## Docstrings

### Docstring Style (Google Format)

```python
def create_wardrobe(
    user_id: int,
    name: str,
    description: Optional[str] = None
) -> Wardrobe:
    """Create a new wardrobe for a user.
    
    Args:
        user_id: The ID of the user who owns the wardrobe
        name: Name of the wardrobe (3-100 characters)
        description: Optional description of the wardrobe
    
    Returns:
        The created Wardrobe object
    
    Raises:
        ValueError: If name is empty or too long
        UserNotFoundError: If user_id doesn't exist
    
    Example:
        >>> wardrobe = create_wardrobe(user_id=1, name="Summer")
        >>> wardrobe.name
        'Summer'
    """
    if not name or len(name) > 100:
        raise ValueError("Name must be 1-100 characters")
    
    # Implementation
    pass
```

### Class Docstrings

```python
class UserRepository:
    """Repository for user database operations.
    
    Handles CRUD operations for User objects with caching
    and query optimization.
    
    Attributes:
        db: SQLAlchemy session
        cache: User cache dictionary
    
    Example:
        >>> repo = UserRepository(db_session)
        >>> user = repo.get_by_username("john")
    """
    
    def __init__(self, db):
        self.db = db
        self.cache = {}
```

### Module Docstrings

```python
"""Authentication and security utilities.

This module provides functions for:
- Password hashing and verification
- JWT token creation and validation
- Security token generation

Example:
    >>> token = create_access_token({"sub": "user123"})
    >>> is_valid = verify_token(token)
"""
```

---

## Error Handling

### Standard Exception Pattern

```python
# Define custom exceptions
class APIException(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(APIException):
    """Resource not found (404)"""
    def __init__(self, message: str):
        super().__init__(message, 404)

class ValidationError(APIException):
    """Invalid request data (400)"""
    def __init__(self, message: str):
        super().__init__(message, 400)

# Using exceptions
def get_user(user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user

# FastAPI error handler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(APIException)
async def api_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
```

### Try-Except Best Practices

```python
# Good: Specific exception handling
try:
    user = get_user(user_id)
except NotFoundError as e:
    logger.warning(f"User not found: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise

# Bad: Catch-all exceptions
try:
    user = get_user(user_id)
except Exception:
    pass  # Never swallow exceptions!
```

---

## Class Organization

### Method Ordering

```python
class User:
    """User model"""
    
    # 1. Class attributes
    DEFAULT_ROLE = "user"
    MAX_USERNAME_LENGTH = 50
    
    # 2. Constructor
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
    
    # 3. Properties
    @property
    def display_name(self) -> str:
        return self.username.replace("_", " ").title()
    
    # 4. Public methods
    def set_password(self, password: str) -> None:
        """Set user password"""
        pass
    
    def verify_password(self, password: str) -> bool:
        """Verify password"""
        pass
    
    # 5. Private methods
    def _validate_email(self) -> bool:
        """Validate email format"""
        pass
    
    # 6. Magic methods
    def __repr__(self) -> str:
        return f"User(username={self.username})"
    
    def __str__(self) -> str:
        return self.username
```

---

## Function Guidelines

### Function Length

Keep functions focused and short:
- Aim for < 20 lines
- One responsibility per function
- Extract complex logic to helper functions

```python
# Good: Small, focused function
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )

# Bad: Too large, multiple responsibilities
def handle_user_login(request, db):
    # Validate input
    # Query database
    # Hash password
    # Create token
    # Log activity
    # Send email
    # Update cache
    # ... too much!
```

### Function Parameters

Limit function parameters (max 4-5):

```python
# Good
def create_item(
    wardrobe_id: int,
    name: str,
    image_path: str,
    category: str
) -> Item:
    pass

# Better: Use data class
from dataclasses import dataclass

@dataclass
class ItemData:
    wardrobe_id: int
    name: str
    image_path: str
    category: str

def create_item(item_data: ItemData) -> Item:
    pass
```

---

## Naming Conventions

### Variable Names

```python
# Good
user_id = 1
is_active = True
max_retries = 3
wardrobe_items = []

# Bad
uid = 1  # Too abbreviated
active = True  # Ambiguous
max = 3  # Reserved word
items = []  # Too generic
```

### Constants

```python
# Good
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
DEFAULT_TIMEOUT = 30
SUPPORTED_FORMATS = {"jpg", "png", "webp"}

# Bad
max_upload_size = 100 * 1024 * 1024
default_timeout = 30
```

### Boolean Variables

```python
# Good
is_authenticated = True
has_permission = False
can_delete = True
should_retry = True

# Bad
authenticated = True  # Ambiguous
permission = False  # Not clearly boolean
deleted = True  # Past tense
```

---

## Code Organization by Module

### Backend Module Structure

```
app/backend/
├── __init__.py          # Package exports
├── database.py          # ORM models, session
├── security.py          # Auth, encryption
├── schemas.py           # Pydantic schemas
├── session_manager.py   # Session handling
├── logging_config.py    # Logging setup
├── storage_config.py    # Storage paths
└── routes/
    ├── __init__.py
    ├── auth.py         # Auth endpoints
    ├── wardrobe.py     # Wardrobe endpoints
    ├── items.py        # Item endpoints
    ├── outfits.py      # Outfit endpoints
    └── ml_models.py    # ML endpoints
```

### Imports in __init__.py

```python
# app/backend/__init__.py
from .database import Base, get_db, User, Wardrobe, Item
from .security import hash_password, verify_password
from .session_manager import SessionManager

__all__ = [
    "Base",
    "get_db",
    "User",
    "Wardrobe",
    "Item",
    "hash_password",
    "verify_password",
    "SessionManager",
]
```

---

## Pre-commit Hooks

### Setup Pre-commit

```bash
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
EOF

# Install hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

---

## Logging Standards

### Logging Setup

```python
import logging

logger = logging.getLogger(__name__)

# Good logging
logger.info("User created successfully", extra={"user_id": user.id})
logger.warning("Attempt to access deleted wardrobe", extra={"wardrobe_id": wid})
logger.error("Database connection failed", exc_info=True)

# Bad logging
logger.info("done")  # Too vague
logger.warning("error")  # Confusing level
logger.debug(f"user.password = {user.password}")  # Don't log secrets!
```

### Log Levels

- **DEBUG:** Detailed information for diagnosing problems
- **INFO:** Confirmation that operations worked
- **WARNING:** Warning about potential problems
- **ERROR:** Something failed, but system continues
- **CRITICAL:** Something failed, system may be unusable

---

## Common Anti-patterns to Avoid

| Anti-pattern | Issue | Solution |
|---|---|---|
| Global variables | Hard to test, unpredictable state | Use dependency injection |
| Deep nesting | Reduced readability | Extract methods, early returns |
| Magic numbers | Unclear purpose | Define constants |
| Catch-all exceptions | Hides bugs | Catch specific exceptions |
| Missing type hints | Harder to debug | Add type annotations |
| God classes | Too many responsibilities | Refactor into smaller classes |
| Mutable default args | Surprising behavior | Use None instead |
| Circular imports | Import errors | Reorganize module structure |

---

## Related Documentation

- [Testing Guide](testing.md)
- [Architecture Guide](architecture.md)
- [Database Guide](database.md)
