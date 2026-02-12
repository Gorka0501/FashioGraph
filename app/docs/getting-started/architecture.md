# Architecture Overview

High-level system design and components.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Client Applications                       │
│  (Web Frontend, Mobile, Desktop)                   │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/REST
┌────────────────▼────────────────────────────────────┐
│          FastAPI Server (Port 8000)                │
├────────────────────────────────────────────────────┤
│                    Route Layer                      │
│  ┌──────────┬──────────┬──────────┬──────────┐    │
│  │  Auth    │Wardrobe  │  Items   │ Outfits  │    │
│  │ Routes   │ Routes   │ Routes   │ Routes   │    │
│  └──────────┴──────────┴──────────┴──────────┘    │
├────────────────────────────────────────────────────┤
│              Business Logic Layer                  │
│  ┌──────────────────────────────────────────────┐ │
│  │ • User authentication & session management   │ │
│  │ • Wardrobe & item operations                │ │
│  │ • Outfit generation & compatibility         │ │
│  │ • User preference learning                 │ │
│  │ • Auto-training trigger                    │ │
│  └──────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│         Data Persistence Layer                    │
│  ┌───────────────┬────────────────────────────┐  │
│  │  SQLite DB    │  File Storage (Sessions,   │  │
│  │  (SQLAlchemy) │  Models, Images)           │  │
│  │               │  ~/.fashion_wardrobe_app/  │  │
│  └───────────────┴────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│             ML Model Layer                        │
│  ┌────────────┬────────────────┬──────────────┐  │
│  │   HGNN     │   CLIP         │   ResNet50   │  │
│  │  (Outfits) │ (Embeddings)   │ (Categories) │  │
│  └────────────┴────────────────┴──────────────┘  │
└────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Single-User Per Device

Each device supports one active user session at a time:

```
Device Login Flow:
├── User A logs in → Session created
├── User B logs in → User A's session destroyed
└── User B becomes active user
```

**Benefits:**
- Simplified session management
- Clear user context per device
- Natural multi-device workflow

### 2. Centralized Storage

All application data stored in `~/.fashion_wardrobe_app/`:

```
~/.fashion_wardrobe_app/
├── images/{username}/           ← Item photos
├── models/personal/{username}/  ← User models
├── sessions/{username}.json     ← Current session
├── data/wardrobes.db           ← SQLite database
└── logs/                        ← Application logs
```

### 3. Layered Architecture

Clean separation of concerns:
- **Route Layer**: HTTP endpoint handling
- **Logic Layer**: Business logic implementation
- **Data Layer**: Database & file operations
- **ML Layer**: Model inference & training

## Core Components

### 1. Authentication Module
- User registration and login
- JWT token generation/validation
- Password hashing (bcrypt)
- Session persistence

### 2. Wardrobe Management
- Wardrobe CRUD operations
- Item upload and storage
- Category auto-tagging
- Attribute embeddings

### 3. Outfit Generation
- Neural network scoring
- Compatibility checking
- Rating system
- Outfit persistence

### 4. Personal Model Training
- Per-user model copies
- Auto-training (every 10 ratings)
- Model persistence & versioning
- Training history tracking

### 5. Storage System
- Centralized file management
- Image optimization
- Session persistence
- Model serialization

## Data Flow

### User Upload Flow

```
User uploads image
    ↓
FastAPI receives upload
    ↓
Image validation & storage
    ↓
ResNet50 categorization
    ↓
CLIP embeddings generation
    ↓
Database record creation
    ↓
Response with item details
```

### Outfit Generation Flow

```
Generate outfit request
    ↓
Load wardrobe items
    ↓
HGNN neural network scoring
    ↓
Compatibility verification
    ↓
Select best combination
    ↓
Save to database
    ↓
Return outfit details
```

### Auto-Training Flow

```
User rates outfit
    ↓
Rating saved to database
    ↓
Rating counter incremented
    ↓
If counter == 10:
    ├── Load user's personal model
    ├── Train on 10 ratings
    ├── Save updated model
    └── Log completion
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI | REST API server |
| **Server** | Uvicorn | ASGI application server |
| **Database** | SQLite + SQLAlchemy | Data persistence |
| **Auth** | JWT + bcrypt | User authentication |
| **ML** | PyTorch | Deep learning models |
| **Testing** | pytest | Test framework |

## Storage Structure

```
app/
├── main.py                      ← Entry point
├── backend/
│   ├── database.py             ← ORM models
│   ├── routes/                 ← API endpoints
│   ├── security.py             ← Auth & security
│   └── storage_config.py       ← Storage management
├── models/
│   ├── load_models.py          ← Model loading
│   ├── user_preference_learner.py ← Training
│   └── base/                   ← Pre-trained models
├── utils/
│   ├── outfit_generator.py     ← Outfit logic
│   └── ml_models.py            ← ML utilities
└── tests/
    └── *.py                    ← Test suite
```

## Database Schema

Five main tables:

- **Users**: User accounts & credentials
- **Wardrobes**: One per user (one-to-one)
- **Items**: Clothing items with embeddings
- **Outfits**: Generated recommendations
- **OutfitItems**: Many-to-many relationship

## Request/Response Flow

```
Client Request
    ↓
FastAPI Route Handler
    ↓
Authentication Check (Dependency)
    ↓
Business Logic Processing
    ↓
Database Query/Update
    ↓
Response Serialization
    ↓
Client Response
```

## Key Features

✅ Modular component design  
✅ Clean separation of concerns  
✅ Centralized storage  
✅ Database transaction management  
✅ Comprehensive error handling  
✅ Extensive logging  
✅ 346+ unit tests  

## Next Steps

- Learn about [Database Schema](../developer-guide/database.md)
- Explore [API Endpoints](../api/)
- Read [Storage System](../developer-guide/storage.md)
