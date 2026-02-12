# Administration Guide - Performance

Performance optimization and scaling strategies.

## Performance Overview

### Performance Metrics

- **Response Time:** Target < 200ms for API calls
- **Throughput:** Target 1000+ requests/second
- **Database:** Query < 50ms for 95th percentile
- **Model Inference:** < 500ms per prediction
- **Availability:** 99.9% uptime SLA

### Performance Baseline

```bash
# Test baseline performance
ab -n 1000 -c 10 http://localhost:8000/api/wardrobes

# Expected output:
# Requests per second: 500+
# Time per request: < 200ms
```

---

## Database Optimization

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,        # Min connections
    max_overflow=40,     # Extra connections
    pool_timeout=30,     # Timeout in seconds
    pool_recycle=3600,   # Recycle after 1 hour
    echo=False           # Set True for debugging
)
```

### Query Optimization

```python
# ✅ Good: Use indexes
from sqlalchemy import Index
from app.backend.database import User

# Create index on frequently searched columns
__table_args__ = (
    Index('idx_user_username', 'username'),
    Index('idx_user_email', 'email'),
    Index('idx_item_wardrobe', 'wardrobe_id'),
)

# ✅ Good: Use relationships efficiently
user_with_wardrobes = (
    db.query(User)
    .filter(User.id == user_id)
    .options(joinedload(User.wardrobes))  # Eager load
    .first()
)

# ❌ Bad: N+1 queries
users = db.query(User).all()
for user in users:
    wardrobes = user.wardrobes  # Queries database for each user
```

### Query Analysis

```sql
-- PostgreSQL: Find slow queries
EXPLAIN ANALYZE
SELECT u.username, COUNT(i.id) 
FROM users u 
LEFT JOIN wardrobes w ON u.id = w.user_id
LEFT JOIN items i ON w.id = i.wardrobe_id
GROUP BY u.id;

-- Create missing indexes
CREATE INDEX idx_wardrobes_user_id ON wardrobes(user_id);
CREATE INDEX idx_items_wardrobe_id ON items(wardrobe_id);
```

### Database Caching

```python
from functools import lru_cache
from sqlalchemy import event
from sqlalchemy.pool import Pool

# Cache frequently accessed data
@lru_cache(maxsize=100)
def get_categories():
    """Cache category list"""
    return db.query(Category).all()

# Invalidate cache on changes
@event.listens_for(Category, "after_update")
def invalidate_categories_cache(mapper, connection, target):
    get_categories.cache_clear()
```

---

## API Performance

### Request/Response Optimization

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZIPMiddleware

app = FastAPI()

# Enable GZIP compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Return only needed fields
from pydantic import BaseModel

class ItemResponse(BaseModel):
    """Minimal item response"""
    id: int
    name: str
    color: str
    # Don't include large fields like image_data
    
    class Config:
        from_attributes = True
```

### Pagination

```python
from fastapi import Query
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list

@app.get("/items")
async def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Return paginated results"""
    skip = (page - 1) * per_page
    
    total = db.query(Item).count()
    items = db.query(Item).offset(skip).limit(per_page).all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items
    )
```

### Caching Responses

```python
from fastapi import FastAPI
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend
from redis import asyncio as aioredis
from fastapi_cache2.decorator import cache

@cache(expire=3600)  # Cache for 1 hour
@app.get("/categories")
async def get_categories():
    """Cached category list"""
    return db.query(Category).all()

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache2.init(RedisBackend(redis), prefix="fastapi-cache")
```

---

## ML Model Performance

### Model Loading & Caching

```python
from functools import lru_cache
import torch

class ModelManager:
    _models = {}
    
    @classmethod
    @lru_cache(maxsize=5)
    def load_model(cls, model_name: str):
        """Load and cache ML model"""
        if model_name not in cls._models:
            if model_name == "hgnn":
                cls._models[model_name] = load_hgnn_model()
            elif model_name == "clip":
                cls._models[model_name] = load_clip_model()
        
        return cls._models[model_name]

# Usage
hgnn_model = ModelManager.load_model("hgnn")
```

### Batch Processing

```python
import numpy as np
from torch.utils.data import DataLoader

def generate_embeddings_batch(items: list):
    """Process multiple items in batch for efficiency"""
    from app.models.load_models import get_models
    
    models = get_models()
    clip_model = models["clip"]
    
    # Batch processing
    batch_size = 32
    embeddings = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_embeddings = clip_model.encode(batch)
        embeddings.extend(batch_embeddings)
    
    return np.array(embeddings)
```

### GPU Acceleration

```python
import torch

class GPUAccelerator:
    @staticmethod
    def get_device():
        """Use GPU if available"""
        return "cuda" if torch.cuda.is_available() else "cpu"
    
    @staticmethod
    def load_model(model_path: str):
        """Load model on appropriate device"""
        device = GPUAccelerator.get_device()
        model = torch.load(model_path)
        model.to(device)
        return model

# Configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ENABLE_GPU = True
```

---

## System Performance

### CPU & Memory Optimization

```bash
# Monitor resource usage
top -p $(pgrep -f uvicorn)

# Check memory usage
ps aux | grep uvicorn | awk '{print $6}' | paste -sd+ | bc

# Check CPU usage
ps aux | grep uvicorn | awk '{print $3}' | paste -sd+ | bc
```

