# Administration Guide - Deployment

Production deployment procedures and best practices.

## Deployment Overview

### Deployment Architectures

**Development:**
- Single server with debug mode
- In-memory SQLite database (optional)
- Hot reloading enabled

**Production:**
- Multiple Uvicorn workers
- PostgreSQL database
- Reverse proxy (Nginx)
- SSL/TLS encryption
- Process manager (Systemd/Supervisor)

### Pre-deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrated and tested
- [ ] Static files collected
- [ ] Secrets secure and not in code
- [ ] Dependencies installed
- [ ] Tests passing
- [ ] Logging configured
- [ ] Backups automated
- [ ] Monitoring setup
- [ ] Security headers configured

---

## Uvicorn Server Setup

### Basic Uvicorn Command

```bash
# Single worker
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Production setup (multiple workers)
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout-keep-alive 30 \
  --timeout-notify 30
```

### Uvicorn Configuration File

**File:** `uvicorn_config.py`

```python
"""Uvicorn configuration"""
import multiprocessing

# Server configuration
host = "0.0.0.0"
port = 8000

# Worker configuration
workers = multiprocessing.cpu_count()  # 1 worker per CPU
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout configuration
timeout_keep_alive = 30
timeout_notify = 30
timeout_graceful_shutdown = 30

# Logging
log_config = "uvicorn_log_config.yaml"
access_log = True

# Performance
loop = "uvloop"  # Fast event loop
http = "h11"     # HTTP implementation
```

**Launch:**

```bash
uvicorn app.main:app --config-path ./uvicorn_config.py
```

---

## Systemd Service

### Service File

**File:** `/etc/systemd/system/fashion-app.service`

```ini
[Unit]
Description=Fashion Wardrobe Application
After=network.target

[Service]
Type=notify
User=fashion
WorkingDirectory=/opt/fashion-app

# Environment variables
EnvironmentFile=/opt/fashion-app/.env.production
Environment="PATH=/opt/fashion-app/venv/bin"

# Start command
ExecStart=/opt/fashion-app/venv/bin/uvicorn \
  app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4

# Restart policy
Restart=on-failure
RestartSec=10

# Resource limits
LimitNOFILE=65535
LimitNPROC=65535

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Managing the Service

```bash
# Enable service
sudo systemctl enable fashion-app

# Start service
sudo systemctl start fashion-app

# Check status
sudo systemctl status fashion-app

# View logs
sudo journalctl -u fashion-app -f

# Restart
sudo systemctl restart fashion-app

# Stop
sudo systemctl stop fashion-app
```

---

## Nginx Reverse Proxy

### Nginx Configuration

**File:** `/etc/nginx/sites-available/fashion-app`

```nginx
upstream fashion_backend {
    # Load balance across multiple Uvicorn workers
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name fashion.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name fashion.example.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/fashion.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fashion.example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;
    
    # Logging
    access_log /var/log/nginx/fashion_access.log;
    error_log /var/log/nginx/fashion_error.log;
    
    # Proxy settings
    location / {
        proxy_pass http://fashion_backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # File upload size
    client_max_body_size 100M;
}
```

### Enable Configuration

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fashion-app /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS with Let's Encrypt

### Setup with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d fashion.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Manual renewal
sudo certbot renew

# Check certificate
sudo certbot certificates
```

### SSL Configuration Best Practices

```nginx
# Modern SSL configuration (Mozilla recommendations)
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Build stage
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application
COPY app/ ./app/
COPY .env.production .env

# Create non-root user
RUN useradd -m -u 1000 fashion && chown -R fashion:fashion /app
USER fashion

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: fashion_db
      POSTGRES_USER: fashion
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - fashion-network
    restart: unless-stopped

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://fashion:${DB_PASSWORD}@db:5432/fashion_db
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "false"
    ports:
      - "8000:8000"
    depends_on:
      - db
    networks:
      - fashion-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - fashion-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  fashion-network:
    driver: bridge
```

### Deploy Docker

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f app

# Stop
docker-compose down
```

---

## Database Migration

### PostgreSQL Migration

```bash
# Install PostgreSQL client
sudo apt-get install postgresql-client

# Create database
createdb -h localhost -U fashion fashion_db

# Set up SQLAlchemy with PostgreSQL
export DATABASE_URL="postgresql://fashion:password@localhost/fashion_db"

# Alembic migration (if used)
alembic upgrade head

# Or manual migration
python -c "from app.backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Database Backup

```bash
# Backup
pg_dump -h localhost -U fashion fashion_db > backup.sql

# Restore
psql -h localhost -U fashion fashion_db < backup.sql
```

---

## Performance Optimization

### Worker Count

```python
# Optimal worker count
import multiprocessing
workers = (multiprocessing.cpu_count() * 2) + 1
```

### Connection Pooling

```python
# SQLAlchemy engine with connection pool
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30
)
```

### Caching Headers

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware

app = FastAPI()

# GZIP compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Cache middleware
from fastapi.middleware.base import BaseHTTPMiddleware

class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response

app.add_middleware(CacheMiddleware)
```

---

## Monitoring & Logs

### Logging Configuration

```bash
# Create log directory
mkdir -p /var/log/fashion-app

# Set permissions
chmod 755 /var/log/fashion-app
chown fashion:fashion /var/log/fashion-app
```

### Log Rotation

**File:** `/etc/logrotate.d/fashion-app`

```
/var/log/fashion-app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 fashion fashion
    sharedscripts
    postrotate
        systemctl reload fashion-app > /dev/null 2>&1 || true
    endscript
}
```

---

## Environment Configuration

### Production .env

```bash
# Server
DEBUG=false
SECRET_KEY=your-very-secret-key-here

# Database
DATABASE_URL=postgresql://fashion:password@db.example.com/fashion_db

# Storage
STORAGE_PATH=/mnt/storage/.fashion_wardrobe_app

# Authentication
TOKEN_EXPIRY=3600
REFRESH_TOKEN_EXPIRY=2592000

# ML Models
ENABLE_GPU=true
MODEL_CACHE_PATH=/opt/models

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=secret
```

---

## Health Checks

### Health Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check (includes dependencies)"""
    try:
        # Check database
        db.query(User).limit(1).all()
        
        # Check storage
        storage_path.exists()
        
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
```

---

## Rollback Procedures

### Blue-Green Deployment

```bash
# Current (blue) on port 8000
# New (green) on port 8001

# Start new version
uvicorn app.main:app --port 8001 &

# Test new version
curl http://localhost:8001/health

# Switch Nginx
# Edit nginx.conf to point to 8001

# Reload Nginx
sudo nginx -s reload

# If issues, revert to port 8000
```

---

## Security Best Practices

- Use environment variables for secrets
- Enable HTTPS only
- Set security headers
- Regular security updates
- Database backups
- Monitor access logs
- Rate limiting
- SQL injection prevention (use ORM)

See [Security Guide](security.md) for detailed security practices.

---

## Next Steps

- Review [Configuration](configuration.md)
- Read [Monitoring](monitoring.md)
- Explore [Backup & Recovery](backup-recovery.md)
