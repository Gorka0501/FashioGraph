# Developer Guide - Storage System

File storage, image management, and data persistence.

## Storage Architecture

### Directory Structure

```
~/.fashion_wardrobe_app/          (Platform-agnostic home directory)
├── images/                        (Item images)
│   └── {username}/
│       ├── {item_id}.jpg
│       ├── {item_id}_thumb.jpg
│       └── ...
├── models/                        (Machine learning models)
│   ├── base/
│   │   ├── hgnn.pth
│   │   ├── clip.pth
│   │   └── resnet50.pth
│   └── personal/
│       └── {username}/
│           ├── hgnn_v1.pth
│           ├── hgnn_v2.pth
│           └── ...
├── sessions/                      (User session data)
│   └── {username}.json
├── logs/                          (Application logs)
│   └── app.log
└── data/                          (Database files)
    └── wardrobes.db
```

### Configuration

**Environment Variable:**
```bash
STORAGE_PATH=~/.fashion_wardrobe_app
```

**Default Paths:**
```python
import os
from pathlib import Path

STORAGE_PATH = Path.home() / ".fashion_wardrobe_app"
IMAGES_PATH = STORAGE_PATH / "images"
MODELS_PATH = STORAGE_PATH / "models"
SESSIONS_PATH = STORAGE_PATH / "sessions"
LOGS_PATH = STORAGE_PATH / "logs"
```

**Cross-Platform Path Resolution:**
```python
# Windows
~/.fashion_wardrobe_app/ → C:\Users\{username}\.fashion_wardrobe_app\

# macOS
~/.fashion_wardrobe_app/ → /Users/{username}/.fashion_wardrobe_app/

# Linux
~/.fashion_wardrobe_app/ → /home/{username}/.fashion_wardrobe_app/
```

---

## Image Storage

### Image Upload Process

```
1. Client Upload
   ↓
2. Receive in Route Handler
   ├─ Validate file type
   ├─ Validate file size (< 5MB)
   └─ Read file bytes
   ↓
3. Image Processing
   ├─ Generate image ID
   ├─ Save original
   ├─ Create thumbnail
   └─ Store metadata
   ↓
4. Database Record
   ├─ Create Item in DB
   ├─ Store image path
   └─ Link to Wardrobe
   ↓
5. Return Response
   └─ Item details with image URL
```

### File Organization

**By User:**
```
images/
├── john_doe/
│   ├── 550e8400-e29b-41d4-a716-446655440000.jpg
│   ├── 550e8400-e29b-41d4-a716-446655440001.jpg
│   └── ...
├── jane_smith/
│   ├── 660f8400-f39b-41d4-b816-556755550000.jpg
│   └── ...
```

**Rationale:**
- Clear user separation
- Easier permission management
- Isolate user data
- Facilitate cleanup on account deletion

### File Naming

**Item Images:**
```
{item_id}.jpg
550e8400-e29b-41d4-a716-446655440000.jpg
```

**Thumbnails:**
```
{item_id}_thumb.jpg
550e8400-e29b-41d4-a716-446655440000_thumb.jpg
```

**Advantages:**
- UUID ensures uniqueness
- No name collisions
- Easy to find/delete
- Maps directly to Item.id

---

### Image Processing

#### Upload Handling

```python
from PIL import Image
import io

async def process_image(file: UploadFile) -> tuple[str, str]:
    """
    Process uploaded image:
    1. Validate format
    2. Check size
    3. Resize for optimization
    4. Generate thumbnail
    5. Save both versions
    """
    
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Invalid image format")
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:  # 5MB
        raise ValueError("File too large")
    
    # Open and process with PIL
    image = Image.open(io.BytesIO(contents))
    
    # Resize to standard size (if needed)
    if image.size[0] > MAX_WIDTH or image.size[1] > MAX_HEIGHT:
        image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
    
    # Create thumbnail
    thumb = image.copy()
    thumb.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
    
    # Save optimized original
    image_path = save_image(image, image_id, username, "jpg", quality=85)
    
    # Save thumbnail
    thumb_path = save_image(thumb, image_id, username, "jpg", quality=80, suffix="_thumb")
    
    return image_path, thumb_path
```

#### Supported Formats

| Format | Extension | Quality | Size |
|--------|-----------|---------|------|
| JPEG | .jpg | 85% (optimized) | ~100-200 KB |
| PNG | .png | Full quality | ~300-500 KB |
| WebP | .webp | 85% (modern) | ~80-150 KB |

#### Optimization Settings

```python
# JPEG compression
image.save(path, format="JPEG", quality=85, optimize=True)

# PNG compression  
image.save(path, format="PNG", compress_level=9)

# WebP (modern browsers)
image.save(path, format="WEBP", quality=85)
```

### Image Retrieval

