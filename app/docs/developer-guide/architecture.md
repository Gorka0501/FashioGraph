# Developer Guide - Architecture

System design, patterns, and architectural decisions.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           Client Applications                       │
│  (Web Frontend, Mobile, Desktop)                   │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/REST
┌────────────────▼────────────────────────────────────┐
│          FastAPI Server (Uvicorn)                  │
├────────────────────────────────────────────────────┤
│                   Route Layer                      │
│  ┌──────────────────────────────────────────────┐ │
│  │ • Authentication Routes                      │ │
│  │ • Wardrobe Routes                           │ │
│  │ • Item Routes                               │ │
│  │ • Outfit Routes                             │ │
│  │ • Model Routes                              │ │
│  └──────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│              Business Logic Layer                  │
│  ┌──────────────────────────────────────────────┐ │
│  │ • User Authentication                        │ │
│  │ • Wardrobe Management                       │ │
│  │ • Item Processing                           │ │
│  │ • Outfit Generation                         │ │
│  │ • Model Training                            │ │
│  │ • Session Management                        │ │
│  └──────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│         Data Persistence Layer                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ SQLAlchemy ORM + SQLite Database           │  │
│  │ • User Model                                │  │
│  │ • Wardrobe Model                           │  │
│  │ • Item Model                               │  │
│  │ • Outfit Model                             │  │
│  │ • OutfitItem Model                         │  │
│  └─────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────┐  │
│  │ File Storage (.fashion_wardrobe_app/)      │  │
│  │ • Item images                              │  │
│  │ • Personal models                          │  │
│  │ • Session data                             │  │
│  │ • Logs                                     │  │
│  └─────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│             ML Model Layer                        │
│  ┌──────────┬────────────┬──────────────────────┐ │
│  │   HGNN   │   CLIP     │   ResNet50           │ │
│  │ (Outfits)│(Embeddings)│ (Classification)     │ │
│  └──────────┴────────────┴──────────────────────┘ │
└────────────────────────────────────────────────────┘
```

---

## Layered Architecture Design

### 1. Route Layer (HTTP Endpoints)

**Responsibility:**
- Handle incoming HTTP requests
- Validate request parameters
- Parse request body/headers
- Call business logic
- Format and return responses

**Files:**
- `app/backend/routes/` - All route definitions
  - `auth.py` - Authentication endpoints
  - `wardrobe.py` - Wardrobe management
  - `items.py` - Item operations
  - `outfits.py` - Outfit generation
  - `models.py` - Model management

**Pattern:**
```python
@router.post("/items")
async def upload_item(
    request: ItemUploadRequest,
    current_user: User = Depends(get_current_user)
):
    # Validation (done by Pydantic)
    # Call business logic
    result = await item_service.upload(request)
    # Return response
    return ItemResponse(**result)
```

---

### 2. Business Logic Layer

**Responsibility:**
- Implement core features
- Handle complex operations
- Coordinate multiple models
- Manage transactions
- Handle errors gracefully

**Components:**

#### User Service
- Registration & authentication
- Password hashing (bcrypt)
- Session management
- Token generation/validation

#### Wardrobe Service
- Create/read/update/delete wardrobes
- Item management
- Statistics calculation
- Organization logic

#### Item Service
- Image upload & storage
- Auto-categorization (ResNet50)
- Embedding generation (CLIP)
- Metadata management

#### Outfit Service
- Outfit generation (HGNN)
- Rating management
- History tracking
- Compatibility scoring

#### Model Service
- Model loading & caching
- Training coordination
- Version management
- Performance tracking

---

### 3. Data Persistence Layer

#### Database Models (SQLAlchemy ORM)

**User Model**
```python
class User(Base):
    id: UUID
    username: str (unique)
    password_hash: str
    created_at: datetime
    updated_at: datetime
    wardrobes: List[Wardrobe]  # Relationship
```

**Wardrobe Model**
```python
class Wardrobe(Base):
    id: UUID
    user_id: UUID (foreign key)
    name: str
    description: str
    created_at: datetime
    items: List[Item]  # Relationship
    outfits: List[Outfit]  # Relationship
```

**Item Model**
```python
class Item(Base):
    id: UUID
    wardrobe_id: UUID (foreign key)
    name: str
    category: str
    color: str
    brand: str
    embedding: List[float]  # CLIP embeddings
    image_path: str
    created_at: datetime