### Worker Configuration

```bash
# Optimal worker count = (CPU cores * 2) + 1
workers=$(($(nproc) * 2 + 1))
echo "Recommended workers: $workers"

# Start with optimal workers
uvicorn app.main:app --workers $workers --port 8000
```

### Memory Limits

```bash
# Set memory limit for Python process
ulimit -v 4194304  # 4 GB limit

# Monitor memory
free -h
vmstat 1 5  # Check memory/swap every second
```

---

## Disk I/O Optimization

### Image Optimization

```python
from PIL import Image
import os

def optimize_image(image_path: str, max_size: tuple = (1920, 1080)):
    """Optimize uploaded images"""
    with Image.open(image_path) as img:
        # Resize if needed
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Compress and save
        img.save(
            image_path,
            'JPEG',
            quality=85,
            optimize=True
        )

# Usage in upload handler
from fastapi import UploadFile

async def upload_image(file: UploadFile):
    filepath = Path(storage_path) / file.filename
    filepath.write_bytes(await file.read())
    
    # Optimize after upload
    optimize_image(str(filepath))
    
    return {"filename": file.filename}
```

### File System Monitoring

```bash
# Check disk usage
du -sh ~/.fashion_wardrobe_app/*

# Find large files
find ~/.fashion_wardrobe_app -type f -size +100M

# Monitor I/O
iostat -x 1 5
```

---

## Network Optimization

### Compression

```nginx
# Enable gzip compression in Nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
gzip_comp_level 6;
gzip_vary on;

# Add Vary header for caching proxies
add_header Vary Accept-Encoding;
```

### CDN Integration

```python
# Serve static files from CDN
STATIC_URL = "https://cdn.example.com/static/"

# Image URLs from CDN
image_url = f"{CDN_URL}images/{image_id}.jpg"
```

### Connection Optimization

```nginx
# Nginx connection settings
keepalive_timeout 65;
keepalive_requests 100;

# TCP settings
client_body_timeout 12;
client_header_timeout 12;
send_timeout 10;
```

---

## Monitoring Performance

### Real-time Metrics

```python
from prometheus_client import Histogram, Counter

# Track endpoint performance
endpoint_latency = Histogram(
    'endpoint_latency_seconds',
    'Endpoint latency',
    ['endpoint']
)

# Track database queries
db_query_time = Histogram(
    'db_query_seconds',
    'Database query time'
)

# Track model inference
inference_time = Histogram(
    'model_inference_seconds',
    'Model inference time',
    ['model_name']
)
```

### Performance Dashboard

```promql
# Average response time
rate(endpoint_latency_sum[5m]) / rate(endpoint_latency_count[5m])

# Database query performance
rate(db_query_seconds_sum[5m]) / rate(db_query_seconds_count[5m])

# Model inference latency
histogram_quantile(0.95, rate(model_inference_seconds_bucket[5m]))
```

---

## Scaling Strategies

### Horizontal Scaling

```yaml
# Docker Compose with multiple workers
version: '3.8'

services:
  app:
    image: fashion-app:latest
    deploy:
      replicas: 3
    environment:
      WORKER_ID: 1  # Set per container
    ports:
      - "8000:8000"
      - "8001:8000"
      - "8002:8000"
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - app
```

### Vertical Scaling

```python
# Optimize for larger instances
WORKERS = multiprocessing.cpu_count()  # Use all cores
DATABASE_POOL_SIZE = 30  # Larger connection pool
MODEL_CACHE_SIZE = 10  # Cache more models
BATCH_SIZE = 64  # Larger batches for GPU
```

### Load Balancing

```nginx
# Nginx load balancing configuration
upstream app_servers {
    least_conn;  # Use least connections strategy
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
    }
}
```

---

## Performance Testing

### Load Testing

```bash
# Install wrk (fast HTTP benchmarking tool)
brew install wrk  # macOS
sudo apt-get install wrk  # Ubuntu

# Run load test
wrk -t12 -c400 -d30s --latency http://localhost:8000/api/wardrobes

# Expected output shows latency distribution
# Avg latency: < 200ms
# Max latency: < 1000ms
```

### Stress Testing

```bash
# Test with high concurrency
ab -n 10000 -c 100 http://localhost:8000/api/wardrobes

# Apache Bench output:
# Requests per second: 500+
# Time per request: < 200ms
```

### Profiling

```python
from cProfile import Profile
from pstats import Stats

def profile_function():
    pr = Profile()
    pr.enable()
    
    # Run code to profile
    for _ in range(1000):
        expensive_operation()
    
    pr.disable()
    stats = Stats(pr)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

---

## Performance Checklist

- [ ] Database indexes created on frequent queries
- [ ] Query N+1 problems eliminated
- [ ] Connection pooling configured
- [ ] Caching enabled (Redis/memcached)
- [ ] GZIP compression enabled
- [ ] Images optimized
- [ ] Model caching implemented
- [ ] Batch processing for ML
- [ ] GPU acceleration enabled
- [ ] Load testing baseline established
- [ ] Performance monitoring alerts configured
- [ ] Scaling strategy documented

---

## Next Steps

- Review [Deployment Guide](deployment.md)
- Check [Monitoring Guide](monitoring.md)
- Read [Security Guide](security.md)
