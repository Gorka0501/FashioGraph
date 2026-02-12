"""
Outfit generation utilities with smart filtering and validation.
Handles creating valid outfit combinations based on category rules.
"""

from typing import List, Set, Tuple, Optional
from itertools import combinations
import torch
import numpy as np
from app.utils.compatibility import can_add_to_outfit
from app.backend.logging_config import get_logger

logger = get_logger(__name__)


def collect_outfit_embeddings(outfit_items):
    """
    Collect CLIP and attribute embeddings from outfit items.
    
    Args:
        outfit_items: List of item objects with img_embedding and attr_embedding
    
    Returns:
        Tuple of (clip_embeddings_list, attr_embeddings_list)
    """
    clip_embs = []
    attr_embs = []
    
    for item in outfit_items:
        clip_emb = item.img_embedding if item.img_embedding else [0.0] * 512
        attr_emb = item.attr_embedding if item.attr_embedding else [0.0] * 256
        clip_embs.append(clip_emb)
        attr_embs.append(attr_emb)
    
    return clip_embs, attr_embs


def build_outfit_hypergraph(n_items, device='cpu'):
    """
    Build hypergraph structure for outfit: all items connected via single hyperedge.
    
    Args:
        n_items: Number of items in outfit
        device: torch device
    
    Returns:
        Tuple of (H, Dv_inv_sqrt, De_inv) as torch tensors
    """
    # H matrix: (n_items, 1) - all items connected to single hyperedge
    H_np = np.ones((n_items, 1), dtype=np.float32)
    
    # Compute degree matrices
    Dv_np = np.sum(H_np, axis=1)  # (n_items,)
    Dv_np = np.maximum(Dv_np, 1e-8)
    Dv_inv_sqrt_np = np.diag(1.0 / np.sqrt(Dv_np))  # (n_items, n_items)
    
    De_np = np.sum(H_np, axis=0)  # (1,)
    De_np = np.maximum(De_np, 1e-8)
    De_inv_np = np.diag(1.0 / De_np)  # (1, 1)
    
    # Convert to torch tensors on device
    H = torch.from_numpy(H_np).to(device)
    Dv_inv_sqrt = torch.from_numpy(Dv_inv_sqrt_np).to(device)
    De_inv = torch.from_numpy(De_inv_np).to(device)
    
    return H, Dv_inv_sqrt, De_inv