```

**Outfit Model**
```python
class Outfit(Base):
    id: UUID
    wardrobe_id: UUID (foreign key)
    compatibility_score: float (0-1)
    created_at: datetime
    rated_at: datetime (optional)
    rating: int (0-5, optional)
    items: List[Item]  # Many-to-many
```

**OutfitItem Model**
```python
class OutfitItem(Base):
    outfit_id: UUID (foreign key)
    item_id: UUID (foreign key)
    position: int  # Order in outfit
```

#### File Storage

**Organization:**
```
~/.fashion_wardrobe_app/
├── images/
│   └── {username}/
│       ├── {item_id}.jpg
│       ├── {item_id}_thumb.jpg
│       └── ...
├── models/
│   ├── base/
│   │   ├── hgnn.pth
│   │   ├── clip.pth
│   │   └── resnet50.pth
│   └── personal/
│       └── {username}/
│           ├── hgnn_v1.pth
│           ├── hgnn_v2.pth
│           └── ...
├── sessions/
│   └── {username}.json
└── logs/
    └── app.log
```

---

### 4. ML Model Layer

**Models Used:**

| Model | Purpose | Input | Output |
|-------|---------|-------|--------|
| **HGNN** | Outfit compatibility | Item embeddings | 0-1 score |
| **CLIP** | Item embeddings | Images | 768-dim vector |
| **ResNet50** | Category classification | Images | Category label |
| **Attribute Encoder** | Attribute detection | Images | Attributes |

**Model Loading:**
```python
# models are loaded on startup
models = {
    'hgnn': load_hgnn_model(),
    'clip': load_clip_model(),
    'resnet50': load_resnet50_model()
}
```

**Personal Model Training:**
- Triggered after 10 ratings
- Trains on user's outfit ratings
- Creates per-user HGNN copy
- Stored in `~/.fashion_wardrobe_app/models/personal/{username}/`

---

## Design Patterns

### 1. Dependency Injection

FastAPI uses dependency injection for:
- Current user authentication
- Database session management
- Service instances

```python
@router.get("/wardrobes")
async def get_wardrobes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Dependencies automatically resolved
    pass
```

### 2. Service Layer Pattern

Services encapsulate business logic:

```python
class ItemService:
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_item(self, request: ItemUploadRequest) -> Item:
        # Complex business logic here
        # - Image processing
        # - Category detection
        # - Embedding generation
        # - Database save
        pass
```

### 3. Repository Pattern

Data access abstraction:

```python
class ItemRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, item_data: dict) -> Item:
        db_item = Item(**item_data)
        self.db.add(db_item)
        self.db.commit()
        return db_item
    
    async def get_by_id(self, item_id: UUID) -> Item:
        return self.db.query(Item).filter(
            Item.id == item_id
        ).first()
```

### 4. Factory Pattern

Creating complex objects:

```python
class ModelFactory:
    @staticmethod
    def create_hgnn_model(base_path: str) -> HGNNModel:
        # Load base model
        # Configure for user
        # Return ready-to-use model
        pass
    
    @staticmethod
    def create_personal_model(
        username: str,
        base_model: HGNNModel
    ) -> PersonalHGNNModel:
        # Create copy of base
        # Train on user data
        # Return personalized model
        pass
```

### 5. Observer Pattern

Event-driven training:

```python
class RatingObserver:
    def on_rating_created(self, rating: Rating):
        # Check if 10 ratings reached
        # Trigger model training
        # Notify user
        pass
```

---

## Data Flow Diagrams

### User Registration & Login

```
Register Request
    ↓
Validate username (unique?)
    ↓
Hash password (bcrypt)
    ↓
Create User record
    ↓
Return user_id
    ↓
User → Login
    ↓
Verify credentials
    ↓
Generate JWT token
    ↓
Return token
    ↓
Client stores token
    ↓
Include in future requests
```

### Item Upload Flow

```
Upload Request + Image
    ↓
Validate image (format, size)
    ↓
Store image to filesystem
    ↓
ResNet50 categorization
    ↓
CLIP embedding generation
    ↓
Create Item record in DB
    ↓
Link to Wardrobe
    ↓
Return item details
```

### Outfit Generation Flow

```
Generate Request
    ↓
Load wardrobe items
    ↓
Load HGNN model (base or personal)
    ↓
Score all item combinations
    ↓
