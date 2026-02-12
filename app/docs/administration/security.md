# Administration Guide - Security

Security hardening and best practices.

## Security Overview

### Security Principles

1. **Least Privilege** - Users only get necessary permissions
2. **Defense in Depth** - Multiple layers of security
3. **Fail Secure** - Deny by default, allow explicitly
4. **Keep It Simple** - Complex security is hard to maintain
5. **Update Regularly** - Patch vulnerabilities promptly

### Security Checklist

- [ ] HTTPS/TLS enabled
- [ ] Secrets not in code
- [ ] Dependencies updated
- [ ] Database encrypted
- [ ] Access logs enabled
- [ ] Rate limiting configured
- [ ] SQL injection prevention
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Regular security audits

---

## HTTPS/TLS Configuration

### SSL Certificate

```bash
# Generate certificate with Let's Encrypt
certbot certonly --standalone -d fashion.example.com

# Auto-renewal
certbot renew --dry-run
sudo systemctl enable certbot.timer

# Check certificate expiration
certbot certificates
```

### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name fashion.example.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/fashion.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fashion.example.com/privkey.pem;
    
    # Strong ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Session configuration
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name fashion.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Authentication & Authorization

### Password Policy

```python
# Enforce strong passwords
PASSWORD_REQUIREMENTS = {
    "min_length": 12,           # At least 12 characters
    "require_uppercase": True,  # At least one uppercase
    "require_lowercase": True,  # At least one lowercase
    "require_digits": True,     # At least one digit
    "require_special": True,    # At least one special char
}

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 12:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()" for c in password):
        return False
    return True
```

### JWT Security

```python
from datetime import timedelta
from fastapi import HTTPException

# Token configuration
TOKEN_EXPIRY = timedelta(hours=1)  # Short-lived tokens
REFRESH_TOKEN_EXPIRY = timedelta(days=30)

# JWT creation
def create_access_token(data: dict) -> str:
    """Create JWT token with short expiry"""
    from app.backend.security import create_access_token
    
    expires_delta = TOKEN_EXPIRY
    return create_access_token(data, expires_delta)

# Token validation
def verify_token(token: str) -> dict:
    """Verify and decode token"""
    try:
        from app.backend.security import verify_token as verify
        return verify(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Session Management

```python
# Session timeout configuration
SESSION_TIMEOUT = 3600  # 1 hour
ABSOLUTE_TIMEOUT = 86400  # 24 hours (regardless of activity)

# Invalidate old sessions
def cleanup_old_sessions():
    """Remove expired sessions"""
    from app.backend.session_manager import SessionManager
    
    manager = SessionManager()
    manager.cleanup_expired()
```

---

## Secrets Management

### Never Commit Secrets

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.*.local" >> .gitignore
echo "*.key" >> .gitignore
echo "private_key.pem" >> .gitignore
```

### Environment Variables

```python
# Load from environment only
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
if not DATABASE_PASSWORD:
    raise ValueError("DATABASE_PASSWORD environment variable not set")
```

### Use Secrets Manager

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id fashion-app-secrets

# Or use HashiCorp Vault
vault read secret/data/fashion-app
```

### Generate Strong Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate database password
openssl rand -base64 32

# Generate API keys
python -c "import uuid; print(str(uuid.uuid4()))"
```

---

## Database Security

### Parameterized Queries (SQL Injection Prevention)

```python
# ✅ Good - Using ORM (SQLAlchemy)
user = db.query(User).filter(User.username == username).first()

# ✅ Good - Using parameterized queries
from sqlalchemy import text
result = db.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": username}
)

# ❌ Bad - String concatenation
query = f"SELECT * FROM users WHERE username = '{username}'"
```

### Database User Permissions

```sql
-- Create limited database user
CREATE USER fashion_app WITH PASSWORD 'strong_password';

-- Grant only needed permissions
GRANT CONNECT ON DATABASE fashion_db TO fashion_app;
GRANT USAGE ON SCHEMA public TO fashion_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashion_app;

-- Restrict specific tables (example)
REVOKE DELETE ON users FROM fashion_app;  -- Can't delete users
```

### Database Encryption

```sql
-- PostgreSQL with pgcrypto
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive columns
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    sensitive_data TEXT ENCRYPTED WITH (algorithm='aes-256-gcm')
);
```

---

## API Security

### Rate Limiting

