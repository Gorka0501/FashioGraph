"""
Centralized Storage Configuration
Manages images, sessions, cache, and data storage across the application.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from enum import Enum
import json
from datetime import datetime


class StorageType(Enum):
    """Storage location types."""
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class StorageConfig:
    """
    Centralized storage configuration for the fashion wardrobe app.
    Handles all file storage paths and configurations.
    """

    # Environment variable overrides
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
    STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", Path.home() / ".fashion_wardrobe_app"))

    # ============================================================================
    # IMAGE STORAGE
    # ============================================================================
    IMAGES_DIR = STORAGE_ROOT / "images"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Image subdirectories (organized by username - each user has ONE wardrobe)
    # Image settings
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}

    # ============================================================================
    # SESSION STORAGE
    # ============================================================================
    SESSION_DIR = STORAGE_ROOT / "sessions"
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Session settings
    SESSION_TIMEOUT = 31 * 24 * 60 * 60  # 31 days in seconds (2,678,400 seconds)
    SESSION_CLEAN_INTERVAL = 24 * 60 * 60  # Check once per day
    MAX_SESSION_SIZE = 10 * 1024 * 1024  # 10MB per session

    # ============================================================================
    # MODEL STORAGE (ONLY PERSONAL MODELS)
    # ============================================================================
    MODELS_DIR = STORAGE_ROOT / "models"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # User personal models (one per user)
    PERSONAL_MODELS_DIR = MODELS_DIR / "personal"
    PERSONAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Model name in user's directory
    PERSONAL_MODEL_FILE = "personal_model.pt"

    # ============================================================================
    # CLASS METHODS
    # ============================================================================

    @classmethod
    def get_user_image_dir(cls, username: str) -> Path:
        """Get directory for user's wardrobe images (one wardrobe per user)."""
        user_dir = cls.IMAGES_DIR / username
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @classmethod
    def get_user_session_file(cls, username: str) -> Path:
        """Get session file path for user."""
        return cls.SESSION_DIR / f"{username}.json"

    @classmethod
    def get_user_personal_model_path(cls, username: str) -> Path:
        """Get personal model file path for user."""
        user_model_dir = cls.PERSONAL_MODELS_DIR / username
        user_model_dir.mkdir(parents=True, exist_ok=True)
        return user_model_dir / cls.PERSONAL_MODEL_FILE

    @classmethod
    def get_storage_stats(cls) -> Dict:
        """Get comprehensive storage statistics."""
        def get_dir_size(path: Path) -> int:
            """Calculate total size of directory."""
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

        return {
            "timestamp": datetime.now().isoformat(),
            "storage_root": str(cls.STORAGE_ROOT),
            "storage_type": cls.STORAGE_TYPE,
            "breakdown": {
                "images": {
                    "path": str(cls.IMAGES_DIR),
                    "size_bytes": get_dir_size(cls.IMAGES_DIR),
                    "file_count": len(list(cls.IMAGES_DIR.rglob('*'))) if cls.IMAGES_DIR.exists() else 0,
                },
                "models": {
                    "path": str(cls.MODELS_DIR),
                    "size_bytes": get_dir_size(cls.MODELS_DIR),
                    "file_count": len(list(cls.MODELS_DIR.rglob('*'))) if cls.MODELS_DIR.exists() else 0,
                },
                "sessions": {
                    "path": str(cls.SESSION_DIR),
                    "size_bytes": get_dir_size(cls.SESSION_DIR),
                    "file_count": len(list(cls.SESSION_DIR.rglob('*'))) if cls.SESSION_DIR.exists() else 0,
                },
            },
            "limits": {
                "max_image_size_mb": cls.MAX_IMAGE_SIZE / (1024 * 1024),
                "session_timeout_seconds": cls.SESSION_TIMEOUT,
            },
        }

    @classmethod
    def validate_storage(cls) -> bool:
        """Validate that all storage directories are accessible."""
        try:
            required_dirs = [
                cls.IMAGES_DIR,
                cls.SESSION_DIR,
                cls.MODELS_DIR,
            ]

            for directory in required_dirs:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                if not directory.is_dir():
                    return False

            # Try to write a test file
            test_file = cls.SESSION_DIR / ".storage_test"
            test_file.write_text("test")
            test_file.unlink()

            return True
        except Exception as e:
            print(f"Storage validation failed: {e}")
            return False


# Initialize storage on module load
if __name__ == "__main__":
    print("Storage configuration initialized")
    print(f"Storage root: {StorageConfig.STORAGE_ROOT}")
    print(f"Storage type: {StorageConfig.STORAGE_TYPE}")
    print(f"Images dir: {StorageConfig.IMAGES_DIR}")
    print(f"Sessions dir: {StorageConfig.SESSION_DIR}")
    print(f"Models dir: {StorageConfig.MODELS_DIR}")