Select best combination
    ↓
Verify compatibility
    ↓
Create Outfit record
    ↓
Return outfit + score
```

### Rating & Auto-Training Flow

```
Rate Outfit Request
    ↓
Validate rating (0-5)
    ↓
Save rating to Outfit
    ↓
Increment user rating counter
    ↓
If counter < 10:
    ├─ Return success
    └─ Done
    ↓
If counter == 10:
    ├─ Load personal model (or create)
    ├─ Gather last 10 ratings
    ├─ Train on rating data
    ├─ Evaluate accuracy
    ├─ Save updated model
    ├─ Reset counter
    ├─ Notify user
    └─ Done
```

---

## Error Handling Strategy

**Approach:** Exception handling with meaningful responses

```python
try:
    # Route handler logic
    result = await business_logic()
    return {status: "success", data: result}

except ValidationError as e:
    # Pydantic validation failed
    return {"error": str(e), "code": "VALIDATION_ERROR"}

except NotFoundError as e:
    # Resource doesn't exist
    return {"error": str(e), "code": "NOT_FOUND"}

except PermissionError as e:
    # User lacks permission
    return {"error": str(e), "code": "FORBIDDEN"}

except Exception as e:
    # Unexpected error
    log_error(e)
    return {"error": "Internal server error", "code": "SERVER_ERROR"}
```

---

## Security Architecture

### Authentication
- **Method:** JWT (JSON Web Tokens)
- **Duration:** 24 hours
- **Storage:** Client-side (HttpOnly cookies preferred)
- **Validation:** Every protected endpoint

### Authorization
- **Method:** Ownership checks
- **Rule:** Users can only access their own data
- **Enforcement:** At route & service layer

### Password Security
- **Algorithm:** bcrypt
- **Rounds:** 10+
- **Requirements:** 8 chars, uppercase, lowercase, digit

### Data Security
- **At Rest:** SQLite with basic encryption (optional)
- **In Transit:** HTTPS (in production)
- **Validation:** Input validation on all endpoints

---

## Performance Optimization

### Caching
- **ML Models:** Loaded once at startup
- **Database:** SQLAlchemy connection pooling
- **Images:** Thumbnail caching

### Query Optimization
- **Indexes:** On frequently queried columns
- **Eager Loading:** Use joinedload for relationships
- **Pagination:** Limit large result sets

### Async Operations
- **Async/Await:** For I/O bound operations
- **Threading:** For CPU-bound ML operations
- **Background Tasks:** For model training

---

## Testing Architecture

### Test Layers

**Unit Tests** (346 total)
- Test individual components
- Mock external dependencies
- Fast execution
- High coverage

**Integration Tests**
- Test component interactions
- Use real database (temporary)
- Test full flows
- Slower but comprehensive

**Fixtures** (conftest.py)
- Test database setup
- Sample data creation
- Authentication helpers
- Cleanup teardown

---

## Deployment Architecture

### Development
- FastAPI dev server (Uvicorn)
- SQLite database
- Local file storage
- Direct model access

### Production
- Gunicorn + Uvicorn workers
- PostgreSQL database (optional)
- Remote storage (S3, etc.)
- Distributed model serving

---

## Technology Decisions

### Why FastAPI?
✅ Modern, fast framework  
✅ Automatic API documentation  
✅ Type hints & validation  
✅ Async support  
✅ Great developer experience  

### Why SQLAlchemy?
✅ ORM abstraction  
✅ Database agnostic  
✅ Complex queries support  
✅ Relationship management  

### Why SQLite?
✅ Zero configuration  
✅ Single file database  
✅ Great for development  
✅ Sufficient for single-user  

### Why PyTorch for ML?
✅ HGNN implementation  
✅ Model serialization  
✅ GPU support (optional)  
✅ Community models (CLIP, ResNet50)  

---

## Future Architectural Changes

**Planned Improvements:**
- 🔄 Microservices for ML models
- 📊 Distributed training
- 🚀 Message queue for long-running tasks
- 💾 PostgreSQL for production
- ☁️ Cloud storage integration
- 📈 Caching layer (Redis)
- 🔐 Enhanced security (2FA, OAuth)

---

## Next Steps

- Learn about [Database Schema](database.md)
- Explore [Storage System](storage.md)
- Read [Authentication](authentication.md)
- Understand [Machine Learning](machine-learning.md)
