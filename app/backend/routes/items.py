"""Item management routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import torch
import numpy as np
import uuid
import base64
from PIL import Image
from io import BytesIO
from pathlib import Path
from datetime import datetime

from app.backend.database import get_db, User, Wardrobe, Item, Outfit, OutfitItem, ItemChange
from app.backend.schemas import ItemResponse, ItemUpdate, ItemChangeResponse
from app.backend.storage_config import StorageConfig
from app.backend.logging_config import get_logger
from app.utils.outfit_generator import generate_outfit_candidates, is_valid_outfit_structure, generate_outfits_for_new_item
from app.utils.ml_models import get_models
from app.models.user_preference_learner import get_preference_learner_manager
from app.models.tagger_feedback_learner import get_tagger_feedback_learner
from app.utils.auth_utils import get_current_user
from app.utils.hgnn_utils import build_incidence_matrix

logger = get_logger(__name__)

# Check if models are available
try:
    from app.models.load_models import load_all_models
    MODELS_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️  Models not available: {e}")
    MODELS_AVAILABLE = False

router = APIRouter(prefix="/wardrobe", tags=["items"])


# ============================================================================
# IN-MEMORY IMAGE CACHE - For Desktop App Download
# ============================================================================
# Temporarily stores image bytes so desktop can download and save locally
_image_cache: Dict[str, Dict[str, Any]] = {}  # {item_id: {"bytes": ..., "filename": ..., "user_id": ...}}




@router.post("/{wardrobe_id}/items/upload", response_model=ItemResponse)
async def upload_item(
    wardrobe_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an item with image and auto-generate outfits."""
    logger.debug(f"📸 Item upload started - User: {user.username}, Wardrobe: {wardrobe_id}, File: {file.filename}")
    
    if not MODELS_AVAILABLE:
        logger.error("❌ Item upload failed: ML models not available")
        raise HTTPException(status_code=503, detail="ML models not available")

    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"⚠️  File rejected: Too large ({len(contents) / 1024 / 1024:.1f}MB)")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )
    
    # Validate file type by checking magic bytes or extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    
    # Check if it's an image by trying to open it
    try:
        test_image = Image.open(BytesIO(contents))
        test_image.verify()
        logger.debug(f"✅ File validation passed - Size: {len(contents) / 1024:.1f}KB")
    except Exception:
        logger.error(f"❌ Invalid image file: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="File must be a valid image (jpg, png, webp, gif, bmp)"
        )

    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        logger.warning(f"⚠️  Wardrobe not found: {wardrobe_id}")
        raise HTTPException(status_code=404, detail="Wardrobe not found")

    models = get_models()
    fashion_clip = models.get("fashion_clip")
    tagger = models.get("hierarchical_tagger")
    attribute_encoder = models.get("attribute_encoder")
    hgnn = models.get("fashion_hypergraph")

    # Process image
    try:
        image = Image.open(BytesIO(contents)).convert("RGB")
        logger.debug("🖼️  Image processed and converted to RGB")
    except Exception as e:
        logger.error(f"❌ Image processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    # Generate unique image path (for reference only, NOT saving to server)
    # Image will be saved ONLY on user device by desktop app
    image_filename = f"{uuid.uuid4().hex}.jpg"
    
    logger.debug(f"📌 Image reference created: {image_filename} (will be saved on user device only)")

    # Generate embeddings
    try:
        clip_emb_result = fashion_clip.encode_images([image], batch_size=1)
        # Handle both tensor and numpy array returns from FashionCLIP
        if isinstance(clip_emb_result, torch.Tensor):
            clip_emb = clip_emb_result.cpu().numpy()[0].tolist()
        else:
            # Already a numpy array
            clip_emb = clip_emb_result[0].tolist() if hasattr(clip_emb_result, 'tolist') else clip_emb_result[0]
        
        # Ensure tensor is on the same device as the model
        device_str = next(tagger.parameters()).device if tagger else torch.device('cpu')
        clip_tensor = torch.tensor([clip_emb], dtype=torch.float32).to(device_str)
        
        # tagger returns a tuple: (main_logits, sub_logits, category_logits, related_logits)
        # Model was trained with 512-dim FashionCLIP embeddings directly - no projection needed
        logits_tuple = tagger(clip_tensor)
        
        # Thresholds for confidence-based prediction
        # These are optimal values found during training via F1-score optimization
        THRESHOLDS = {
            'main': 0.511,      # Optimal threshold for main categories
            'sub': 0.471,       # Optimal threshold for sub categories (was incorrectly 0.6)
            'category': 0.559,  # Optimal threshold for full categories
            'related': 0.238    # Optimal threshold for related items
        }
        
        # Extract category indices from all logits outputs with confidence thresholds
        # Can have multiple indices if confidence is above threshold
        main_category_idx = []
        sub_category_idx = []
        category_idx = []
        related_idx = []
        
        if isinstance(logits_tuple, tuple) and len(logits_tuple) >= 4:
            # Forward pass - extract logits in correct order: main, sub, category, related
            main_logits = logits_tuple[0]
            sub_logits = logits_tuple[1]
            category_logits = logits_tuple[2]
            related_logits = logits_tuple[3]
            
            # Compute probabilities using sigmoid (multi-label classification)
            main_probs = torch.sigmoid(main_logits).cpu().detach().numpy()[0]
            sub_probs = torch.sigmoid(sub_logits).cpu().detach().numpy()[0]
            cat_probs = torch.sigmoid(category_logits).cpu().detach().numpy()[0]
            rel_probs = torch.sigmoid(related_logits).cpu().detach().numpy()[0]
            
            # Thresholded predictions -> get all indices above threshold
            main_category_idx = [i for i, p in enumerate(main_probs) if p >= THRESHOLDS['main']]
            sub_category_idx = [i for i, p in enumerate(sub_probs) if p >= THRESHOLDS['sub']]
            category_idx = [i for i, p in enumerate(cat_probs) if p >= THRESHOLDS['category']]
            related_idx = [i for i, p in enumerate(rel_probs) if p >= THRESHOLDS['related']]
            
        elif isinstance(logits_tuple, tuple) and len(logits_tuple) >= 3:
            # Fallback for older model format (3 outputs)
            main_logits = logits_tuple[0]
            main_probs = torch.sigmoid(main_logits).cpu().detach().numpy()[0]
            main_category_idx = [i for i, p in enumerate(main_probs) if p >= THRESHOLDS['main']]
            
            sub_logits = logits_tuple[1]
            sub_probs = torch.sigmoid(sub_logits).cpu().detach().numpy()[0]
            sub_category_idx = [i for i, p in enumerate(sub_probs) if p >= THRESHOLDS['sub']]
            
            category_logits = logits_tuple[2]
            cat_probs = torch.sigmoid(category_logits).cpu().detach().numpy()[0]
            category_idx = [i for i, p in enumerate(cat_probs) if p >= THRESHOLDS['category']]
        else:
            # Fallback if not tuple format
            main_logits = logits_tuple[0] if isinstance(logits_tuple, tuple) else logits_tuple
            main_probs = torch.sigmoid(main_logits).cpu().detach().numpy()[0]
            category_idx = [i for i, p in enumerate(main_probs) if p >= THRESHOLDS['main']]
            main_category_idx = category_idx
        
        # For attribute embeddings, create a simple one-hot encoded vector based on category
        # Since we don't have full attribute features, use a placeholder
        if attribute_encoder:
            attr_device = next(attribute_encoder.parameters()).device
            # Create placeholder attribute vector (zeros) - in production, this should be actual attributes
            # Get expected input_dim from model
            attr_input_dim = next(attribute_encoder.parameters()).shape[1]  # Gets first linear layer input features
            attr_input_vec = torch.zeros(1, attr_input_dim, dtype=torch.float32).to(attr_device)
            # Set first category index as feature to help differentiate items
            first_cat_idx = category_idx[0] if isinstance(category_idx, list) and len(category_idx) > 0 else 0
            attr_input_vec[0, min(first_cat_idx, attr_input_dim-1)] = 1.0
            with torch.no_grad():  # Disable gradients to allow numpy conversion
                attr_result = attribute_encoder(attr_input_vec)
            attr_emb = attr_result.cpu().numpy()[0].tolist() if hasattr(attr_result, 'cpu') else attr_result[0]
        else:
            attr_emb = [0.0] * 256
    except Exception as e:
        print(f"⚠️  Error generating embeddings: {e}")
        import traceback
        traceback.print_exc()
        clip_emb = [0.0] * 512
        attr_emb = [0.0] * 256

    # Create item with category information
    # Use a unique node_id based on current timestamp + random to ensure uniqueness
    next_node_id = int(datetime.utcnow().timestamp() * 1000) + uuid.uuid4().int % 1000
    item = Item(
        user_id=user.id,
        wardrobe_id=wardrobe_id,
        node_id=next_node_id,
        image_path=image_filename,
        img_embedding=clip_emb,
        attr_embedding=attr_emb,
        available=True,
        main_category_indices=main_category_idx if isinstance(main_category_idx, list) else ([] if not main_category_idx else [main_category_idx]),
        sub_category_indices=sub_category_idx if isinstance(sub_category_idx, list) else ([] if not sub_category_idx else [sub_category_idx]),
        category_indices=category_idx if isinstance(category_idx, list) else ([] if not category_idx else [category_idx]),
        related_indices=related_idx if isinstance(related_idx, list) else ([] if not related_idx else [related_idx]),
    )
    db.add(item)
    db.flush()
    logger.info(f"✅ Item created - ID: {item.id}, Node: {next_node_id}, Categories: {category_idx}")

    # Save image to backend storage directory
    # Images are stored on the backend server for access across devices
    try:
        # Create backend images directory (not user device)
        backend_images_dir = StorageConfig.IMAGES_DIR / user.username  # Organize by username
        backend_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Save image with item ID as filename
        image_file_path = backend_images_dir / f"item_{item.id}.jpg"
        with open(image_file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"💾 Image saved to backend - Path: {image_file_path}, Size: {len(contents) / 1024:.1f}KB")
    except Exception as e:
        logger.error(f"⚠️  Failed to save image to backend: {e}")
    
    # Also keep in-memory cache for quick access during this session
    _image_cache[str(item.id)] = {
        "bytes": contents,
        "filename": image_filename,
        "user_id": user.id,
        "content_type": "image/jpeg"
    }
    logger.debug(f"📦 Image cached in memory - Item: {item.id}, Size: {len(contents) / 1024:.1f}KB")

    # Auto-generate outfits with the new item
    outfits_count = generate_outfits_for_new_item(
        db=db,
        new_item=item,
        wardrobe_id=wardrobe_id,
        user_id=user.id,
        hgnn=hgnn,
        max_outfits=100
    )
    logger.info(f"🎨 Auto-generated {outfits_count} outfits for new item {item.id}")
    
    # Commit all changes to database (CRITICAL - must be done before returning)
    db.commit()
    db.refresh(item)
    logger.info(f"✨ Item upload completed - ID: {item.id}, File: {image_filename}")

    # Return item response with image bytes encoded as base64 for desktop to save
    item_response = ItemResponse.model_validate(item)
    
    # Convert response to dict and add image bytes
    response_dict = item_response.model_dump()
    response_dict["image_data"] = base64.b64encode(contents).decode('utf-8')
    response_dict["image_filename"] = image_filename
    response_dict["save_instructions"] = f"Save image to: ~/.fashion_wardrobe_app/{{username}}/images/{image_filename}"
    
    logger.info(f"📸 Image bytes included in response - Size: {len(contents) / 1024:.1f}KB")
    
    return response_dict



@router.post("/{wardrobe_id}/items", response_model=ItemResponse)
async def upload_item_alt(
    wardrobe_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an item with image (alias for /items/upload)."""
    # Delegate to the main upload_item function
    return await upload_item(wardrobe_id, file, user, db)


@router.get("/{wardrobe_id}/items", response_model=List[ItemResponse])
def list_items(wardrobe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all items in a wardrobe."""
    wardrobe = db.query(Wardrobe).filter(Wardrobe.id == wardrobe_id, Wardrobe.user_id == user.id).first()
    if not wardrobe:
        raise HTTPException(status_code=404, detail="Wardrobe not found")
    
    items = db.query(Item).filter(Item.wardrobe_id == wardrobe_id).all()
    return [ItemResponse.model_validate(item) for item in items]


# ========== SPECIFIC ROUTES - MUST BE BEFORE GENERIC {item_id} ROUTE ==========

@router.get("/{wardrobe_id}/items/{item_id}/download-image")
def download_item_image_for_local_save(
    wardrobe_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download image bytes so desktop app can save locally to:
    ~/.fashion_wardrobe_app/{username}/images/{image_path}
    
    This is called after upload so the app can save the image it just uploaded.
    Image bytes are stored in cache directory for persistent access.
    """
    # Verify item exists and belongs to user
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.wardrobe_id == wardrobe_id,
        Item.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Try to get image from cache file first (persistent)
    cache_dir = StorageConfig.STORAGE_ROOT / "temp_image_cache"
    cache_file = cache_dir / f"item_{item_id}.jpg"
    
    if cache_file.exists():
        logger.info(f"📥 Serving image from cache file - Item: {item_id}, Path: {cache_file}")
        return FileResponse(
            path=cache_file,
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename=item_{item_id}.jpg"}
        )
    
    # Fallback to in-memory cache
    item_id_str = str(item_id)
    if item_id_str in _image_cache:
        image_data = _image_cache[item_id_str]
        
        # Verify user ownership
        if image_data["user_id"] != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"📥 Serving image from memory cache - Item: {item_id}")
        
        # Stream image bytes
        return StreamingResponse(
            iter([image_data["bytes"]]),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename={image_data['filename']}"}
        )
    
    # Image not found in either cache
    logger.warning(f"⚠️  Image not found in any cache - Item: {item_id}")
    raise HTTPException(status_code=404, detail="Image not found. Please re-upload.")


@router.get("/{wardrobe_id}/items/{item_id}/image")
def get_item_image(wardrobe_id: int, item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get item image from backend storage. Works across devices.
    Returns image bytes that frontend can display.
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.wardrobe_id == wardrobe_id,
        Item.user_id == user.id
    ).first()
    
    if not item or not item.image_path:
        raise HTTPException(status_code=404, detail="Item not found or has no image")
    
    # Try to get image from backend storage first (disk)
    backend_images_dir = StorageConfig.IMAGES_DIR / user.username
    image_file_path = backend_images_dir / f"item_{item_id}.jpg"
    
    if image_file_path.exists():
        logger.debug(f"📥 Serving image from backend storage - Item: {item_id}, Path: {image_file_path}")
        return FileResponse(
            path=image_file_path,
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename=item_{item_id}.jpg"}
        )
    
    # Fallback to memory cache if file not found
    item_id_str = str(item_id)
    if item_id_str in _image_cache:
        image_data = _image_cache[item_id_str]
        
        # Verify user ownership
        if image_data["user_id"] != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.debug(f"📥 Serving image from cache - Item: {item_id}")
        
        return StreamingResponse(
            iter([image_data["bytes"]]),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename={image_data['filename']}"}
        )
    
    raise HTTPException(status_code=404, detail="Image not found")


# ========== GENERIC ROUTES - MUST BE AFTER SPECIFIC ROUTES ==========

@router.get("/{wardrobe_id}/items/{item_id}", response_model=ItemResponse)
def get_item(wardrobe_id: int, item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific item from wardrobe."""
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.wardrobe_id == wardrobe_id,
        Item.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return ItemResponse.model_validate(item)


@router.delete("/{wardrobe_id}/items/{item_id}")
def delete_item(wardrobe_id: int, item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete an item from wardrobe and cascade delete all associated outfits.
    
    NOTE: Image file is on user device, so it's the desktop app's responsibility to delete it from:
    ~/.fashion_wardrobe_app/{username}/images/{image_path}
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.wardrobe_id == wardrobe_id,
        Item.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Find all outfits containing this item
    outfits_with_item = db.query(Outfit).join(OutfitItem).filter(
        OutfitItem.item_id == item_id,
        Outfit.wardrobe_id == wardrobe_id
    ).distinct().all()
    
    # Delete all outfits that contain this item
    for outfit in outfits_with_item:
        # Delete outfit items
        db.query(OutfitItem).filter(OutfitItem.outfit_id == outfit.id).delete()
        # Delete outfit itself
        db.delete(outfit)
    
    # NOTE: Image file is on user device, not server
    # Desktop app should delete image from: ~/.fashion_wardrobe_app/{username}/images/{image_path}
    # We only delete the database record here
    
    # Delete item from database
    db.delete(item)
    db.commit()
    
    logger.info(f"✅ Item deleted - ID: {item.id}, User: {user.username}")
    logger.info(f"📌 Desktop app should delete image from: ~/.fashion_wardrobe_app/{user.username}/images/{item.image_path}")
    
    return {
        "message": "Item deleted successfully with associated outfits",
        "image_path": item.image_path,
        "note": f"Desktop app should manually delete: ~/.fashion_wardrobe_app/{user.username}/images/{item.image_path}"
    }



@router.put("/{wardrobe_id}/items/{item_id}", response_model=ItemResponse)
def update_item(
    wardrobe_id: int,
    item_id: int,
    item_update: ItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update item attributes and availability, optionally tracking corrections for tagger improvement."""
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.wardrobe_id == wardrobe_id,
        Item.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Store original values for change tracking
    original_values = {
        'main_category_indices': item.main_category_indices,
        'sub_category_indices': item.sub_category_indices,
        'category_indices': item.category_indices,
        'related_indices': item.related_indices,
    }
    
    # Track if user is correcting categories (for tagger improvement)
    has_category_changes = False
    
    # Update fields that are provided
    if item_update.main_category_indices is not None:
        if item_update.main_category_indices != item.main_category_indices:
            has_category_changes = True
        item.main_category_indices = item_update.main_category_indices
    if item_update.sub_category_indices is not None:
        if item_update.sub_category_indices != item.sub_category_indices:
            has_category_changes = True
        item.sub_category_indices = item_update.sub_category_indices
    if item_update.category_indices is not None:
        if item_update.category_indices != item.category_indices:
            has_category_changes = True
        item.category_indices = item_update.category_indices
    if item_update.related_indices is not None:
        if item_update.related_indices != item.related_indices:
            has_category_changes = True
        item.related_indices = item_update.related_indices
    if item_update.available is not None:
        item.available = item_update.available
    
    # Regenerate attribute embeddings if categories changed
    if has_category_changes:
        try:
            # Get models for attribute encoding
            models = get_models()
            attribute_encoder = models.get("attribute_encoder") if models else None
            
            if attribute_encoder and item.main_category_indices and len(item.main_category_indices) > 0:
                # Use first main category index to generate embedding
                first_cat_idx = item.main_category_indices[0]
                attr_device = next(attribute_encoder.parameters()).device
                
                # Get expected input_dim from model
                attr_input_dim = next(attribute_encoder.parameters()).shape[1]
                attr_input_vec = torch.zeros(1, attr_input_dim, dtype=torch.float32).to(attr_device)
                
                # Set the category index
                attr_input_vec[0, min(first_cat_idx, attr_input_dim-1)] = 1.0
                
                # Generate embedding
                attribute_encoder.eval()
                with torch.no_grad():
                    attr_result = attribute_encoder(attr_input_vec)
                    attr_embedding = attr_result.cpu().numpy().flatten().tolist()
                    item.attr_embedding = attr_embedding
                    logger.info(f"✨ Regenerated attribute embedding for item {item_id} - Categories: {item.main_category_indices}")
            else:
                logger.debug(f"Could not regenerate attribute embedding for item {item_id} - encoder or categories unavailable")
        except Exception as e:
            logger.warning(f"⚠️ Failed to regenerate attribute embedding for item {item_id}: {e}")
    
    db.commit()
    db.refresh(item)
    
    # Save item change record if this is a user correction with category changes
    if item_update.is_correction and has_category_changes:
        item_change = ItemChange(
            item_id=item.id,
            user_id=user.id,
            wardrobe_id=wardrobe_id,
            original_main_category_indices=original_values['main_category_indices'],
            original_sub_category_indices=original_values['sub_category_indices'],
            original_category_indices=original_values['category_indices'],
            original_related_indices=original_values['related_indices'],
            corrected_main_category_indices=item_update.main_category_indices,
            corrected_sub_category_indices=item_update.sub_category_indices,
            corrected_category_indices=item_update.category_indices,
            corrected_related_indices=item_update.related_indices,
            is_user_feedback=True  # Mark as user-provided feedback
        )
        db.add(item_change)
        db.commit()
        print(f"✅ Item change tracked for item {item_id} by user {user.id}")
        
        # Trigger tagger retraining every 100 user feedback corrections (shared across all users)
        try:
            # Count only user-feedback corrections
            user_feedback_count = db.query(ItemChange).filter(ItemChange.is_user_feedback == True).count()
            if user_feedback_count % 100 == 0 and user_feedback_count > 0:
                print(f"🎯 {user_feedback_count} user feedback corrections reached - triggering tagger retraining...")
                
                # Collect user feedback corrections with embeddings for retraining
                all_user_feedback = db.query(ItemChange).filter(ItemChange.is_user_feedback == True).all()
                training_samples = []
                
                for change in all_user_feedback:
                    item_to_train = db.query(Item).filter(Item.id == change.item_id).first()
                    if not item_to_train or not item_to_train.img_embedding:
                        continue
                    
                    sample = {
                        'embedding': np.array(item_to_train.img_embedding),
                        'original_main': change.original_main_category_indices or [],
                        'original_sub': change.original_sub_category_indices or [],
                        'original_category': change.original_category_indices or [],
                        'corrected_main': change.corrected_main_category_indices or [],
                        'corrected_sub': change.corrected_sub_category_indices or [],
                        'corrected_category': change.corrected_category_indices or [],
                        'confidence': change.confidence_feedback or 1.0
                    }
                    training_samples.append(sample)
                
                if len(training_samples) >= 2:
                    tagger_learner = get_tagger_feedback_learner()
                    if tagger_learner:
                        print(f"🚀 Retraining tagger on {len(training_samples)} user feedback corrections...")
                        result = tagger_learner.train_on_corrections(training_samples, epochs=5)
                        print(f"✅ Tagger retrained: {result}")
        except Exception as e:
            print(f"⚠️  Error triggering tagger retraining: {e}")
            import traceback
            traceback.print_exc()
    
    return ItemResponse.model_validate(item)


# ============================================================================
# UTILITY FUNCTIONS - Storage Management
# ============================================================================

def cleanup_orphaned_files(user: User, db: Session) -> Dict[str, Any]:
    """
    NOTE: Images are no longer stored on server - they're on user device only.
    This function is deprecated but kept for reference.
    
    Returns:
        Dictionary with cleanup status
    """
    return {
        "status": "success",
        "message": "Images are now stored on user device only (no server cleanup needed)",
        "note": "Desktop app manages images in: ~/.fashion_wardrobe_app/{username}/images/"
    }


@router.post("/cleanup/orphaned")
def cleanup_orphaned_images(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Endpoint to manually trigger cleanup (now deprecated - images on user device only).
    """
    return cleanup_orphaned_files(user, db)

