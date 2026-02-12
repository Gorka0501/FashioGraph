# Developer Guide - Testing

Comprehensive testing strategy, test suites, and best practices.

## Testing Overview

### Test Coverage

**Current Status:** 346 tests, all passing
- Unit tests: 280+
- Integration tests: 50+
- Edge case tests: 16+

**Coverage Areas:**
- ✅ Authentication & security
- ✅ Database operations
- ✅ API endpoints
- ✅ ML model loading
- ✅ Storage operations
- ✅ Business logic

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_database.py         # Database tests
├── test_security.py         # Auth tests
├── test_routes.py           # API endpoint tests
├── test_session_manager.py  # Session tests
├── test_storage_config.py   # Storage tests
├── test_preference_learner.py # ML tests
├── test_tagger_learner.py   # ML tests
└── __init__.py
```

---

## Test Framework & Configuration

### pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
minversion = 7.0
addopts = -v --tb=short --strict-markers
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
timeout = 300
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests requiring ML models
    database: Database tests
    security: Security and auth tests
```

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_security.py

# Run with markers
pytest -m unit  # Only unit tests
pytest -m "not slow"  # Skip slow tests

# Run specific test
pytest tests/test_security.py::TestPasswordHashing::test_hash_password

# Run with output
pytest -v  # Verbose
pytest -s  # Show print statements
pytest --tb=long  # Detailed tracebacks
```

---

## Fixtures (conftest.py)

### Database Fixtures

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.backend.database import Base

@pytest.fixture(scope="function")
def db():
    """Create temporary test database"""
    
    # Create in-memory SQLite
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    yield db
    
    db.close()
    engine.dispose()

@pytest.fixture(scope="function")
def db_user(db):
    """Create test user"""
    from app.backend.database import User
    from app.backend.security import hash_password
    
    user = User(
        username="testuser",
        password_hash=hash_password("TestPass123!")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
```

### Authentication Fixtures

```python
@pytest.fixture
def valid_token(db_user):
    """Generate valid JWT token"""
    from app.backend.security import create_access_token
    from datetime import timedelta
    
    token = create_access_token(
        data={"sub": str(db_user.id), "username": db_user.username},
        expires_delta=timedelta(hours=1)
    )
    return token

@pytest.fixture
def headers_with_auth(valid_token):
    """HTTP headers with authorization"""
    return {"Authorization": f"Bearer {valid_token}"}
```

### File System Fixtures

```python
import tempfile
from pathlib import Path

@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    storage_path = tmp_path / ".fashion_wardrobe_app"
    storage_path.mkdir()
    
    (storage_path / "images").mkdir()
    (storage_path / "models").mkdir()
    (storage_path / "sessions").mkdir()
    
    return storage_path
```

---

## Unit Tests

### Authentication Tests

```python
import pytest
from app.backend.security import hash_password, verify_password, is_strong_password

class TestPasswordHashing:
    """Test password hashing"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "MyPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
    
    def test_wrong_password(self):
        """Test wrong password fails"""
        password = "MyPassword123!"
        wrong_password = "WrongPassword"
        hashed = hash_password(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_hash_is_unique(self):
        """Test same password produces different hashes"""
        password = "MyPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different due to salt

class TestPasswordStrength:
    """Test password strength validation"""
    
    @pytest.mark.parametrize("password,valid", [
        ("weak", False),
        ("NoDigits!", False),
        ("nouppercase123", False),
        ("NoLowercase123", False),
        ("MyPass123!", True),
        ("SecurePassword456", True),
    ])
    def test_password_strength(self, password, valid):
        """Test various password strengths"""
        assert is_strong_password(password) == valid
```

### Database Tests

```python
import pytest
from app.backend.database import User, Wardrobe, Item

class TestUserOperations:
    """Test user database operations"""
    
    def test_create_user(self, db):
        """Test creating user"""
        from app.backend.security import hash_password
        
        user = User(
            username="testuser",
            password_hash=hash_password("Password123!")
        )
        db.add(user)
        db.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.created_at is not None

    def test_user_uniqueness(self, db, db_user):
        """Test username uniqueness"""
        from sqlalchemy.exc import IntegrityError
        
        duplicate = User(
            username="testuser",  # Same as db_user
            password_hash="hash"
        )
        db.add(duplicate)
        
        with pytest.raises(IntegrityError):
            db.commit()

class TestWardrobeOperations:
    """Test wardrobe database operations"""
    
    def test_create_wardrobe(self, db, db_user):
        """Test creating wardrobe"""
        wardrobe = Wardrobe(
            user_id=db_user.id,
            name="Summer Collection"
        )
        db.add(wardrobe)
        db.commit()
        
        assert wardrobe.id is not None
        assert wardrobe.name == "Summer Collection"
        assert wardrobe.user_id == db_user.id

    def test_wardrobe_items_relationship(self, db, db_user):
        """Test wardrobe-items relationship"""
        wardrobe = Wardrobe(user_id=db_user.id, name="Test")
        db.add(wardrobe)
        db.commit()
        
        item = Item(
            wardrobe_id=wardrobe.id,
            name="Test Item",
            image_path="/path/to/image.jpg"
        )
        db.add(item)
        db.commit()
        
        # Reload to test relationship
        wardrobe = db.query(Wardrobe).get(wardrobe.id)
        assert len(wardrobe.items) == 1
        assert wardrobe.items[0].name == "Test Item"
```

