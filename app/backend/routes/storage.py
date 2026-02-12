"""Storage orchestration and image streaming routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.backend.database import get_db, User, Item, Wardrobe
from app.backend.schemas import StorageSyncPlan, CacheReportRequest
from app.utils.auth_utils import get_current_user
from app.models.user_preference_learner import get_preference_learner_manager
from app.backend.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])


# ==================== Storage Orchestration ====================

@router.get("/sync", response_model=StorageSyncPlan)
async def get_storage_sync_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Backend tells desktop what to cache.
    Checks what user needs and returns sync plan.
    """
    try:
        sync_plan = {
            "model": None,
            "images": None,
            "message": "Sync plan ready"
        }
        
        # Check if user has a trained model available
        preference_manager = get_preference_learner_manager()
        learner = preference_manager.get_learner(user.username)
        
        if learner and learner.user_model:
            # User has a trained model - desktop should download it
            sync_plan["model"] = {
                "action": "keep_cached",
                "status": "available",
                "message": "Personal model is ready to use"
            }
        else:
            # No personal model - use base
            sync_plan["model"] = {
                "action": "none",
                "status": "using_base",
                "message": "Using base model, no personal model yet"
            }
        
        # Check which images user has
        user_items = db.query(Item).filter(Item.wardrobe_id == user.wardrobe_id).all()
        if user_items:
            sync_plan["images"] = {
                "action": "sync_needed",
                "status": "partial",
                "item_count": len(user_items),
                "message": f"User has {len(user_items)} items in wardrobe"
            }
        else:
            sync_plan["images"] = {
                "action": "none",
                "status": "empty",
                "message": "No items in wardrobe yet"
            }
        
        logger.info(f"📊 Storage sync plan created - User: {user.username}")
        return StorageSyncPlan(**sync_plan)
    
    except Exception as e:
        logger.error(f"❌ Error creating sync plan - User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating sync plan: {str(e)}")


@router.get("/config")
def get_storage_config(user: User = Depends(get_current_user)):
    """
    Get storage configuration paths for the current user.
    Frontend uses this to know where to store/retrieve user data.
    """
    from app.backend.storage_config import StorageConfig
    
    return {
        "storage_root": str(StorageConfig.STORAGE_ROOT),
        "images_dir": str(StorageConfig.IMAGES_DIR),
        "personal_models_dir": str(StorageConfig.PERSONAL_MODELS_DIR),
        "sessions_dir": str(StorageConfig.SESSION_DIR),
        "user_image_dir": str(StorageConfig.get_user_image_dir(user.username)),
        "user_personal_model_path": str(StorageConfig.get_user_personal_model_path(user.username)),
        "user_session_file": str(StorageConfig.get_user_session_file(user.username)),
    }


@router.post("/cache-report")
async def report_cache_status(
    report: CacheReportRequest,
    user: User = Depends(get_current_user)
):
    """Desktop reports what's cached locally."""
    try:
        logger.info(
            f"💾 Cache report received - User: {user.username}, "
            f"Model cached: {report.cached_model}, "
            f"Images: {report.cached_image_count}, "
            f"Size: {report.total_cache_size_mb:.1f}MB"
        )
        
        return {
            "success": True,
            "message": "Cache status recorded",
            "cached_model": report.cached_model,
            "cached_images": report.cached_image_count
        }
    except Exception as e:
        logger.error(f"❌ Error recording cache report - User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error recording cache: {str(e)}")
