"""Machine Learning routes for model information and category data."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from enum import Enum
import uuid
import torch
import io
from datetime import datetime

from app.backend.database import get_db, User
from app.backend.schemas import (
    ItemResponse, TrainingJobResponse, TrainingStatusResponse
)
from app.utils.auth_utils import get_current_user
from app.utils.ml_models import get_models
from app.models.user_preference_learner import get_preference_learner_manager
from app.backend.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/categories")
def get_categories():
    """Get available item categories."""
    try:
        import pandas as pd
        from pathlib import Path
        
        # Get the app/models directory directly
        app_dir = Path(__file__).resolve().parents[2]  # app directory
        model_dir = app_dir / "models"
        
        categories = {
            "main_categories": [],
            "sub_categories": [],
            "categories": [],
            "related_categories": []
        }
        
        # Load main categories
        main_csv = model_dir / "idx2main.csv"
        if main_csv.exists():
            try:
                df = pd.read_csv(main_csv)
                # Convert to list format: each row as [index, name]
                categories["main_categories"] = df.values.tolist()
            except Exception as e:
                print(f"Error loading idx2main.csv: {e}")
        
        # Load sub categories
        sub_csv = model_dir / "idx2sub.csv"
        if sub_csv.exists():
            try:
                df = pd.read_csv(sub_csv)
                categories["sub_categories"] = df.values.tolist()
            except Exception as e:
                print(f"Error loading idx2sub.csv: {e}")
        
        # Load categories
        cat_csv = model_dir / "idx2category.csv"
        if cat_csv.exists():
            try:
                df = pd.read_csv(cat_csv)
                categories["categories"] = df.values.tolist()
            except Exception as e:
                print(f"Error loading idx2category.csv: {e}")
        
        # Load related categories
        rel_csv = model_dir / "idx2related.csv"
        if rel_csv.exists():
            try:
                df = pd.read_csv(rel_csv)
                categories["related_categories"] = df.values.tolist()
            except Exception as e:
                print(f"Error loading idx2related.csv: {e}")
        
        return categories
    except Exception as e:
        print(f"Error in get_categories: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Could not load category mappings",
            "main_categories": [],
            "sub_categories": [],
            "categories": [],
            "related_categories": []
        }


@router.get("/models/status")
def get_models_status():
    """Get ML models availability status."""
    try:
        models = get_models()
        
        available_models = {}
        if models:
            for model_name in models.keys():
                available_models[model_name] = True
        
        return {
            "models_available": len(available_models) > 0,
            "available_models": available_models,
            "total_models": len(available_models)
        }
    except Exception as e:
        return {
            "models_available": False,
            "error": str(e),
            "available_models": {}
        }


@router.get("/embedding-info")
def get_embedding_info():
    """Get information about ML embeddings."""
    return {
        "image_embedding": {
            "model": "FashionCLIP",
            "dimension": 512,
            "description": "Image embedding from FashionCLIP model"
        },
        "attribute_embedding": {
            "model": "AttributeEncoder",
            "dimension": 256,
            "description": "Attribute embedding from category predictions"
        },
        "outfit_scoring": {
            "model": "FashionHyperGraphModel",
            "description": "Outfit compatibility scoring using hypergraph neural network"
        }
    }


@router.get("/tagger-info")
def get_tagger_info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get information about the hierarchical tagger model and user corrections."""
    from app.backend.database import ItemChange
    
    # Count user's corrections
    user_corrections = db.query(ItemChange).filter(
        ItemChange.user_id == user.id,
        ItemChange.is_user_feedback == True
    ).count()
    
    # Count all corrections in system
    total_corrections = db.query(ItemChange).filter(
        ItemChange.is_user_feedback == True
    ).count()
    
    return {
        "model": "HierarchicalTagger",
        "description": "Hierarchical category tagger using embeddings",
        "user_corrections": user_corrections,
        "total_system_corrections": total_corrections,
        "retraining_threshold": 100,
        "ready_for_retraining": total_corrections >= 100
    }