**Direct Access:**
```python
@app.get("/images/{username}/{item_id}")
async def get_image(username: str, item_id: UUID):
    """Serve image file"""
    image_path = IMAGES_PATH / username / f"{item_id}.jpg"
    return FileResponse(image_path)
```

**Thumbnail Access:**
```python
@app.get("/images/{username}/{item_id}/thumb")
async def get_image_thumb(username: str, item_id: UUID):
    """Serve thumbnail"""
    thumb_path = IMAGES_PATH / username / f"{item_id}_thumb.jpg"
    return FileResponse(thumb_path)
```

### Image Cleanup

**On Item Deletion:**
```python
async def delete_item(item_id: UUID):
    # Remove database record
    db.delete(item)
    db.commit()
    
    # Remove image files
    image_path = IMAGES_PATH / username / f"{item_id}.jpg"
    thumb_path = IMAGES_PATH / username / f"{item_id}_thumb.jpg"
    
    image_path.unlink(missing_ok=True)
    thumb_path.unlink(missing_ok=True)
```

**On User Deletion:**
```python
async def delete_user(user_id: UUID):
    user = db.get(User, user_id)
    username = user.username
    
    # Remove user's image directory
    user_images = IMAGES_PATH / username
    shutil.rmtree(user_images, ignore_errors=True)
    
    # Delete from database
    db.delete(user)
    db.commit()
```

---

## Model Storage

### Base Models

**Location:**
```
models/base/
├── hgnn.pth          (HGNN model - 45 MB)
├── clip.pth          (CLIP model - 340 MB)
└── resnet50.pth      (ResNet50 model - 98 MB)
```

**Loading:**
```python
import torch
from pathlib import Path

MODELS_PATH = Path.home() / ".fashion_wardrobe_app" / "models"

# Load model on startup
def load_hgnn():
    model_path = MODELS_PATH / "base" / "hgnn.pth"
    model = torch.load(model_path, map_location="cpu")
    model.eval()  # Inference mode
    return model

# Cache loaded models
_models_cache = {}

def get_hgnn():
    if "hgnn" not in _models_cache:
        _models_cache["hgnn"] = load_hgnn()
    return _models_cache["hgnn"]
```

### Personal Models

**Location:**
```
models/personal/{username}/
├── hgnn_v1.pth       (First training - Date)
├── hgnn_v2.pth       (Second training - Date)
└── hgnn_v3.pth       (Latest version)
```

**Versioning Strategy:**
```python
def get_latest_model(username: str):
    """Get user's latest personal model"""
    user_models = MODELS_PATH / "personal" / username
    
    # Find all model files
    models = list(user_models.glob("hgnn_v*.pth"))
    
    if not models:
        # No personal model, use base
        return get_hgnn()
    
    # Get highest version number
    latest = sorted(models)[-1]
    return torch.load(latest, map_location="cpu")
```

**Training & Saving:**
```python
def save_personal_model(username: str, model: torch.nn.Module):
    """Save trained personal model with versioning"""
    user_models_dir = MODELS_PATH / "personal" / username
    user_models_dir.mkdir(parents=True, exist_ok=True)
    
    # Get next version number
    existing = list(user_models_dir.glob("hgnn_v*.pth"))
    next_version = len(existing) + 1
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = user_models_dir / f"hgnn_v{next_version}_{timestamp}.pth"
    
    torch.save({
        "model_state": model.state_dict(),
        "version": next_version,
        "timestamp": timestamp,
        "accuracy": metrics["accuracy"],
        "loss": metrics["loss"]
    }, model_path)
    
    return model_path
```

### Cleanup

**Delete Old Models:**
```python
def cleanup_old_models(username: str, keep_count: int = 3):
    """Keep only recent N versions"""
    user_models = MODELS_PATH / "personal" / username
    models = sorted(user_models.glob("hgnn_v*.pth"))
    
    if len(models) > keep_count:
        for old_model in models[:-keep_count]:
            old_model.unlink()
```

---

## Session Storage

### Session Files

**Location:**
```
sessions/{username}.json
```

**Purpose:**
- Store current user session
- Persist across restarts (optional)
- Track login/logout

**Format:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_expires": "2024-01-02T10:00:00Z",
  "login_time": "2024-01-01T10:00:00Z",
  "last_activity": "2024-01-01T14:30:00Z",
  "device": "desktop",
  "ip_address": "192.168.1.100"
}
```

### Session Management

```python
import json
from datetime import datetime, timedelta

