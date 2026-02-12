# Developer Guide - Database

Database schema, models, and data management.

## Database Technology

### SQLite (Development)
- **File-based:** `app/data/wardrobes.db`
- **Auto-creation:** On first startup
- **Type:** Single-file database
- **Ideal for:** Development, single-user

### PostgreSQL (Production)
- **Remote:** Separate database server
- **Scalability:** Better for multi-user
- **Features:** Advanced, ACID compliance
- **Configuration:** Via `DATABASE_URL` env var

---

## Database Connection

### Connection String Format

**SQLite:**
```
sqlite:///./data/wardrobes.db
```

**PostgreSQL:**
```
postgresql://user:password@localhost/wardrobe_db
```

### Connection Management

**SQLAlchemy Setup:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
```

**Session Usage in Routes:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In route:
@app.get("/wardrobes")
async def get_wardrobes(db: Session = Depends(get_db)):
    # Use db for queries
    wardrobes = db.query(Wardrobe).all()
    return wardrobes
```

---

## Database Schema

### Core Models

#### User Model

**Purpose:** Store user account information

**Fields:**
```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: str = Column(String(50), unique=True, nullable=False, index=True)
    password_hash: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wardrobes: List["Wardrobe"] = relationship("Wardrobe", back_populates="user", cascade="all, delete-orphan")
```

**Constraints:**
- `username`: UNIQUE, NOT NULL, INDEX
- `password_hash`: NOT NULL (bcrypt hash)
- `created_at/updated_at`: Automatic timestamps

