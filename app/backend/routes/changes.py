"""Item changes and feedback tracking routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime

from app.backend.database import get_db, User, Wardrobe, Item, ItemChange
from app.backend.schemas import ItemChangeResponse
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/wardrobe", tags=["changes"])


@router.get("/changes/user", response_model=List[ItemChangeResponse])
def get_user_item_changes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get all item changes (corrections) made by the current user for tagger retraining."""
    changes = db.query(ItemChange).filter(
        ItemChange.user_id == user.id
    ).order_by(ItemChange.created_at.desc()).offset(skip).limit(limit).all()
    
    return [ItemChangeResponse.model_validate(c) for c in changes]


@router.get("/changes/wardrobe/{wardrobe_id}", response_model=List[ItemChangeResponse])
def get_wardrobe_item_changes(
    wardrobe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get all item changes in a specific wardrobe for tagger retraining."""
    wardrobe = db.query(Wardrobe).filter(
        Wardrobe.id == wardrobe_id,
        Wardrobe.user_id == user.id
    ).first()
    
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    changes = db.query(ItemChange).filter(
        ItemChange.wardrobe_id == wardrobe_id
    ).order_by(ItemChange.created_at.desc()).offset(skip).limit(limit).all()
    
    return [ItemChangeResponse.model_validate(c) for c in changes]


@router.get("/changes/stats", response_model=Dict[str, Any])
def get_item_changes_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics on item corrections for tagger improvement tracking."""
    total_changes = db.query(func.count(ItemChange.id)).filter(
        ItemChange.user_id == user.id
    ).scalar()
    
    # Count changes by type
    main_cat_changes = db.query(func.count(ItemChange.id)).filter(
        ItemChange.user_id == user.id,
        ItemChange.corrected_main_category_indices.isnot(None)
    ).scalar()
    
    sub_cat_changes = db.query(func.count(ItemChange.id)).filter(
        ItemChange.user_id == user.id,
        ItemChange.corrected_sub_category_indices.isnot(None)
    ).scalar()
    
    cat_changes = db.query(func.count(ItemChange.id)).filter(
        ItemChange.user_id == user.id,
        ItemChange.corrected_category_indices.isnot(None)
    ).scalar()
    
    # Average confidence in corrections
    avg_confidence = db.query(func.avg(ItemChange.confidence_feedback)).filter(
        ItemChange.user_id == user.id,
        ItemChange.confidence_feedback.isnot(None)
    ).scalar()
    
    return {
        "total_changes": total_changes or 0,
        "main_category_corrections": main_cat_changes or 0,
        "sub_category_corrections": sub_cat_changes or 0,
        "category_corrections": cat_changes or 0,
        "average_confidence": float(avg_confidence) if avg_confidence else None,
        "ready_for_tagger_retraining": (total_changes or 0) >= 10  # Minimum for effective training
    }


@router.post("/changes/export-for-training", response_model=Dict[str, Any])
def export_item_changes_for_training(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Export item changes as training data for tagger improvement.
    
    Returns structured data ready for fine-tuning the tagger model.
    """
    changes = db.query(ItemChange).filter(
        ItemChange.user_id == user.id
    ).all()
    
    if min_confidence > 0:
        changes = [c for c in changes if c.confidence_feedback and c.confidence_feedback >= min_confidence]
    
    # Structure data for tagger retraining
    training_samples = []
    
    for change in changes:
        # Get the item to access embeddings
        item = db.query(Item).filter(Item.id == change.item_id).first()
        if not item:
            continue
        
        sample = {
            'item_id': item.id,
            'node_id': item.node_id,
            'img_embedding': item.img_embedding,
            'attr_embedding': item.attr_embedding,
            'original_predictions': {
                'main_category_indices': change.original_main_category_indices,
                'sub_category_indices': change.original_sub_category_indices,
                'category_indices': change.original_category_indices,
                'related_indices': change.original_related_indices,
            },
            'corrected_labels': {
                'main_category_indices': change.corrected_main_category_indices,
                'sub_category_indices': change.corrected_sub_category_indices,
                'category_indices': change.corrected_category_indices,
                'related_indices': change.corrected_related_indices,
            },
            'confidence': change.confidence_feedback or 1.0,
            'notes': change.notes,
            'timestamp': change.created_at.isoformat()
        }
        training_samples.append(sample)
    
    return {
        'user_id': user.id,
        'total_samples': len(training_samples),
        'samples': training_samples,
        'export_timestamp': datetime.now().isoformat(),
        'recommendation': 'Use samples with confidence >= 0.7 for best training results'
    }