async def create_session(user_id: UUID, username: str, access_token: str):
    """Create session file"""
    session_data = {
        "user_id": str(user_id),
        "username": username,
        "access_token": access_token,
        "token_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "login_time": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }
    
    session_path = SESSIONS_PATH / f"{username}.json"
    with open(session_path, "w") as f:
        json.dump(session_data, f, indent=2)

async def get_session(username: str):
    """Load session file"""
    session_path = SESSIONS_PATH / f"{username}.json"
    if not session_path.exists():
        return None
    
    with open(session_path, "r") as f:
        return json.load(f)

async def delete_session(username: str):
    """Remove session file"""
    session_path = SESSIONS_PATH / f"{username}.json"
    session_path.unlink(missing_ok=True)
```

---

## Logging

### Log File

**Location:**
```
logs/app.log
```

**Configuration:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Configure logging
handler = RotatingFileHandler(
    LOGS_PATH / "app.log",
    maxBytes=10_000_000,  # 10 MB
    backupCount=5  # Keep 5 files
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Log Rotation

Logs are automatically rotated:
- Max size per file: 10 MB
- Backup files: 5 (app.log.1, app.log.2, etc.)
- Cleanup: Oldest files deleted automatically

---

## File Permissions

### Linux/macOS

```bash
# Directory permissions
chmod 700 ~/.fashion_wardrobe_app/          # Owner only
chmod 700 ~/.fashion_wardrobe_app/images/
chmod 700 ~/.fashion_wardrobe_app/models/

# File permissions
chmod 600 ~/.fashion_wardrobe_app/data/*.db  # Owner read/write only
```

### Windows

```powershell
# Inherited permissions from user profile
# No special configuration needed
```

---

## Database File Storage

### SQLite Database

**Location:**
```
data/wardrobes.db
```

**Size Management:**
```python
import os

# Get database size
db_size = os.path.getsize("data/wardrobes.db")
print(f"Database size: {db_size / 1024 / 1024:.2f} MB")
```

### Backup Strategy

**Automatic Backup:**
```python
import shutil
from datetime import datetime

def backup_database():
    """Create database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    source = STORAGE_PATH / "data" / "wardrobes.db"
    backup = STORAGE_PATH / "data" / f"wardrobes_backup_{timestamp}.db"
    
    shutil.copy2(source, backup)
    
    # Keep only last 5 backups
    backups = sorted(STORAGE_PATH.glob("data/wardrobes_backup_*.db"))
    for old_backup in backups[:-5]:
        old_backup.unlink()
```

---

## Storage Cleanup

### Removing User Data

**Complete Cleanup:**
```python
async def delete_user_all_data(username: str):
    """Remove all user data"""
    
    # Remove images
    images = IMAGES_PATH / username
    shutil.rmtree(images, ignore_errors=True)
    
    # Remove personal models
    models = MODELS_PATH / "personal" / username
    shutil.rmtree(models, ignore_errors=True)
    
    # Remove session
    session = SESSIONS_PATH / f"{username}.json"
    session.unlink(missing_ok=True)
    
    # Remove from database (done separately)
    db.delete(user)
    db.commit()
```

### Orphaned Files Cleanup

```python
def cleanup_orphaned_files():
    """Remove files for deleted users"""
    
    # Get all users in database
    users = db.query(User).all()
    usernames = {u.username for u in users}
    
    # Clean images
    for user_dir in IMAGES_PATH.iterdir():
        if user_dir.name not in usernames:
            shutil.rmtree(user_dir)
    
    # Clean models
    for user_dir in (MODELS_PATH / "personal").iterdir():
        if user_dir.name not in usernames:
            shutil.rmtree(user_dir)
    
    # Clean sessions
    for session_file in SESSIONS_PATH.glob("*.json"):
        username = session_file.stem
        if username not in usernames:
            session_file.unlink()
```

---

## Performance Optimization

### Image Optimization Tips

```python
# Resize large images during upload
image.thumbnail((1920, 1920), Image.LANCZOS)

# Compress JPEG aggressively
image.save(path, quality=85)

# Use lazy loading in frontend
<img src="..." loading="lazy" />
```

### Storage Monitoring

```python
import os

def get_storage_stats():
    """Get storage usage"""
    
    def dir_size(path):
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += dir_size(entry)
        return total
    
    return {
        "images": dir_size(IMAGES_PATH) / 1024 / 1024,  # MB
        "models": dir_size(MODELS_PATH) / 1024 / 1024,
        "database": os.path.getsize(STORAGE_PATH / "data" / "wardrobes.db") / 1024 / 1024,
        "logs": dir_size(LOGS_PATH) / 1024 / 1024
    }
```

---

## Future Improvements

**Planned Enhancements:**
- ☁️ Cloud storage integration (S3, Google Cloud)
- 🗜️ Advanced image compression (WebP optimization)
- 📊 Storage quota per user
- 🔐 Encryption for sensitive files
- 🌐 CDN integration for image delivery
- 📈 Automated cleanup policies

---

## Next Steps

- Learn about [Database](database.md)
- Explore [Authentication](authentication.md)
- Read [Machine Learning](machine-learning.md)
