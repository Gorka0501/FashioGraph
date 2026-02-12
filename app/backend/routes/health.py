"""System health check routes."""
from fastapi import APIRouter, Depends
from app.backend.database import User, get_db
from sqlalchemy.orm import Session
from app.utils.auth_utils import get_current_user

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Check system health and ML models availability."""
    from app.backend.storage_config import StorageConfig
    models_available = True
    storage_dir = str(StorageConfig.STORAGE_ROOT)
    
    # Check if models are available
    try:
        from app.models.load_models import load_all_models
        from app.utils.ml_models import get_models
        models = get_models()
        models_available = models is not None and len(models) > 0
    except Exception as e:
        print(f"Models check failed: {e}")
        models_available = False
    
    return {
        "status": "ok" if models_available else "degraded",
        "models_available": models_available,
        "storage_dir": storage_dir
    }

