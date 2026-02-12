"""Outfit management routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import torch

from app.backend.database import get_db, User, Wardrobe, Item, Outfit, OutfitItem
from app.backend.schemas import OutfitResponse
from app.backend.logging_config import get_logger
from app.utils.outfit_generator import generate_outfit_candidates
from app.utils.ml_models import get_models
from app.models.user_preference_learner import get_preference_learner_manager
from app.utils.auth_utils import get_current_user

logger = get_logger(__name__)

# Check if models are available
try:
    from app.models.load_models import load_all_models
    MODELS_AVAILABLE = True
except Exception as e:
    print("⚠️  Models not available:", e)
    MODELS_AVAILABLE = False

router = APIRouter(prefix="/wardrobe", tags=["outfits"])


@router.get("/{wardrobe_id}/outfits", response_model=List[OutfitResponse])
def list_outfits(
    wardrobe_id: int, 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """List top outfits in a wardrobe, sorted by score (highest first)."""
    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    # Sort by system_rating (score) in descending order, limit to top results
    outfits = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe_id).order_by(Outfit.system_rating.desc()).offset(skip).limit(limit).all()
    return [OutfitResponse.model_validate(o) for o in outfits]


@router.post("/{wardrobe_id}/generate-outfits")
def generate_outfits(wardrobe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate outfits from available items in the wardrobe with smart filtering."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    # Get available items in wardrobe with proper category classification
    items = db.query(Item).filter(
        Item.wardrobe_id == wardrobe_id,
        Item.available == True,  # Only available items
        Item.main_category_indices != None  # Must have category assigned
    ).all()
    
    # Filter out items with empty category arrays
    items = [item for item in items if item.main_category_indices and len(item.main_category_indices) > 0]
    
    if len(items) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 available items with proper category classification to generate outfits")
    
    # Get existing outfit item combinations to prevent duplicates
    existing_outfits = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe_id).all()
    existing_item_sets = set()
    for outfit in existing_outfits:
        item_ids = sorted([oi.item_id for oi in outfit.items])
        existing_item_sets.add(tuple(item_ids))
    
    # Get model for scoring - prefer personal model if available, fall back to base model
    models = get_models()
    base_model = models.get("fashion_hypergraph") if models else None
    
    # Try to load user's personal model if it exists
    user_model = None
    model_source = "BASE"
    try:
        preference_manager = get_preference_learner_manager()
        learner = preference_manager.get_learner(user.username)
        
        if learner and learner.user_model is not None:
            user_model = learner.user_model
            model_source = "PERSONAL"
            logger.info(f"🎯 Using PERSONALIZED model for user {user.username}")
        else:
            logger.info(f"📊 Using BASE model for user {user.username} (no personal model yet)")
    except Exception as e:
        logger.warning(f"⚠️  Could not load personal model, using BASE model: {e}")
        model_source = "BASE"
    
    # Use personal model if available, otherwise use base model
    scoring_model = user_model if user_model else base_model
    model_device = next(scoring_model.parameters()).device if scoring_model else torch.device('cpu')
    
    # Generate outfit candidates using utility function with model scoring
    outfit_candidates = generate_outfit_candidates(
        items, 
        existing_item_sets, 
        model=scoring_model,
        device=model_device,
        max_outfits=100
    )
    
    # Save outfits to database
    final_count = 0
    for item_ids, score, item_objects in outfit_candidates:
        if final_count >= 1000:
            break
        
        # Create outfit
        outfit = Outfit(
            wardrobe_id=wardrobe_id,
            user_id=user.id,
            system_rating=score
        )
        db.add(outfit)
        db.flush()
        
        # Add items to outfit
        for item in item_objects:
            outfit_item = OutfitItem(outfit_id=outfit.id, item_id=item.id)
            db.add(outfit_item)
        
        final_count += 1
    
    db.commit()
    logger.info(f"✨ Generated {final_count} outfits using {model_source} model (scores: {[round(s, 3) for _, s, _ in outfit_candidates[:5]]}...)")
    
    return {"count": final_count, "message": f"Generated {final_count} high-quality outfit(s)"}


@router.get("/{wardrobe_id}/outfits/{outfit_id}", response_model=OutfitResponse)
def get_outfit(wardrobe_id: int, outfit_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific outfit."""
    outfit = db.query(Outfit).filter(
        Outfit.id == outfit_id,
        Outfit.wardrobe_id == wardrobe_id,
        Outfit.user_id == user.id
    ).first()
    
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    
    return OutfitResponse.model_validate(outfit)


