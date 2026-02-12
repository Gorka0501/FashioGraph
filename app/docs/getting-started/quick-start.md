# Quick Start

Get the application running in 5 minutes.

## Prerequisites

- Python 3.9 or later
- pip package manager
- 2GB RAM minimum

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/fashion-wardrobe.git
cd fashion-wardrobe
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -c "from app.backend.database import Base, engine; Base.metadata.create_all(engine)"
```

### 5. Start Application

```bash
python start_web.py
```

The application is now running at `http://localhost:8000`

## Verify Installation

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00",
  "version": "1.0"
}
```

### API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## First Steps

### 1. Create User Account

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

Save the `access_token` from the response.

### 3. Upload Item

```bash
curl -X POST http://localhost:8000/api/wardrobe/1/items/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg"
```

### 4. Generate Outfit

```bash
curl -X POST http://localhost:8000/api/outfits/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wardrobe_id": 1}'
```

## Next Steps

- Learn about the [Architecture](architecture.md)
- Read the [API Reference](../api/)
- Set up [Development Environment](../developer-guide/)

## Troubleshooting

**"Module not found" error?**
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

**"Port 8000 already in use?"**
- Stop other processes: `lsof -i :8000`
- Or use different port: `python start_web.py --port 8001`

**Database error?**
- Reinitialize: `python -c "from app.backend.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"`

More help in [Troubleshooting](../troubleshooting/common-issues.md)