@router.get("/preference-learner-info")
def get_preference_learner_info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get information about the user preference learner model."""
    from app.backend.database import Outfit
    
    # Count user's outfit ratings
    user_ratings = db.query(Outfit).filter(
        Outfit.user_id == user.id,
        Outfit.user_rating.isnot(None)
    ).count()
    
    from app.backend.storage_config import StorageConfig
    return {
        "model": "PreferenceLearnerManager",
        "description": "Per-user outfit preference model training",
        "user_outfit_ratings": user_ratings,
        "training_threshold": 10,
        "ready_for_training": user_ratings >= 10,
        "model_location": str(StorageConfig.get_user_personal_model_path(user.username))
    }


# ==================== In-Memory Training Job Tracking ====================

class JobStatus(str, Enum):
    """Training job status states."""
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingJob:
    """Tracks a background model training job."""
    def __init__(self, job_id: str, username: str):
        self.job_id = job_id
        self.username = username
        self.status = JobStatus.PENDING
        self.progress = 0  # 0-100
        self.message = "Queued for training"
        self.error = None
        self.model_bytes = None
        self.created_at = datetime.now()


# In-memory storage for training jobs (cleared on server restart)
_training_jobs: Dict[str, TrainingJob] = {}


# ==================== Background Training Task ====================

async def _train_model_background(job_id: str, username: str):
    """Background task for training user's personal model."""
    try:
        if job_id not in _training_jobs:
            return
        
        job = _training_jobs[job_id]
        job.status = JobStatus.TRAINING
        job.progress = 10
        job.message = "Starting training..."
        
        logger.info(f"🔄 Starting background training - Job: {job_id}, User: {username}")
        
        # Get preference learner manager
        preference_manager = get_preference_learner_manager()
        
        # Update progress
        job.progress = 30
        job.message = "Retraining model from base..."
        
        # Call the training method
        success, message = preference_manager.retrain_personal_model_from_base(username)
        
        if not success:
            job.status = JobStatus.FAILED
            job.error = message
            job.progress = 100
            job.message = f"Training failed: {message}"
            logger.error(f"❌ Training failed - Job: {job_id}, User: {username}, Error: {message}")
            return
        
        job.progress = 80
        job.message = "Training completed, preparing model for download..."
        
        # Get the trained model and serialize it
        learner = preference_manager.get_learner(username)
        if learner and learner.user_model:
            try:
                model_state = {
                    'model_state_dict': learner.user_model.state_dict(),
                    'architecture': learner.base_model_type,
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'training_batches': len(learner.training_history)
                }
                # Serialize to bytes for download
                model_buffer = io.BytesIO()
                torch.save(model_state, model_buffer)
                model_buffer.seek(0)
                job.model_bytes = model_buffer.getvalue()
                
                job.progress = 100
                job.status = JobStatus.COMPLETED
                job.message = "Training completed successfully! Model ready for download."
                logger.info(f"✅ Training completed - Job: {job_id}, User: {username}")
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = f"Failed to serialize model: {str(e)}"
                job.progress = 100
                job.message = job.error
                logger.error(f"❌ Model serialization failed - Job: {job_id}, Error: {str(e)}")
        else:
            job.status = JobStatus.FAILED
            job.error = "Trained model not found"
            job.progress = 100
            job.message = job.error
            logger.error(f"❌ Trained model not found - Job: {job_id}, User: {username}")
    
    except Exception as e:
        logger.error(f"❌ Background training error - Job: {job_id}, User: {username}, Error: {str(e)}", exc_info=True)
        if job_id in _training_jobs:
            job = _training_jobs[job_id]
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.progress = 100
            job.message = f"Training error: {str(e)}"


# ==================== Async Model Training (Non-Blocking) ====================