```python
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address

app = FastAPI()

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis_url="redis://localhost")

# Apply rate limit
from fastapi_limiter.depends import RateLimiter

@app.post("/auth/login")
@app.limiter.limit("5/minute")
async def login(credentials: LoginRequest):
    """5 attempts per minute"""
    pass
```

### Request Validation

```python
from pydantic import BaseModel, validator, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=12)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
```

### CORS Security

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",  # Only specific origins
        "https://www.example.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization"],  # Only needed headers
    expose_headers=["Content-Length"],
    max_age=600,  # 10 minutes
)
```

---

## Security Headers

### Nginx Security Headers

```nginx
# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Enable XSS protection
add_header X-XSS-Protection "1; mode=block" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions Policy (former Feature Policy)
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### FastAPI Security Headers

```python
from fastapi.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## Logging & Audit

### Audit Logging

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

def log_action(user_id: int, action: str, resource: str, details: dict = None):
    """Log user action for audit"""
    audit_logger.info(
        f"User action: {action}",
        extra={
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
    )

# Usage
log_action(user_id=123, action="DELETE", resource="wardrobe", 
           details={"wardrobe_id": 456})
```

### Access Logging

```bash
# Nginx access log format
log_format security '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '"$http_x_forwarded_for"';

access_log /var/log/nginx/fashion_access.log security;
```

### Monitor for Suspicious Activity

```bash
# Find failed login attempts
grep "401" /var/log/fashion-app/access.log | wc -l

# Find unusual traffic patterns
grep -oP '(?<= )[^ ]+$' /var/log/nginx/fashion_access.log | sort | uniq -c | sort -rn

# Monitor for SQL injection attempts
grep -i "union\|select\|insert\|delete\|drop" /var/log/nginx/fashion_access.log
```

---

## File Upload Security

### Validate File Uploads

```python
from pathlib import Path
from fastapi import File, UploadFile
from magic import Magic

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

async def upload_image(file: UploadFile = File(...)):
    """Validate and save uploaded image"""
    
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Read file
    contents = await file.read()
    
    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Check MIME type
    mime = Magic(mime=True)
    mime_type = mime.from_buffer(contents)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid MIME type")
    
    # Save securely
    filename = secure_filename(file.filename)
    filepath = Path(storage_path) / filename
    filepath.write_bytes(contents)
    
    return {"filename": filename}
```

### Prevent Path Traversal

```python
from pathlib import Path
from werkzeug.utils import secure_filename

def safe_join(base_path: str, user_path: str) -> Path:
    """Safely join paths preventing directory traversal"""
    base = Path(base_path).resolve()
    requested = (base / secure_filename(user_path)).resolve()
    
    # Ensure result is within base directory
    if not str(requested).startswith(str(base)):
        raise ValueError("Path traversal detected")
    
    return requested
```

---

## Dependency Security

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade pip
pip list --outdated
pip install -U -r requirements.txt

# Use pip-audit for security scanning
pip install pip-audit
pip-audit
```

### Manage Dependencies

```bash
# Generate requirements with versions
pip freeze > requirements.txt

# Regular security updates
pip install -U pip setuptools wheel
```

---

## Security Monitoring

### Setup Security Alerts

```python
import logging
import smtplib

security_logger = logging.getLogger("security")

def alert_security_team(event: str, details: dict):
    """Alert security team of suspicious activity"""
    
    message = f"""
    SECURITY ALERT
    
    Event: {event}
    Timestamp: {datetime.now()}
    Details: {details}
    
    Please investigate immediately.
    """
    
    # Send email alert
    # or post to Slack webhook
```

### Regular Security Audits

- Code review of security-critical functions
- Dependency vulnerability scans
- Access log analysis
- Database query optimization review
- SSL certificate validation

---

## Compliance

### Data Protection

- GDPR compliance (if EU users)
- CCPA compliance (if California users)
- Data retention policies
- User data export capabilities

### Regular Tasks

- [ ] Monthly: Check for security updates
- [ ] Monthly: Review access logs
- [ ] Quarterly: Security audit
- [ ] Quarterly: Update dependencies
- [ ] Annually: Penetration test

---

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html)
- [Let's Encrypt](https://letsencrypt.org/)

---

## Next Steps

- Review [Performance Guide](performance.md)
- Check [Deployment Guide](deployment.md)
- Read [Monitoring Guide](monitoring.md)
