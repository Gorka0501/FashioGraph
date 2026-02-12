"""
Fashion Wardrobe Frontend App
Local-first application with backend synchronization
"""

__version__ = "1.0.0"
__author__ = "Fashion Wardrobe Team"

from .config import LocalStorage, APP_HOME, IMAGES_DIR, MODELS_DIR
from .api_client import BackendAPIClient, SyncManager
from .model_manager import PersonaModelManager

__all__ = [
    'LocalStorage',
    'BackendAPIClient',
    'SyncManager',
    'PersonaModelManager',
    'APP_HOME',
    'IMAGES_DIR',
    'MODELS_DIR',
]