@router.post("/model/retrain-async", response_model=TrainingJobResponse)
async def retrain_personal_model_async(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Start async background training of user's personal model.
    Returns immediately with job_id for polling progress.
    """
    try:
        # Create job
        job_id = str(uuid.uuid4())
        job = TrainingJob(job_id, user.username)
        _training_jobs[job_id] = job
        
        logger.info(f"📋 Training job created - Job: {job_id}, User: {user.username}")
        
        # Add background task (will be executed after response is sent)
        background_tasks.add_task(_train_model_background, job_id, user.username)
        
        return TrainingJobResponse(
            job_id=job_id,
            status="pending",
            message="Training queued. Use job_id to check progress."
        )
    except Exception as e:
        logger.error(f"❌ Error creating training job - User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")


@router.post("/model/retrain")
def retrain_personal_model(user: User = Depends(get_current_user)):
    """Retrain user's personal preference model from scratch using base model."""
    try:
        preference_manager = get_preference_learner_manager()
        success, message = preference_manager.retrain_personal_model_from_base(user.username)
        
        logger.info(f"🔄 Retrain result - User: {user.username}, Success: {success}, Message: {message}")
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"status": "success", "message": message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retraining model - User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrain model: {str(e)}")

@router.get("/model/training-status/{job_id}", response_model=TrainingStatusResponse)
async def get_training_status(
    job_id: str,
    user: User = Depends(get_current_user)
):
    """Get the status and progress of a training job."""
    try:
        if job_id not in _training_jobs:
            logger.warning(f"⚠️  Training job not found - Job: {job_id}, User: {user.username}")
            raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")
        
        job = _training_jobs[job_id]
        
        # Verify user owns this job
        if job.username != user.username:
            logger.warning(f"⚠️  Unauthorized access to job - Job: {job_id}, User: {user.username}")
            raise HTTPException(status_code=403, detail="You don't have access to this training job")
        
        return TrainingStatusResponse(
            job_id=job_id,
            status=job.status.value,
            progress=job.progress,
            message=job.message,
            error=job.error
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting training status - Job: {job_id}, User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving training status: {str(e)}")


@router.get("/model/download/{job_id}")
async def download_trained_model(
    job_id: str,
    user: User = Depends(get_current_user)
):
    """
    Download the trained model from a completed training job.
    Returns model as bytes (.pt file).
    """
    try:
        if job_id not in _training_jobs:
            logger.warning(f"⚠️  Training job not found - Job: {job_id}, User: {user.username}")
            raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")
        
        job = _training_jobs[job_id]
        
        # Verify user owns this job
        if job.username != user.username:
            logger.warning(f"⚠️  Unauthorized access to job - Job: {job_id}, User: {user.username}")
            raise HTTPException(status_code=403, detail="You don't have access to this training job")
        
        # Check if training is complete
        if job.status != JobStatus.COMPLETED:
            logger.warning(f"⚠️  Training not complete - Job: {job_id}, Status: {job.status}")
            raise HTTPException(status_code=400, detail=f"Training job status is {job.status.value}, not ready for download")
        
        # Check if model bytes are available
        if not job.model_bytes:
            logger.error(f"❌ Model bytes not available - Job: {job_id}, User: {user.username}")
            raise HTTPException(status_code=500, detail="Model bytes not available")
        
        logger.info(f"📥 Downloading trained model - Job: {job_id}, User: {user.username}, Size: {len(job.model_bytes)} bytes")
        
        # Return as streaming response
        return StreamingResponse(
            iter([job.model_bytes]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=hgnn_model_{user.username}.pt"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading model - Job: {job_id}, User: {user.username}, Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading model: {str(e)}")


@router.delete("/model/reset")
def reset_personal_model(user: User = Depends(get_current_user)):
    """Reset user's personal preference model back to base model."""
    try:
        preference_manager = get_preference_learner_manager()
        success, message = preference_manager.reset_personal_model(user.username)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"status": "success", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset model: {str(e)}")
