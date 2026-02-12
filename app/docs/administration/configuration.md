# Administration Guide - Configuration

Environment configuration and settings management.

## Configuration Overview

### Configuration Levels

1. **Default Settings** - Built into code
2. **Environment Variables** - Override defaults
3. **Configuration Files** - Settings per environment
4. **.env Files** - Local overrides (development only)

### Configuration Priority

```
.env (local) > Environment Variables > Config Files > Defaults
```

---

## Environment Variables

### Essential Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Debug mode (development only) |
| `SECRET_KEY` | - | Secret key for JWT signing |
| `DATABASE_URL` | `sqlite:///app.db` | Database connection string |
| `STORAGE_PATH` | `~/.fashion_wardrobe_app` | File storage directory |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed host names |
| `CORS_ORIGINS` | `http://localhost:3000` | CORS allowed origins |
| `LOG_LEVEL` | `INFO` | Logging level |

### Authentication Variables

```bash
# JWT Configuration
TOKEN_EXPIRY=3600                    # 1 hour in seconds
REFRESH_TOKEN_EXPIRY=2592000        # 30 days in seconds
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_DIGITS=true
```

### Database Variables

```bash
# SQLite (Development)
DATABASE_URL=sqlite:///./app.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/fashion_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
```

### Storage Variables

```bash
# File Storage
STORAGE_PATH=/home/user/.fashion_wardrobe_app
MAX_UPLOAD_SIZE=104857600  # 100 MB
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,webp

# Model Storage
MODEL_CACHE_PATH=/opt/models
ENABLE_GPU=true
DEVICE=cuda  # cuda or cpu
```

### Email Variables (Optional)

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=Fashion App <notifications@example.com>
ENABLE_EMAIL_NOTIFICATIONS=false
```

---

## Configuration Files

### .env File (Development)

**File:** `.env.development`

```bash
# Server
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///./app.db

# Storage
STORAGE_PATH=~/.fashion_wardrobe_app

# Logging
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# ML Models
ENABLE_GPU=false
```

### .env File (Production)

**File:** `.env.production`

```bash
# Server
DEBUG=false
SECRET_KEY=your-very-secret-key-minimum-32-chars

# Database
DATABASE_URL=postgresql://fashion:password@db.example.com:5432/fashion_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Storage
STORAGE_PATH=/mnt/storage/.fashion_wardrobe_app
MAX_UPLOAD_SIZE=104857600

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=https://app.example.com

# ML Models
ENABLE_GPU=true
DEVICE=cuda
```

### Configuration Module

**File:** `app/config.py`

```python
"""Application configuration"""
import os
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    DEBUG: bool = Field(False, description="Debug mode")
    SECRET_KEY: str = Field(..., description="Secret key for JWT")
    
    # Database
    DATABASE_URL: str = Field(
        "sqlite:///./app.db",
        description="Database connection string"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Storage
    STORAGE_PATH: str = Field(
        "~/.fashion_wardrobe_app",
        description="File storage path"
    )
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    # Authentication
    TOKEN_EXPIRY: int = 3600  # 1 hour
    REFRESH_TOKEN_EXPIRY: int = 2592000  # 30 days
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # ML Models
    ENABLE_GPU: bool = False
    DEVICE: str = "cuda"  # cuda or cpu
    MODEL_CACHE_PATH: str = "~/.fashion_wardrobe_app/models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Usage
settings = get_settings()
```

---

## Database Configuration

### SQLite (Development)

```python
# settings.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

from sqlalchemy import create_engine

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)
```

### PostgreSQL (Production)

```python
# settings.py
DATABASE_URL = "postgresql://user:password@localhost:5432/fashion_db"

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    echo=False  # Set True for debugging SQL
)
```

### Database Initialization

```python
from app.backend.database import Base, engine, SessionLocal

def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

# Run once on startup
if __name__ == "__main__":
    init_db()
```

---

## Logging Configuration

### Logging Levels

| Level | Severity | Usage |
|-------|----------|-------|
| DEBUG | Low | Detailed info for diagnosing |
| INFO | Low | Confirmation of operations |
| WARNING | Medium | Warning about issues |
| ERROR | High | Error occurred |
| CRITICAL | Very High | System may be unusable |

### Logging Configuration File

**File:** `logging.yaml`

```yaml
version: 1
disable_existing_loggers: false

formatters:
  default:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  detailed:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: default
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 10

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 10485760
    backupCount: 5

