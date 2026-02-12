"""Wardrobe management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.backend.database import get_db, User, Wardrobe, Item, Outfit, OutfitItem
from app.backend.schemas import WardrobeResponse
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


@router.post("/", response_model=WardrobeResponse)
def create_wardrobe(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new wardrobe."""
    # Check if user already has wardrobe
    existing = db.query(Wardrobe).filter(Wardrobe.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has a wardrobe")
    
    wardrobe = Wardrobe(user_id=user.id)
    db.add(wardrobe)
    db.commit()
    db.refresh(wardrobe)
    
    return WardrobeResponse(
        id=wardrobe.id,
        created_at=wardrobe.created_at,
        updated_at=wardrobe.updated_at,
        items_count=0,
        outfits_count=0
    )


@router.get("/", response_model=List[WardrobeResponse])
def list_wardrobes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all wardrobes for the current user."""
    wardrobes = db.query(Wardrobe).filter(Wardrobe.user_id == user.id).all()
    
    result = []
    for wardrobe in wardrobes:
        items_count = db.query(Item).filter(Item.wardrobe_id == wardrobe.id).count()
        outfits_count = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe.id).count()
        result.append(WardrobeResponse(
            id=wardrobe.id,
            created_at=wardrobe.created_at,
            updated_at=wardrobe.updated_at,
            items_count=items_count,
            outfits_count=outfits_count
        ))
    
    return result


@router.get("/{wardrobe_id}", response_model=WardrobeResponse)
def get_wardrobe(wardrobe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get wardrobe details with item and outfit counts."""
    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    items_count = db.query(Item).filter(Item.wardrobe_id == wardrobe_id).count()
    outfits_count = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe_id).count()
    
    return WardrobeResponse(
        id=wardrobe.id,
        created_at=wardrobe.created_at,
        updated_at=wardrobe.updated_at,
        items_count=items_count,
        outfits_count=outfits_count
    )


@router.get("/{wardrobe_id}/stats")
def get_wardrobe_stats(wardrobe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed statistics for a wardrobe."""
    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    # Count items by category
    items = db.query(Item).filter(Item.wardrobe_id == wardrobe_id).all()
    outfits = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe_id).all()
    
    items_count = len(items)
    outfits_count = len(outfits)
    
    # Category distribution
    category_dist = {}
    for item in items:
        if item.main_category_indices and len(item.main_category_indices) > 0:
            cat = str(item.main_category_indices[0])
            category_dist[cat] = category_dist.get(cat, 0) + 1
        else:
            category_dist["unknown"] = category_dist.get("unknown", 0) + 1
    
    # Outfit size distribution
    outfit_sizes = {}
    for outfit in outfits:
        size = db.query(OutfitItem).filter(OutfitItem.outfit_id == outfit.id).count()
        outfit_sizes[str(size)] = outfit_sizes.get(str(size), 0) + 1
    
    # Average outfit rating
    avg_rating = 0.0
    if outfits:
        total_rating = sum((o.user_rating or o.system_rating or 0.5) for o in outfits)
        avg_rating = round(total_rating / len(outfits), 2)
    
    return {
        "wardrobe_id": wardrobe_id,
        "items_count": items_count,
        "outfits_count": outfits_count,
        "avg_outfit_rating": avg_rating,
        "category_distribution": category_dist,
        "outfit_size_distribution": outfit_sizes,
        "created_at": wardrobe.created_at,
        "updated_at": wardrobe.updated_at
    }