@router.post("/{wardrobe_id}/outfits/{outfit_id}/rate")
def rate_outfit(
    wardrobe_id: int,
    outfit_id: int,
    rating: float = Query(..., ge=0, le=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate an outfit from 0-1 and trigger personalized model training every 10 ratings."""
    logger.info(f"📥 Rating received for outfit {outfit_id}: {rating} from user {user.username}")
    
    outfit = db.query(Outfit).filter(
        Outfit.id == outfit_id,
        Outfit.wardrobe_id == wardrobe_id,
        Outfit.user_id == user.id
    ).first()
    
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    
    # Store rating as-is (already normalized 0-1 from frontend)
    outfit.user_rating = rating
    outfit.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"📊 Rating stored in DB for outfit {outfit_id}")
    
    # Trigger personalized model training every 10 user ratings
    try:
        learner_manager = get_preference_learner_manager()
        logger.info(f"📢 Learner manager obtained: {learner_manager is not None}")
        if learner_manager:
            # Save rating to user's preference learner
            # Convert outfit to tensor format for the learner
            outfit_items = db.query(Item).join(OutfitItem).filter(OutfitItem.outfit_id == outfit_id).all()
            if outfit_items and len(outfit_items) >= 2:
                # Create embedding tensor from items - concatenate clip + attr
                clip_embeddings = []
                attr_embeddings = []
                for item in outfit_items:
                    # Get CLIP embedding (img_embedding, 512 dims)
                    if item.img_embedding:
                        clip_embeddings.append(torch.tensor(item.img_embedding, dtype=torch.float32))
                    else:
                        clip_embeddings.append(torch.zeros(512, dtype=torch.float32))
                    
                    # Get attribute embedding (attr_embedding, 256 dims)
                    if item.attr_embedding:
                        attr_embeddings.append(torch.tensor(item.attr_embedding, dtype=torch.float32))
                    else:
                        attr_embeddings.append(torch.zeros(256, dtype=torch.float32))
                
                if clip_embeddings and attr_embeddings:
                    # Average pool across items to get single outfit representation
                    clip_avg = torch.stack(clip_embeddings).mean(dim=0)  # (512,)
                    attr_avg = torch.stack(attr_embeddings).mean(dim=0)  # (256,)
                    
                    # Concatenate clip + attr: total 768 features
                    outfit_tensor = torch.cat([clip_avg, attr_avg]).unsqueeze(0)  # (1, 768)
                    
                    # Rating is already normalized 0-1 from frontend
                    learner_manager.save_outfit_rating(user.username, outfit_tensor, rating)
                    logger.info(f"🧠 Personal model trained - User: {user.username}, Rating: {rating}")
    except Exception as e:
        logger.error(f"❌ Error updating user preference model: {e}", exc_info=True)
        # Don't fail the rating if preference learning fails
    
    return {"message": "Outfit rated successfully", "rating": rating}


@router.delete("/{wardrobe_id}/outfits/{outfit_id}")
def delete_outfit(wardrobe_id: int, outfit_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete an outfit."""
    outfit = db.query(Outfit).filter(
        Outfit.id == outfit_id,
        Outfit.wardrobe_id == wardrobe_id,
        Outfit.user_id == user.id
    ).first()
    
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    
    db.delete(outfit)
    db.commit()
    
    return {"message": "Outfit deleted successfully"}