---

## Integration Tests

### API Endpoint Tests

```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client(db):
    """Create FastAPI test client"""
    from app.main import app
    from app.backend.database import get_db
    
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)

class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "password": "NewPass123!"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["username"] == "newuser"
    
    def test_login_user(self, client, db_user):
        """Test user login"""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPass123!"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, db_user):
        """Test login with wrong password"""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401

class TestWardrobeEndpoints:
    """Test wardrobe API endpoints"""
    
    def test_create_wardrobe(self, client, headers_with_auth):
        """Test creating wardrobe"""
        response = client.post(
            "/wardrobes",
            json={"name": "Summer Collection"},
            headers=headers_with_auth
        )
        
        assert response.status_code == 201
        assert response.json()["name"] == "Summer Collection"
    
    def test_get_wardrobes(self, client, headers_with_auth):
        """Test getting wardrobes"""
        # Create wardrobe first
        client.post(
            "/wardrobes",
            json={"name": "Test"},
            headers=headers_with_auth
        )
        
        response = client.get(
            "/wardrobes",
            headers=headers_with_auth
        )
        
        assert response.status_code == 200
        wardrobes = response.json()["wardrobes"]
        assert len(wardrobes) > 0
    
    def test_unauthorized_access(self, client):
        """Test access without token"""
        response = client.get("/wardrobes")
        
        assert response.status_code == 403  # Forbidden
```

---

## Test Data Builders

### Factories for Test Data

```python
from datetime import datetime
import uuid

class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create(db, username="testuser", password="TestPass123!"):
        from app.backend.database import User
        from app.backend.security import hash_password
        
        user = User(
            username=username,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

class WardrobeFactory:
    """Factory for creating test wardrobes"""
    
    @staticmethod
    def create(db, user_id, name="Test Wardrobe"):
        from app.backend.database import Wardrobe
        
        wardrobe = Wardrobe(
            user_id=user_id,
            name=name
        )
        db.add(wardrobe)
        db.commit()
        db.refresh(wardrobe)
        return wardrobe

class ItemFactory:
    """Factory for creating test items"""
    
    @staticmethod
    def create(db, wardrobe_id, name="Test Item", **kwargs):
        from app.backend.database import Item
        
        item = Item(
            wardrobe_id=wardrobe_id,
            name=name,
            image_path=kwargs.get("image_path", "/test/image.jpg"),
            category=kwargs.get("category", "shirts"),
            color=kwargs.get("color", "blue")
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

# Usage in tests
def test_with_factories(db):
    user = UserFactory.create(db)
    wardrobe = WardrobeFactory.create(db, user.id)
    item = ItemFactory.create(db, wardrobe.id)
    
    assert item.wardrobe_id == wardrobe.id
```

---

## Testing Best Practices

### Test Structure (Arrange-Act-Assert)

```python
def test_user_can_create_wardrobe(client, headers_with_auth):
    """Test user can create wardrobe (AAA pattern)"""
    
    # Arrange
    wardrobe_data = {"name": "My Wardrobe"}
    
    # Act
    response = client.post(
        "/wardrobes",
        json=wardrobe_data,
        headers=headers_with_auth
    )
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "My Wardrobe"
```

### Descriptive Test Names

```python
# Good
def test_hash_password_returns_different_hash_than_plain_text():
    pass

def test_login_with_correct_password_returns_token():
    pass

def test_create_wardrobe_without_auth_returns_401():
    pass

# Bad
def test_hash():
    pass

def test_login():
    pass

def test_wardrobe():
    pass
```

### Clear Assertions

```python
# Good
assert response.status_code == 200
assert response.json()["username"] == "testuser"
assert len(response.json()["wardrobes"]) == 3

# Bad
assert response
assert response == {...}  # Hard to debug
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input_value,expected", [
    ("strong_password123", True),
    ("weak", False),
    ("NoDigits!", False),
])
def test_password_validation(input_value, expected):
    assert is_strong_password(input_value) == expected
```

---

## Test Performance

### Marking Slow Tests

```python
@pytest.mark.slow
def test_model_loading():
    """This test is slow (loads ML models)"""
    model = load_hgnn_model()
    assert model is not None
```

### Running Fast Tests Only

```bash
pytest -m "not slow"  # Skip slow tests
```

### Timeout Configuration

```python
@pytest.mark.timeout(10)  # 10 second timeout
def test_with_timeout():
    pass
```

---

## Continuous Integration (CI)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=app tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Next Steps

- Review [Code Style](code-style.md)
- Explore [Architecture](architecture.md)
- Read [Machine Learning](machine-learning.md)