**Table:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
```

---

#### Wardrobe Model

**Purpose:** User's clothing collection

**Fields:**
```python
class Wardrobe(Base):
    __tablename__ = "wardrobes"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: str = Column(String(100), nullable=False)
    description: str = Column(String(500), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: User = relationship("User", back_populates="wardrobes")
    items: List["Item"] = relationship("Item", back_populates="wardrobe", cascade="all, delete-orphan")
    outfits: List["Outfit"] = relationship("Outfit", back_populates="wardrobe", cascade="all, delete-orphan")
```

**Constraints:**
- `user_id`: FOREIGN KEY (users.id), NOT NULL
- `name`: NOT NULL (1-100 chars)
- One-to-many with Items and Outfits

**One Wardrobe Per User:**
```sql
CREATE UNIQUE INDEX idx_user_default_wardrobe 
ON wardrobes(user_id) 
WHERE name = 'Default';
```

---

#### Item Model

**Purpose:** Individual clothing pieces

**Fields:**
```python
class Item(Base):
    __tablename__ = "items"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wardrobe_id: UUID = Column(UUID(as_uuid=True), ForeignKey("wardrobes.id"), nullable=False, index=True)
    name: str = Column(String(100), nullable=False)
    category: str = Column(String(50), nullable=True)
    subcategory: str = Column(String(50), nullable=True)
    color: str = Column(String(50), nullable=True)
    brand: str = Column(String(100), nullable=True)
    size: str = Column(String(20), nullable=True)
    image_path: str = Column(String(500), nullable=False)
    embedding: List[float] = Column(JSON, nullable=True)  # CLIP embeddings
    attributes: dict = Column(JSON, nullable=True)  # Auto-detected attributes
    notes: str = Column(String(500), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wardrobe: Wardrobe = relationship("Wardrobe", back_populates="items")
    outfits: List["Outfit"] = relationship("Outfit", secondary="outfit_items", back_populates="items")
```

**Indexes:**
```sql
CREATE INDEX idx_items_wardrobe_id ON items(wardrobe_id);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_color ON items(color);
CREATE INDEX idx_items_created_at ON items(created_at);
```

---

#### Outfit Model

**Purpose:** Generated outfit recommendations

**Fields:**
```python
class Outfit(Base):
    __tablename__ = "outfits"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wardrobe_id: UUID = Column(UUID(as_uuid=True), ForeignKey("wardrobes.id"), nullable=False, index=True)
    compatibility_score: float = Column(Float, nullable=False)  # 0-1 range
    occasion: str = Column(String(50), nullable=True)  # casual, formal, sports, etc.
    rating: int = Column(Integer, nullable=True)  # 1-5 stars (maps to 0.2-1.0)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    rated_at: datetime = Column(DateTime, nullable=True)
    
    # Relationships
    wardrobe: Wardrobe = relationship("Wardrobe", back_populates="outfits")
    items: List["Item"] = relationship("Item", secondary="outfit_items", back_populates="outfits")
```

**Constraints:**
- `wardrobe_id`: FOREIGN KEY
- `compatibility_score`: 0-1 float
- `rating`: 1-5 integer (optional)
- Many-to-many with Items via OutfitItems

**Rating Normalization:**
```python
# Frontend to Backend
backend_rating = (frontend_rating * 0.2)  # 5 → 1.0, 1 → 0.2

# Backend to Frontend  
frontend_rating = round(backend_rating * 5)  # 1.0 → 5, 0.2 → 1
```

---

#### OutfitItem Model (Junction Table)

**Purpose:** Many-to-many relationship between Outfits and Items

**Fields:**
```python
class OutfitItem(Base):
    __tablename__ = "outfit_items"
    
    outfit_id: UUID = Column(UUID(as_uuid=True), ForeignKey("outfits.id"), primary_key=True)
    item_id: UUID = Column(UUID(as_uuid=True), ForeignKey("items.id"), primary_key=True)
    position: int = Column(Integer, nullable=False)  # Order in outfit
    
    # Relationships
    outfit: Outfit = relationship("Outfit")
    item: Item = relationship("Item")
```

**Constraints:**
- Composite primary key (outfit_id, item_id)
- Foreign keys to both tables
- Position for ordering

**Table Definition:**
```sql
CREATE TABLE outfit_items (
    outfit_id UUID NOT NULL REFERENCES outfits(id),
    item_id UUID NOT NULL REFERENCES items(id),
    position INTEGER NOT NULL,
    PRIMARY KEY (outfit_id, item_id)
);

CREATE INDEX idx_outfit_items_outfit ON outfit_items(outfit_id);
CREATE INDEX idx_outfit_items_item ON outfit_items(item_id);
```

---

## Entity-Relationship Diagram

```
┌─────────────┐
│   User      │
├─────────────┤
│ id (PK)     │
│ username    │
│ password    │
└────────┬────┘
         │ 1:N
         │
         ▼
┌──────────────────┐
│   Wardrobe       │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ name             │
│ description      │
└─────┬──────┬─────┘
      │      │
    1:N   1:N
      │    │
      ▼    ▼
┌──────────┐   ┌─────────┐
│  Item    │───┤Outfit   │
├──────────┤   │Item     │
│ id (PK)  │   └─────────┘
│ wardrobe │
│_id (FK)  │   (Junction Table)
│ category │
│ color    │
│ embedding│
└──────────┘

Outfit also has FK to Wardrobe
```

---

## Queries & Operations

### User Operations

**Create User:**
```python
db.add(User(
    username=username,
    password_hash=bcrypt_hash(password),
    created_at=datetime.utcnow()
))
db.commit()
```

**Get User by Username:**
```python
user = db.query(User).filter(User.username == username).first()
```

**Update User:**
```python
user.updated_at = datetime.utcnow()
db.commit()
```

---

### Wardrobe Operations

**Create Wardrobe:**
```python
wardrobe = Wardrobe(
    user_id=user_id,
    name=name,
    description=description
)
db.add(wardrobe)
db.commit()
```

**Get User's Wardrobes:**
```python
wardrobes = db.query(Wardrobe).filter(
    Wardrobe.user_id == user_id
).all()
```

**Get Wardrobe with Items (Eager Load):**
```python
from sqlalchemy.orm import joinedload

wardrobe = db.query(Wardrobe).options(
    joinedload(Wardrobe.items)
).filter(
    Wardrobe.id == wardrobe_id
).first()
```

---

### Item Operations

**Create Item:**
```python
item = Item(
    wardrobe_id=wardrobe_id,
    name=name,
    category=category,
    color=color,
    image_path=image_path,
    embedding=embedding_vector
)
db.add(item)
db.commit()
```

**Get Items by Category:**
```python
items = db.query(Item).filter(
    Item.wardrobe_id == wardrobe_id,
    Item.category == category
).all()
```

**Get Items by Color:**
```python
items = db.query(Item).filter(
    Item.wardrobe_id == wardrobe_id,
    Item.color == color
).all()
```

**Update Item:**
```python
item.color = new_color
item.category = new_category
item.updated_at = datetime.utcnow()
db.commit()
```

---

### Outfit Operations

**Create Outfit:**
```python
outfit = Outfit(
    wardrobe_id=wardrobe_id,
    compatibility_score=0.87,
    occasion="casual"
)
db.add(outfit)
db.flush()  # Get outfit.id

# Add items to outfit
for position, item in enumerate(items):
    outfit_item = OutfitItem(
        outfit_id=outfit.id,
        item_id=item.id,
        position=position
    )
    db.add(outfit_item)

db.commit()
```

**Get Outfit with Items:**
```python
outfit = db.query(Outfit).options(
    joinedload(Outfit.items)
).filter(
    Outfit.id == outfit_id
).first()
```

**Get Recent Outfits:**
```python
outfits = db.query(Outfit).filter(
    Outfit.wardrobe_id == wardrobe_id
).order_by(
    Outfit.created_at.desc()
).limit(10).all()
```

**Rate Outfit:**
```python
outfit = db.query(Outfit).get(outfit_id)
outfit.rating = rating  # 1-5
outfit.rated_at = datetime.utcnow()
db.commit()
```

**Get Rated Outfits:**
```python
outfits = db.query(Outfit).filter(
    Outfit.wardrobe_id == wardrobe_id,
    Outfit.rating != None  # Only rated
).all()
```

---

## Migrations

### Using Alembic (Future)

**Setup:**
```bash
alembic init alembic
```

**Create Migration:**
```bash
alembic revision --autogenerate -m "Add Item table"
```

**Apply Migration:**
```bash
alembic upgrade head
```

### Manual Schema Creation

```python
# In app startup
from app.backend.database import Base, engine

Base.metadata.create_all(bind=engine)
```

---

## Performance Optimization

### Indexes

**Frequently Queried Columns:**
```python
# Username lookup
Column(String, index=True)

# User ID filter
Column(UUID, ForeignKey(...), index=True)

# Category/Color filter
Column(String, index=True)

# Date range queries
Column(DateTime, index=True)
```

**Query Example with Indexes:**
```python
# Fast: Uses index on user_id
wardrobes = db.query(Wardrobe).filter(
    Wardrobe.user_id == user_id
).all()

# Fast: Uses index on category
items = db.query(Item).filter(
    Item.category == "shirts"
).all()
```

### Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Connections to keep open
    max_overflow=40,  # Additional connections if needed
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

### Batch Operations

```python
# Efficient batch insert
items = [Item(...) for _ in range(100)]
db.bulk_insert_mappings(Item, items)
db.commit()

# Efficient batch update
db.query(Item).filter(
    Item.category == "old"
).update({Item.category: "new"})
db.commit()
```

---

## Transactions

### Auto-commit Behavior

```python
# Automatic transaction
session = SessionLocal()
try:
    user = User(username="test")
    session.add(user)
    session.commit()  # Transaction committed
except Exception:
    session.rollback()  # Rollback on error
finally:
    session.close()
```

### Explicit Transactions

```python
try:
    # Multiple operations in one transaction
    wardrobe = create_wardrobe(...)
    for item_data in items:
        create_item(wardrobe.id, item_data)
    
    db.commit()  # All or nothing
except Exception:
    db.rollback()  # Revert all changes
```

---

## Data Validation

### Model-Level Validation

```python
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^[a-z_]+$")
    color: Optional[str] = None
    
    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v
```

### Database Constraints

```python
class Item(Base):
    name: str = Column(String(100), nullable=False)
    category: str = Column(String(50), index=True)
    # Constraints enforced at DB level
```

---

## Backup & Recovery

### SQLite Backup

```bash
# Simple file copy
cp app/data/wardrobes.db app/data/wardrobes_backup.db

# Scheduled backup
0 2 * * * cp /app/data/wardrobes.db /backup/wardrobes_$(date +\%Y\%m\%d).db
```

### PostgreSQL Backup

```bash
# Dump database
pg_dump postgresql://user:pass@localhost/db > backup.sql

# Restore database
psql postgresql://user:pass@localhost/db < backup.sql
```

---

## Next Steps

- Explore [Storage System](storage.md)
- Learn about [Authentication](authentication.md)
- Read [Machine Learning](machine-learning.md)
- Review [Testing Strategy](testing.md)
