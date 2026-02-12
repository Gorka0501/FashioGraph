# Administration Guide - Monitoring

Logging, metrics, and application health monitoring.

## Monitoring Overview

### Key Metrics to Monitor

- **Application Health:** Uptime, response times, error rates
- **Database:** Query performance, connection pool usage, data integrity
- **System:** CPU, memory, disk usage, network I/O
- **User Activity:** Login attempts, API usage, file uploads
- **Models:** Training progress, prediction accuracy, latency

### Monitoring Stack

```
Application Logs → Log Aggregation → Visualization → Alerting
System Metrics  → Prometheus      → Grafana        → Email/Slack
```

---

## Logging System

### Log Files Location

```
/var/log/fashion-app/
├── app.log           # General application logs
├── error.log         # Errors only
├── access.log        # API access logs
└── audit.log         # User actions (logins, uploads)
```

### Log Levels

```python
DEBUG    # Detailed diagnostic information
INFO     # Confirmation that operations are working
WARNING  # Warning about potential issues
ERROR    # Error occurred but system continues
CRITICAL # Critical error, system may be unusable
```

### Logging Configuration

**File:** `logging_config.py`

```python
"""Logging configuration"""
import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path("/var/log/fashion-app")
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        },
        "json": {
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 10,
            "formatter": "detailed",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "level": "ERROR",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detailed",
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
            "handlers": ["file"],
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file", "error_file"],
    },
}

import logging.config
logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
```

### Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)

# Usage
logger = logging.getLogger(__name__)
logger.info("User login", extra={"user_id": 123, "request_id": "abc-123"})
```

---

## Health Checks

### Health Check Endpoints

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.backend.database import get_db

app = FastAPI()

@app.get("/health")
async def health():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """Readiness check (includes dependencies)"""
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check storage
        from pathlib import Path
        storage_path = Path("~/.fashion_wardrobe_app").expanduser()
        if not storage_path.exists():
            return {"status": "not_ready", "error": "Storage not accessible"}, 503
        
        # Check models
        from app.models.load_models import get_models
        models = get_models()
        if not models:
            return {"status": "not_ready", "error": "Models not loaded"}, 503
        
        return {"status": "ready"}
    
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503

@app.get("/health/live")
async def liveness():
    """Liveness check (just confirm app is running)"""
    return {"status": "alive"}
```

### Health Check Monitoring

```bash
# Monitor health every 30 seconds
watch -n 30 'curl -s http://localhost:8000/health/ready | jq .'

# In Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1
```

---

## Metrics & Observability

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()

# Define metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'app_active_connections',
    'Active connections'
)

model_inference_time = Histogram(
    'app_model_inference_seconds',
    'Model inference time',
    ['model_name']
)

# Middleware to track metrics
from fastapi.middleware.base import BaseHTTPMiddleware
from time import time

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time()
        
        response = await call_next(request)
        
        duration = time() - start_time
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        return response

app.add_middleware(MetricsMiddleware)

# Expose metrics
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Model Metrics

```python
from prometheus_client import Histogram, Counter

# Training metrics
training_duration = Histogram(
    'app_training_duration_seconds',
    'Model training duration',
    ['user_id']
)

training_loss = Histogram(
    'app_training_loss',
    'Training loss',
    ['user_id']
)

predictions_made = Counter(
    'app_predictions_total',
    'Total predictions made',
    ['model_type']
)

# Usage
with training_duration.labels(user_id=user_id).time():
    # Train model
    loss = train_model(user_id)
    training_loss.labels(user_id=user_id).observe(loss)
```

---

## Grafana Dashboards

### Prometheus Data Source

```yaml
# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fashion-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Sample Dashboard Queries

```promql
# Request rate
rate(app_requests_total[5m])

# Error rate
rate(app_requests_total{status=~"5.."}[5m])

# Average response time
rate(app_request_duration_seconds_sum[5m]) /
rate(app_request_duration_seconds_count[5m])

# Model inference time
histogram_quantile(0.95, rate(app_model_inference_seconds_bucket[5m]))
```

---

## Log Aggregation

### ELK Stack Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000/udp"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Logstash Configuration

```
# logstash.conf
input {
  file {
    path => "/var/log/fashion-app/*.log"
    start_position => "beginning"
  }
}

filter {
  grok {
    match => {
      "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{DATA:logger} - %{LOGLEVEL:level} - %{GREEDYDATA:message}"
    }
  }
  
  mutate {
    convert => { "timestamp" => "string" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "fashion-app-%{+YYYY.MM.dd}"
  }
}
```

---

## Alerting

### Alert Rules

**File:** `prometheus_alerts.yml`

```yaml
groups:
  - name: fashion_app
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (sum(rate(app_requests_total{status=~"5.."}[5m])) by (job)) >
          0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # Database unavailable
      - alert: DatabaseUnavailable
        expr: |
          up{job="database"} == 0
        for: 1m
        annotations:
          summary: "Database is unavailable"
      
      # High latency
      - alert: HighLatency
        expr: |
          (histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m]))) > 1
        for: 5m
        annotations:
          summary: "High API latency"
          description: "P95 latency is {{ $value }}s"
```

### Email Alerting

```python
# Alert handler
import smtplib
from email.mime.text import MIMEText

def send_alert(alert_title: str, alert_message: str):
    """Send email alert"""
    msg = MIMEText(alert_message)
    msg['Subject'] = f"[ALERT] {alert_title}"
    msg['From'] = "alerts@example.com"
    msg['To'] = "ops@example.com"
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("alerts@example.com", "app_password")
        server.send_message(msg)
```

### Slack Integration

```python
import requests

def send_slack_alert(message: str, color: str = "danger"):
    """Send alert to Slack"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": "Fashion App Alert",
                "text": message,
                "ts": int(time.time()),
            }
        ]
    }
    
    requests.post(webhook_url, json=payload)
```

---

## Database Monitoring

### Query Performance

```sql
-- Slow queries (PostgreSQL)
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Connection Monitoring

```python
# Monitor database connections
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable connection pool monitoring"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# Check pool status
from app.backend.database import engine
pool = engine.pool
print(f"Connections: {pool.checkedout()}/{pool.size()}")
```

---

## Performance Monitoring

### Track Key Operations

```python
import time
import logging

logger = logging.getLogger(__name__)

def track_operation(operation_name: str):
    """Decorator to track operation duration"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(
                    f"{operation_name} completed",
                    extra={
                        "duration_seconds": duration,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"{operation_name} failed",
                    extra={
                        "duration_seconds": duration,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator

# Usage
@track_operation("User Model Training")
def train_user_model(user_id: int):
    pass
```

---

## Monitoring Checklist

- [ ] Logs being written to `/var/log/fashion-app/`
- [ ] Log rotation configured
- [ ] Health check endpoints accessible
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] Alert channels tested (email, Slack)
- [ ] Database queries optimized
- [ ] Slow query log enabled
- [ ] Error rates monitored
- [ ] User activity logged
- [ ] Model training tracked

---

## Next Steps

- Read [Backup & Recovery](backup-recovery.md)
- Review [Security](security.md)
- Check [Deployment](deployment.md)