root:
  level: INFO
  handlers: [console, file, error_file]

loggers:
  app:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  sqlalchemy:
    level: WARNING
    handlers: [file]
    propagate: false
```

### Load Logging Configuration

```python
import logging.config
import yaml

with open("logging.yaml") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)
```

---

## CORS Configuration

### FastAPI CORS Setup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

app = FastAPI()
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CORS Configuration Examples

```python
# Development (allow any origin)
allow_origins = ["*"]
allow_methods = ["*"]
allow_headers = ["*"]

# Production (specific origins only)
allow_origins = [
    "https://app.example.com",
    "https://www.example.com",
]
allow_methods = ["GET", "POST", "PUT", "DELETE"]
allow_headers = ["Content-Type", "Authorization"]

# Development with multiple hosts
allow_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
```

---

## Security Configuration

### Secret Key Generation

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: ABC123...XYZ789 (use in .env)
SECRET_KEY=the-generated-key
```

### Password Policy

```python
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special": True,
}

# Special characters allowed
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
```

### HTTPS/SSL Configuration

```nginx
# Nginx SSL settings
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

---

## Feature Flags

### Feature Configuration

```python
# config.py
class Settings:
    # Features
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_OAUTH: bool = False
    ENABLE_API_DOCS: bool = not DEBUG
    ENABLE_GPU: bool = False
    
    # Limits
    MAX_ITEMS_PER_WARDROBE: int = 10000
    MAX_OUTFITS_PER_REQUEST: int = 100
    MAX_CONCURRENT_UPLOADS: int = 5
    
    # Timeouts
    IMAGE_UPLOAD_TIMEOUT: int = 300  # 5 minutes
    MODEL_TRAINING_TIMEOUT: int = 3600  # 1 hour
    API_REQUEST_TIMEOUT: int = 30  # 30 seconds
```

### Using Feature Flags

```python
from app.config import get_settings

settings = get_settings()

if settings.ENABLE_EMAIL_NOTIFICATIONS:
    # Send email
    send_email(user.email, notification)
else:
    logger.info("Email notifications disabled")
```

---

## Performance Configuration

### Database Connection Pool

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,           # Min connections
    "max_overflow": 40,        # Extra connections
    "pool_timeout": 30,        # Timeout in seconds
    "pool_recycle": 3600,      # Recycle after 1 hour
    "echo": False,             # Set True for SQL logging
}
```

### File Uploads

```python
# Limits
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks
TIMEOUT_SECONDS = 300  # 5 minutes
```

### ML Model Loading

```python
# Cache models in memory
MODEL_CACHE_SIZE = 5  # Max 5 models cached

# Device configuration
DEVICE = "cuda"  # gpu for faster inference
BATCH_SIZE = 32  # Batch size for processing
```

---

## Monitoring Configuration

### Health Check Endpoints

```python
# Enable/disable health checks
ENABLE_HEALTH_CHECK = True
HEALTH_CHECK_INTERVAL = 30  # Check every 30 seconds

# Included in health check
CHECK_DATABASE = True
CHECK_STORAGE = True
CHECK_MODELS = True
```

### Metrics Collection

```python
# Prometheus metrics
ENABLE_METRICS = True
METRICS_PORT = 9090
METRICS_PREFIX = "fashion_app_"
```

---

## Configuration Validation

### Validate on Startup

```python
# app/main.py
from app.config import get_settings

@app.on_event("startup")
async def startup():
    settings = get_settings()
    
    # Validate storage path
    storage_path = Path(settings.STORAGE_PATH).expanduser()
    if not storage_path.exists():
        storage_path.mkdir(parents=True)
    
    # Validate database connection
    try:
        db_session = SessionLocal()
        db_session.execute("SELECT 1")
        db_session.close()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    logger.info("Configuration validated successfully")
```

---

## Configuration Management Tools

### Environment File Management

```bash
# Use different .env files by environment
export ENV=production
source .env.$ENV

# Or specify file directly
set -a
source .env.production
set +a
```

### Configuration Secrets

```bash
# Don't commit secrets to git
echo ".env.*.local" >> .gitignore

# Use environment variables in CI/CD
# Set in GitHub Secrets, GitLab CI/CD, etc.
```

---

## Next Steps

- Review [Deployment](deployment.md)
- Read [Monitoring](monitoring.md)
- Check [Security](security.md)
