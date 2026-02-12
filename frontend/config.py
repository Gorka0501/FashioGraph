"""
Frontend App Configuration
Manages connection to backend storage only.

Storage Architecture:
- FRONTEND: No local storage (Streamlit session state only for auth token)
- BACKEND SERVER: ~/.fashion_wardrobe_app/ (images, models, sessions)

The frontend does NOT store anything locally on disk.
All images, models, and sessions are managed by the backend - accessed via API.
Only Streamlit session state stores temporary auth data (in memory).
"""

import os
from pathlib import Path
from typing import Optional, Dict

# Backend API configuration (must be set before using storage)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "30"))

# ============================================================================
# BACKEND STORAGE CONFIG (frontend uses this, does NOT create local folders)
# ============================================================================

class FrontendStorageConfig:
    """Frontend storage configuration - manages ONLY backend storage paths.
    
    This class only handles backend storage configuration - paths to images,
    models, and sessions stored on the backend server.
    
    The frontend does NOT store anything locally on disk.
    Authentication is stored only in Streamlit session state (memory).
    """
    
    # Backend storage paths (fetched from API)
    _backend_storage_config: Optional[Dict[str, str]] = None
    
    @staticmethod
    def init_storage():
        """No-op for frontend - backend manages all storage"""
        pass
    
    @staticmethod
    def set_backend_config(config: Dict[str, str]):
        """
        Set backend storage configuration (called after fetching from API).
        
        Args:
            config: Dictionary with storage paths from backend
        """
        FrontendStorageConfig._backend_storage_config = config
    
    @staticmethod
    def get_backend_config() -> Optional[Dict[str, str]]:
        """Get cached backend storage configuration"""
        return FrontendStorageConfig._backend_storage_config
    
    @staticmethod
    def get_user_image_dir() -> Optional[Path]:
        """Get user's image directory from backend config"""
        if FrontendStorageConfig._backend_storage_config:
            path_str = FrontendStorageConfig._backend_storage_config.get("user_image_dir")
            return Path(path_str) if path_str else None
        return None
    
    @staticmethod
    def get_user_personal_model_path() -> Optional[Path]:
        """Get user's personal model path from backend config"""
        if FrontendStorageConfig._backend_storage_config:
            path_str = FrontendStorageConfig._backend_storage_config.get("user_personal_model_path")
            return Path(path_str) if path_str else None
        return None
    
    @staticmethod
    def get_user_session_file() -> Optional[Path]:
        """Get user's session file path from backend config"""
        if FrontendStorageConfig._backend_storage_config:
            path_str = FrontendStorageConfig._backend_storage_config.get("user_session_file")
            return Path(path_str) if path_str else None
        return None


# ============================================================================
# APP CONFIGURATION (Frontend only - no local storage)
# ============================================================================

# App settings
APP_TITLE = "👗 Fashion Wardrobe Manager"
APP_ICON = "👗"
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']

# Session configuration
SESSION_TIMEOUT = 3600  # 1 hour in seconds
AUTO_SYNC_INTERVAL = 300  # 5 minutes in seconds

# Embedding model name (frontend uses this when processing images)
EMBEDDING_MODEL_NAME = "fashion-clip"
