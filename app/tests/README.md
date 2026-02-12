# Backend Unit Tests

Unit tests for the Fashion Wardrobe Manager backend application.

## Test Modules

### test_security.py
Tests for authentication and security functionality:
- Password hashing and verification
- JWT token creation and verification

### test_database.py
Tests for database models and ORM operations:
- User model
- Wardrobe model
- Item model
- Outfit and OutfitItem relationships
- **ItemChange model** - tracks item category corrections for tagger improvement

### test_routes.py
Tests for API endpoints:
- Authentication routes (register, login)
- Wardrobe management routes
- Item CRUD operations
- **Item changes tracking** - verifies corrections are saved with confidence levels
- **Changes statistics** - tests retrieval and analysis of corrections
- **Export for training** - tests data export for tagger retraining
- **Preference rating** - tests outfit ratings for preference learning
- **Tagger training endpoint** - tests background task scheduling for tagger retraining
- **Stats endpoints** - tests statistics retrieval for both tagger and preferences

### test_tagger_learner.py
Tests for machine learning utilities:
- **TaggerFeedbackLearner**: Fine-tuning item category tagger on user corrections
  - Model initialization and training
  - Correction sample handling
  - Training history and persistence
- **UserPreferenceLearner**: Per-user outfit preference learning
  - Rating buffering and background training
  - Outfit score prediction
  - Model persistence and loading
  - Statistics tracking

## Running Tests

Run all tests:
```bash
pytest app/tests/
```

Run specific test module:
```bash
pytest app/tests/test_routes.py
```

Run specific test class:
```bash
pytest app/tests/test_routes.py::TestItemChangesTracking
```

Run with coverage:
```bash
pytest app/tests/ --cov=app
```

## Key Features Tested

### Item Change Tracking
- Users can correct item category classifications
- Changes are recorded with confidence levels
- Multiple corrections per item are supported
- Changes can be filtered by confidence threshold

### Tagger Feedback Learning
- Collected corrections can be exported for training
- TaggerFeedbackLearner fine-tunes on correction data
- Background training doesn't block API requests
- Training history and models are persisted

### User Preference Learning
- Users rate outfits (0-5 scale, normalized to 0-1)
- Ratings are buffered and trigger background training
- Per-user models fine-tuned via transfer learning
- User models predict personalized outfit scores
- Models and training history persist across sessions
- Background training with threading (non-blocking)

### Non-Blocking Training
- Tagger training runs in background threads via `BackgroundTasks`
- Preference learning spawns threads automatically when buffer fills
- API endpoints return immediately after scheduling training
- Training history and models saved asynchronously
- TokenData validation

**Test Classes:**
- `TestPasswordHashing` - Password security tests
- `TestJWTTokens` - JWT token tests
- `TestTokenData` - Token data model tests

### test_database.py
Tests for database models and operations:
- User model and operations
- Wardrobe model and relationships
- Item model with embeddings and attributes
- Outfit and OutfitItem models

**Test Classes:**
- `TestUserModel` - User creation and queries
- `TestWardrobeModel` - Wardrobe operations
- `TestItemModel` - Item management
- `TestOutfitModel` - Outfit and outfit items

### test_routes.py
Tests for API endpoints:
- Authentication routes (register, login)
- Wardrobe routes (CRUD operations)
- Health check endpoint
- Error handling and validation

**Test Classes:**
- `TestAuthRoutes` - Authentication endpoint tests
- `TestWardrobeRoutes` - Wardrobe endpoint tests
- `TestHealthCheck` - Health check endpoint
- `TestErrorHandling` - Error handling tests

### conftest.py
Pytest configuration and shared fixtures:
- Test database setup
- Test fixtures (test_config, mock_image_path)
- Path configuration

## Running Tests

### Run all tests
```bash
pytest app/tests/
```

### Run specific test module
```bash
pytest app/tests/test_security.py
pytest app/tests/test_database.py
pytest app/tests/test_routes.py
```

### Run specific test class
```bash
pytest app/tests/test_security.py::TestPasswordHashing
pytest app/tests/test_database.py::TestUserModel
```

### Run specific test
```bash
pytest app/tests/test_security.py::TestPasswordHashing::test_hash_password
```

### Run with verbose output
```bash
pytest app/tests/ -v
```

### Run with coverage
```bash
pytest app/tests/ --cov=app --cov-report=html
```

### Run with markers
```bash
pytest app/tests/ -m "not slow"
```

## Test Coverage

Target coverage areas:
- Security module (password hashing, JWT tokens)
- Database models and relationships
- API routes and endpoints
- Error handling and validation
- Authentication flow

## Requirements

The tests require the following dependencies:
- pytest
- pytest-cov (for coverage reports)
- sqlalchemy
- fastapi
- starlette (for TestClient)

Install with:
```bash
pip install -r requirements.txt
```

## Notes

- Tests use in-memory SQLite databases for isolation
- Each test is independent and cleans up after itself
- Fixtures provide reusable test data and configurations
- Authentication tests validate token creation and verification
- Database tests verify model relationships and constraints
