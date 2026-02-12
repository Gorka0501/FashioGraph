# Installation Guide

Complete setup instructions for development and production environments.

## Prerequisites

### System Requirements

- **Python**: 3.8+ (3.10+ recommended)
- **OS**: Windows, macOS, Linux
- **RAM**: 8GB minimum (16GB recommended for ML models)
- **Disk Space**: 5GB minimum
- **Database**: SQLite (included with Python)

### Required Software

- Python package manager: `pip` or `conda`
- Git (for cloning the repository)
- Virtual environment tool: `venv` or `conda`

### Optional Dependencies

- Docker (for containerized deployment)
- PostgreSQL (for production database)
- Redis (for caching/sessions)

## Development Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd TFM/APP
```

### 2. Create Virtual Environment

**Using venv:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**Using conda:**
```bash
conda create -n wardrobe python=3.10
conda activate wardrobe
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `fastapi==0.104.1` - Web framework
- `sqlalchemy==2.0.23` - ORM
- `pydantic==2.5.0` - Data validation
- `torch==2.1.1` - ML framework
- `torchvision` - Vision utilities
- `pytest==7.4.3` - Testing

### 4. Install Frontend Dependencies (Optional)

```bash
cd frontend
pip install -r requirements.txt
cd ..
```

### 5. Initialize Database

```bash
# The database is auto-created on first run
# No manual initialization needed
```

### 6. Download ML Models

Models are auto-downloaded on first use. Initial startup may take 2-3 minutes.

To pre-download:
```bash
python -c "from app.models.load_models import load_all_models; load_all_models()"
```

## Running the Application

### Backend Only (API Server)

```bash
python start.py
```

Server runs on: `http://localhost:8000`

**Verify startup:**
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

### Web Application

```bash
python start_web.py
```

Runs on: `http://localhost:8501`

### Desktop Application

```bash
python start_desktop.py
```

### Full Stack

```bash
python start.py  # Backend
# In another terminal:
python start_web.py  # Frontend
```

## Verification

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. First API Call - Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### 3. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

Response includes `access_token`.

### 4. Create Wardrobe

```bash
curl -X POST http://localhost:8000/wardrobes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Collection"}'
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///./data/wardrobes.db

# Storage
STORAGE_PATH=~/.fashion_wardrobe_app

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=app/logs/app.log

# Security
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Storage Configuration

The application automatically creates the storage structure:

```
~/.fashion_wardrobe_app/
├── images/
├── models/
├── sessions/
└── logs/
```

Customize path with `STORAGE_PATH` environment variable.

## Testing Setup

### Run All Tests

```bash
pytest
```

### Run Specific Test Suite

```bash
pytest tests/test_database.py
pytest tests/test_routes.py
pytest tests/test_security.py
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

### Test Configuration

Tests use `pytest.ini` configuration:
- Timeout: 300 seconds per test
- Markers: unit, integration, slow
- Database: Temporary SQLite for each test

## Production Deployment

### 1. Production-Grade Installation

```bash
# Install production ASGI server
pip install gunicorn

# Install production database (PostgreSQL)
pip install psycopg2-binary
```

### 2. Environment Setup

```bash
export DATABASE_URL=postgresql://user:password@localhost/wardrobe_db
export SECRET_KEY=generate-strong-key
export LOG_LEVEL=WARNING
export DEBUG=False
```

### 3. Run with Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 4. Docker Deployment

```bash
docker build -t wardrobe-app .
docker run -p 8000:8000 wardrobe-app
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution:**
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt
```

### Issue: Port Already in Use

**Solution:**
```bash
# Use different port
python start.py --port 8001
```

### Issue: Database Locked

**Solution:**
```bash
# Remove old database
rm app/data/wardrobes.db

# Restart application
python start.py
```

### Issue: Slow Model Loading

**Solution:**
```bash
# Pre-download models (one-time)
python -c "from app.models.load_models import load_all_models; load_all_models()"

# Subsequent runs will be faster
```

### Issue: Permission Denied (Linux/macOS)

**Solution:**
```bash
chmod +x start.py start_web.py start_desktop.py
python start.py
```

## Next Steps

1. Read [Quick Start Guide](quick-start.md)
2. Review [Architecture Overview](architecture.md)
3. Explore [API Reference](../api/)
4. Check [Configuration Guide](../administration/configuration.md)
