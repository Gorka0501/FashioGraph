from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict
from datetime import datetime

# ==================== User Schemas ====================

class UserRegister(BaseModel):
    """User registration request."""
    username: str
    password: str


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str
    user_id: int
    username: str
    wardrobe_id: int | None = None


# ==================== Item Schemas ====================

class ItemCreate(BaseModel):
    """Create a new item (dataset-driven)."""
    node_id: int
    related_indices: Optional[List[int]] = None
    category_indices: Optional[List[int]] = None
    main_category_indices: Optional[List[int]] = None
    sub_category_indices: Optional[List[int]] = None
    img_embedding: Optional[List[float]] = None
    attr_embedding: Optional[List[float]] = None
    available: bool = True


class ItemUpdate(BaseModel):
    """Update an item."""
    related_indices: Optional[List[int]] = None
    category_indices: Optional[List[int]] = None
    main_category_indices: Optional[List[int]] = None
    sub_category_indices: Optional[List[int]] = None
    img_embedding: Optional[List[float]] = None
    attr_embedding: Optional[List[float]] = None
    available: Optional[bool] = None
    # Track if this is a user correction (for tagger improvement)
    is_correction: Optional[bool] = False


class ItemChangeResponse(BaseModel):
    """Item change/correction response."""
    id: int
    item_id: int
    user_id: int
    
    # Original predictions
    original_main_category_indices: Optional[List[int]]
    original_sub_category_indices: Optional[List[int]]
    original_category_indices: Optional[List[int]]
    original_related_indices: Optional[List[int]]
    
    # Corrections
    corrected_main_category_indices: Optional[List[int]]
    corrected_sub_category_indices: Optional[List[int]]
    corrected_category_indices: Optional[List[int]]
    corrected_related_indices: Optional[List[int]]
    
    confidence_feedback: Optional[float]
    notes: Optional[str]
    is_user_feedback: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemResponse(BaseModel):
    """Item response."""
    id: int
    node_id: int
    image_path: Optional[str]
    related_indices: Optional[List[int]]
    category_indices: Optional[List[int]]
    main_category_indices: Optional[List[int]]
    sub_category_indices: Optional[List[int]]
    img_embedding: Optional[List[float]]
    attr_embedding: Optional[List[float]]
    available: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Outfit Schemas ====================

class OutfitItemCreate(BaseModel):
    """Add item to outfit."""
    item_id: int
    score: Optional[float] = None


class OutfitCreate(BaseModel):
    """Create a new outfit."""
    item_ids: List[int] = []
    
    @field_validator('item_ids')
    @classmethod
    def no_duplicate_items(cls, v):
        """Ensure no duplicate item IDs in outfit."""
        if len(v) != len(set(v)):
            raise ValueError("Outfit cannot contain duplicate items")
        return v


class OutfitUpdate(BaseModel):
    """Update an outfit."""
    user_rating: Optional[float] = None
    system_rating: Optional[float] = None


class OutfitItemResponse(BaseModel):
    """Outfit item response with full item data."""
    item_id: int
    position: int
    score: Optional[float]
    item: ItemResponse

    model_config = ConfigDict(from_attributes=True)


class OutfitResponse(BaseModel):
    """Outfit response."""
    id: int
    user_rating: Optional[float]
    system_rating: Optional[float]
    created_at: datetime
    updated_at: datetime
    items: List[OutfitItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==================== Wardrobe Schemas ====================

class WardrobeResponse(BaseModel):
    """Wardrobe response (one per user)."""
    id: int
    created_at: datetime
    updated_at: datetime
    items_count: Optional[int] = 0
    outfits_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# ==================== Model Training Schemas ====================

class TrainingJobResponse(BaseModel):
    """Training job status response."""
    job_id: str
    status: str  # pending, training, completed, failed
    progress: int  # 0-100
    message: str
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingStatusResponse(BaseModel):
    """Training status detailed response."""
    job_id: str
    status: str
    progress: int
    message: str
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Storage Schemas ====================

class StorageSyncPlan(BaseModel):
    """Storage synchronization plan from backend."""
    model: Optional[Dict] = None
    images: Optional[Dict] = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class CacheReportRequest(BaseModel):
    """Desktop app reports what it has cached."""
    cached_model: bool
    cached_image_count: int
    cached_image_ids: List[int] = []
    total_cache_size_mb: float

    model_config = ConfigDict(from_attributes=True)