def score_outfit_with_model(outfit_items, model, device='cpu'):
    """
    Score an outfit using the FashionHyperGraphModel.
    Items are always sorted in order: all-body, tops, bottoms, shoes, then accessories by category.
    
    Args:
        outfit_items: List of item objects with img_embedding and attr_embedding
        model: FashionHyperGraphModel instance
        device: torch device
    
    Returns:
        float: Score between 0 and 1
    """
    if not model or len(outfit_items) < 2:
        return 0.5
    
    try:
        # Define the desired order: all-body(0), tops(2), bottoms(1), shoes(5), then accessories in order
        category_order = {0: 0, 2: 1, 1: 2, 5: 3, 3: 4, 4: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
        
        # Sort items by this specific order
        def get_sort_key(item):
            main_cat = item.main_category_indices[0] if item.main_category_indices else 999
            return category_order.get(main_cat, 999)
        
        sorted_items = sorted(outfit_items, key=get_sort_key)
        
        n_items = len(sorted_items)
        
        # Collect embeddings from sorted items
        clip_embs, attr_embs = collect_outfit_embeddings(sorted_items)
        
        # Convert to tensors
        clip_feats = torch.tensor(clip_embs, dtype=torch.float32).to(device)
        attr_feats = torch.tensor(attr_embs, dtype=torch.float32).to(device)
        
        # Build hypergraph structure
        H, Dv_inv_sqrt, De_inv = build_outfit_hypergraph(n_items, device)
        
        # Outfit nodes and mask
        outfit_nodes = torch.arange(n_items, dtype=torch.long, device=device).unsqueeze(0)
        outfit_mask = torch.ones(1, n_items, dtype=torch.float32, device=device)
        
        with torch.no_grad():
            # Call model with outfit_nodes and outfit_mask for proper scoring
            scores, node_emb, pooled, attn = model(
                clip_feats,
                attr_feats,
                H=H,
                Dv_inv_sqrt=Dv_inv_sqrt,
                De_inv=De_inv,
                outfit_nodes=outfit_nodes,
                outfit_mask=outfit_mask
            )
            
            # Extract the scalar value from scores tensor
            if isinstance(scores, torch.Tensor):
                score_val = float(scores.flatten()[0].item())
            else:
                score_val = float(scores)
            
            # Clamp to [0, 1] (regressor uses Sigmoid so should be in range)
            score_val = np.clip(score_val, 0.0, 1.0)
        
        return score_val
    except Exception as e:
        print(f"⚠️  Error scoring outfit: {e}")
        import traceback
        traceback.print_exc()
        return 0.5


def is_valid_outfit_structure(item_categories: List[int]) -> bool:
    """
    Validate that an outfit has proper structure with logical reasoning.
    
    A valid outfit must have:
    1. A core item: tops (1) + bottoms (2), OR all-body (0)
    2. Shoes (4) - REQUIRED for complete outfits
    3. Optional: bags (5), accessories (6-10)
    4. NO duplicate main categories (each appears only once)
    
    Valid patterns:
    - (tops + bottoms) + shoes = valid 3-item base
    - (all-body) + shoes = valid 2-item base
    - Core + shoes + bag/accessory = valid combinations
    
    Args:
        item_categories: List of main category indices for items in outfit
    
    Returns:
        True if outfit structure is logical and complete, False otherwise
    """
    if not item_categories:
        return False
    
    # Check for duplicate main categories - not allowed
    if len(item_categories) != len(set(item_categories)):
        return False
    
    # Must have at least 2 items
    if len(item_categories) < 2:
        return False
    
    # Category groups
    TOPS = 2
    BOTTOMS = 1
    ALL_BODY = 0
    SHOES = 5
    ACCESSORIES = {3, 4, 6, 7, 8, 9, 10}  # Scarves, hats, sunglasses, jewellery, etc.
    
    has_core = False
    has_shoes = False
    
    # Check for core item (tops+bottoms OR all-body)
    if ALL_BODY in item_categories:
        has_core = True
    elif TOPS in item_categories and BOTTOMS in item_categories:
        has_core = True
    
    # Check for shoes
    if SHOES in item_categories:
        has_shoes = True
    
    # Rule 1: Must have a core item
    if not has_core:
        return False
    
    # Rule 2: Must have shoes
    if not has_shoes:
        return False
    
    # Rule 3: All items must be valid clothing categories
    for cat in item_categories:
        if cat not in {ALL_BODY, TOPS, BOTTOMS, SHOES} and cat not in ACCESSORIES:
            return False
    
    # Rule 4: Logical combinations
    # - All-body items shouldn't be mixed with tops/bottoms
    if ALL_BODY in item_categories and (TOPS in item_categories or BOTTOMS in item_categories):
        return False
    
    return True


def generate_outfit_candidates(
    items: List,
    existing_combinations: Set[Tuple[int, ...]],
    model=None,
    device='cpu',
    max_outfits: int = 100
) -> List[Tuple[List[int], float, List]]:
    """
    Generate outfit candidates with sizes 2-6 items.
    Filters by compatibility and structure rules.
    Prevents outfits that are exact duplicates.
    
    Args:
        items: List of item objects with id and main_category_indices
        existing_combinations: Set of already-used item ID combinations (sorted tuples)
        model: ML model for scoring
        device: torch device
        max_outfits: Maximum number of outfits to generate
    
    Returns:
        List of tuples: (sorted_item_ids, score, item_objects)
    """
    outfit_candidates = []
    generated_count = 0
    
    def is_exact_duplicate(item_ids: List[int]) -> bool:
        """Check if item_ids is an exact duplicate of an existing outfit."""
        return tuple(sorted(item_ids)) in existing_combinations
    
    def validate_and_score_outfit(combo_items: List) -> Optional[Tuple[List[int], float, List]]:
        """Validate and score an outfit combination."""
        nonlocal generated_count
        
        if generated_count >= max_outfits:
            return None
        
        # Get categories
        cats = [
            item.main_category_indices[0] if item.main_category_indices else 0
            for item in combo_items
        ]
        
        # Check compatibility: each item compatible with all before it
        compatible = all(
            can_add_to_outfit(cats[i], cats[:i])
            for i in range(1, len(cats))
        )
        
        if not compatible:
            return None
        
        # Check structure validity
        if not is_valid_outfit_structure(cats):
            return None
        
        # Check for duplicates
        item_ids = sorted([item.id for item in combo_items])
        if is_exact_duplicate(item_ids):
            return None
        
        # Score outfit
        sorted_items = sorted(combo_items, key=lambda x: x.id)
        score = score_outfit_with_model(sorted_items, model, device)
        
        generated_count += 1
        return (item_ids, score, sorted_items)
    
    # Generate outfits of sizes 2-6
    for size in range(2, 7):
        if generated_count >= max_outfits:
            break
        
        for combo in combinations(range(len(items)), size):
            if generated_count >= max_outfits:
                break
            
            combo_items = [items[i] for i in combo]
            result = validate_and_score_outfit(combo_items)
            if result:
                outfit_candidates.append(result)
    
    # Sort by score (descending)
    outfit_candidates.sort(key=lambda x: x[1], reverse=True)
    return outfit_candidates


def generate_outfits_for_new_item(
    db,
    new_item,
    wardrobe_id: int,
    user_id: int,
    hgnn=None,
    max_outfits: int = 100
) -> int:
    """
    Generate outfits featuring a newly added item.
    
    Args:
        db: Database session
        new_item: The newly created item
        wardrobe_id: Wardrobe ID
        user_id: User ID
        hgnn: ML model for scoring
        max_outfits: Max outfits to generate (default 100)
    
    Returns:
        Number of outfits created
    """
    import traceback
    from app.backend.database import Outfit, OutfitItem, Item
    
    try:
        all_items = db.query(Item).filter(Item.wardrobe_id == wardrobe_id).all()
        logger.debug(f"📊 Generating outfits: {len(all_items)} total items in wardrobe")
        
        # Need at least 2 items total to create outfits
        if len(all_items) < 2:
            logger.warning(f"⚠️  Not enough items to create outfits (need 2+, have {len(all_items)})")
            return 0
        
        # Get existing outfit combinations to avoid duplicates
        existing_outfits = db.query(Outfit).filter(Outfit.wardrobe_id == wardrobe_id).all()
        existing_combinations = set()
        for outfit in existing_outfits:
            outfit_items = db.query(OutfitItem).filter(OutfitItem.outfit_id == outfit.id).all()
            item_ids = tuple(sorted([oi.item_id for oi in outfit_items]))
            existing_combinations.add(item_ids)
        
        logger.debug(f"📊 Found {len(existing_combinations)} existing outfit combinations")
        
        # Generate candidates (2-6 items)
        model_device = next(hgnn.parameters()).device if hgnn else torch.device('cpu')
        outfit_candidates = generate_outfit_candidates(
            all_items,
            existing_combinations,
            model=hgnn,
            device=model_device,
            max_outfits=200  # Generate extra to filter by new item
        )
        
        # Filter to only those with new item
        new_item_outfits = [
            (item_ids, score, outfit_items) 
            for item_ids, score, outfit_items in outfit_candidates 
            if new_item.id in item_ids
        ]
        
        # Create outfits
        created_count = 0
        for item_ids, score, outfit_items in new_item_outfits[:max_outfits]:
            outfit = Outfit(user_id=user_id, wardrobe_id=wardrobe_id, system_rating=score)
            db.add(outfit)
            db.flush()
            
            for position, outfit_item in enumerate(outfit_items):
                outfit_item_record = OutfitItem(
                    outfit_id=outfit.id,
                    item_id=outfit_item.id,
                    position=position
                )
                db.add(outfit_item_record)
            created_count += 1
        
        db.commit()
        logger.info(f"✅ Generated {created_count}/{len(new_item_outfits)} outfits with new item (avg score: {np.mean([s for _, s, _ in new_item_outfits]) if new_item_outfits else 0:.3f})")
        return created_count
        
    except Exception as e:
        logger.error(f"❌ Error generating outfits: {e}", exc_info=True)
