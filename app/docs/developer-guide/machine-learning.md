# Developer Guide - Machine Learning

ML models, training pipeline, and neural networks.

## Models Overview

### HGNN (Heterogeneous Graph Neural Network)

**Purpose:** Outfit compatibility scoring

**Architecture:**
- Heterogeneous graph with item and category nodes
- Graph convolution layers
- Compatibility prediction

**Input:**
- Item embeddings (768-dimensional CLIP vectors)
- Item categories
- Item attributes

**Output:**
- Compatibility score (0-1)
- Confidence metric

**Location:**
```
app/models/base/hgnn.pth (45 MB)
app/models/personal/{username}/hgnn_v1.pth (personalized)
```

### CLIP (Contrastive Language-Image Pre-training)

**Purpose:** Generate item embeddings

**Architecture:**
- Vision Transformer encoder
- Text-image alignment
- 768-dimensional outputs

**Input:**
- Item images (RGB)

**Output:**
- 768-dimensional embedding vector

**Location:**
```
app/models/base/clip.pth (340 MB)
```

**Usage:**
```python
from app.models.load_models import load_clip_model

clip_model = load_clip_model()
image_tensor = preprocess_image("item.jpg")
embedding = clip_model.encode(image_tensor)  # 768-dim vector
```

### ResNet50 (Residual Network)

**Purpose:** Item category classification

**Architecture:**
- Deep residual network
- 50 layers
- ImageNet pre-trained

**Input:**
- Item images

**Output:**
- 50+ clothing categories

**Location:**
```
app/models/base/resnet50.pth (98 MB)
```

**Usage:**
```python
from app.models.load_models import load_resnet50_model

resnet = load_resnet50_model()
category = resnet.classify(image_tensor)
```

---

## Model Loading & Caching

### Lazy Loading

```python
from typing import Dict
import torch

# Global cache
_models_cache: Dict[str, torch.nn.Module] = {}

def get_hgnn_model():
    """Load HGNN model (lazy loading)"""
    if "hgnn" not in _models_cache:
        print("Loading HGNN model...")
        model = torch.load("models/base/hgnn.pth", map_location="cpu")
        model.eval()
        _models_cache["hgnn"] = model
    return _models_cache["hgnn"]

def get_clip_model():
    """Load CLIP model (lazy loading)"""
    if "clip" not in _models_cache:
        print("Loading CLIP model...")
        model = load_clip_model()
        _models_cache["clip"] = model
    return _models_cache["clip"]

def get_resnet50_model():
    """Load ResNet50 model (lazy loading)"""
    if "resnet50" not in _models_cache:
        print("Loading ResNet50 model...")
        model = load_resnet50_model()
        _models_cache["resnet50"] = model
    return _models_cache["resnet50"]
```

### Device Selection

```python
import torch

def get_device():
    """Get optimal device (GPU if available, else CPU)"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

# Move model to device
device = get_device()
model = get_hgnn_model()
model.to(device)

# Move input to device
input_tensor = input_tensor.to(device)
```

---

## Item Embedding Generation

### Embedding Pipeline

```python
from PIL import Image
import torch
import numpy as np

async def generate_item_embedding(image_path: str) -> np.ndarray:
    """
    Generate embedding for item image
    1. Load image
    2. Preprocess
    3. Pass through CLIP
    4. Return 768-dim vector
    """
    
    # Load image
    image = Image.open(image_path).convert("RGB")
    
    # Preprocess (resize, normalize)
    image_tensor = preprocess_image(image)
    
    # Get CLIP model
    clip_model = get_clip_model()
    
    # Generate embedding
    with torch.no_grad():
        embedding = clip_model.encode(image_tensor)
    
    # Convert to numpy
    embedding_np = embedding.cpu().numpy().flatten()
    
    # Normalize
    embedding_np = embedding_np / np.linalg.norm(embedding_np)
    
    return embedding_np

def preprocess_image(image: Image.Image) -> torch.Tensor:
    """Preprocess image for CLIP"""
    
    # Resize to 224x224
    image = image.resize((224, 224))
    
    # Convert to tensor
    image_tensor = torch.from_numpy(np.array(image)).float()
    
    # Normalize ImageNet statistics
    mean = torch.tensor([0.485, 0.456, 0.406])
    std = torch.tensor([0.229, 0.224, 0.225])
    
    image_tensor = image_tensor / 255.0
    image_tensor = (image_tensor - mean) / std
    
    # Add batch dimension
    image_tensor = image_tensor.unsqueeze(0)
    
    return image_tensor
```

### Embedding Storage

```python
# In database
item.embedding = embedding_vector.tolist()  # Store as list in JSON
db.commit()

# Retrieve
embedding = np.array(item.embedding)  # Convert back to numpy

# Similarity calculation
def cosine_similarity(emb1, emb2):
    """Calculate cosine similarity between embeddings"""
    return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
```

---

## Outfit Generation

### HGNN Scoring

```python
import torch
import numpy as np

def generate_outfit(wardrobe_items, num_items=3):
    """
    Generate outfit using HGNN
    1. Get all item embeddings
    2. Score all combinations
    3. Select best
    """
    
    # Extract embeddings
    embeddings = [np.array(item.embedding) for item in wardrobe_items]
    
    # Score all combinations
    best_score = -1
    best_combo = None
    
    from itertools import combinations
    
    for combo in combinations(range(len(wardrobe_items)), num_items):
        items = [wardrobe_items[i] for i in combo]
        score = score_outfit(embeddings, combo)
        
        if score > best_score:
            best_score = score
            best_combo = combo
    
    selected_items = [wardrobe_items[i] for i in best_combo]
    
    return {
        "items": selected_items,
        "score": float(best_score),
        "combo": best_combo
    }

def score_outfit(embeddings, combo):
    """
    Score outfit combination using HGNN
    """
    
    # Stack embeddings for selected items
    outfit_embeddings = torch.tensor([
        embeddings[i] for i in combo
    ]).float()
    
    # Get HGNN model
    model = get_hgnn_model()
    
    # Score through HGNN
    with torch.no_grad():
        score = model.score(outfit_embeddings)
    
    return score.item()
```

### Color Harmony

```python
import colorsys

def color_harmony_score(colors: List[str]) -> float:
    """
    Score color harmony in outfit
    Based on color theory principles
    """
    
    # Convert colors to HSV
    hsv_colors = []
    for color in colors:
        rgb = hex_to_rgb(color)
        hsv = colorsys.rgb_to_hsv(*rgb)
        hsv_colors.append(hsv)
    
    # Calculate hue spread
    hues = [hsv[0] * 360 for hsv in hsv_colors]
    hue_spread = max(hues) - min(hues)
    
    # Score based on spread
    # Perfect harmony: hues 120° apart (triadic) or close (analogous)
    if hue_spread < 30:
        harmony = 1.0  # Monochromatic
    elif hue_spread < 90:
        harmony = 0.95  # Analogous
    elif hue_spread < 150:
        harmony = 0.85  # Complementary
    elif hue_spread < 180:
        harmony = 0.80  # Triadic
    else:
        harmony = 0.70  # Scattered
    
    return harmony

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex to RGB"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
```

---

## Personal Model Training

### Training Pipeline

```python
import torch
from torch.utils.data import DataLoader, TensorDataset

async def train_personal_model(username: str, ratings_data: List[dict]):
    """
    Train personalized HGNN model
    
    1. Prepare training data
    2. Load base model
    3. Fine-tune on user ratings
    4. Save personalized model
    """
    
    # Prepare training data
    X_train = []  # Outfit embeddings
    y_train = []  # Ratings (normalized to 0-1)
    
    for rating in ratings_data:
        outfit = rating["outfit"]
        score = rating["score"]
        
        # Create outfit embedding (concatenate item embeddings)
        outfit_emb = create_outfit_embedding(outfit)
        X_train.append(outfit_emb)
        
        # Normalize rating 1-5 to 0.2-1.0
        normalized_score = (score * 0.2)
        y_train.append(normalized_score)
    
    # Convert to tensors
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    
    # Create data loader
    dataset = TensorDataset(X_train, y_train)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Load base model
    base_model = get_hgnn_model()
    personal_model = copy.deepcopy(base_model)
    personal_model.train()
    
    # Training loop
    optimizer = torch.optim.Adam(personal_model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()
    
    num_epochs = 5
    for epoch in range(num_epochs):
        total_loss = 0
        
        for batch_X, batch_y in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            predictions = personal_model(batch_X)
            
            # Calculate loss
            loss = criterion(predictions, batch_y.unsqueeze(1))
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
    
    # Evaluate on test set
    personal_model.eval()
    with torch.no_grad():
        test_predictions = personal_model(X_train)
        accuracy = calculate_accuracy(test_predictions, y_train)
    
    # Save model
    save_personal_model(username, personal_model, accuracy)
    
    return {
        "status": "completed",
        "accuracy": accuracy,
        "epochs": num_epochs,
        "training_samples": len(X_train)
    }

def create_outfit_embedding(outfit):
    """Create combined embedding from item embeddings"""
    embeddings = [np.array(item.embedding) for item in outfit.items]
    # Mean pooling
    combined = np.mean(embeddings, axis=0)
    return combined

def calculate_accuracy(predictions, targets):
    """Calculate prediction accuracy"""
    # Round to nearest 0.2 (maps to star rating)
    pred_rounded = torch.round(predictions * 5) / 5
    target_rounded = torch.round(targets * 5) / 5
    
    accuracy = (pred_rounded == target_rounded).float().mean()
    return accuracy.item()
```

### Auto-Training Triggers

The system has **three automatic training triggers**:

#### 1. HGNN Personal Model Training (Every 10 Ratings Per-User)

**Trigger Location:** `app/backend/routes/outfits.py` - `rate_outfit()` endpoint

When a user rates an outfit, the system automatically trains their personalized HGNN model every 10 ratings:

```python
# In rate_outfit endpoint (outfits.py)
def rate_outfit(
    wardrobe_id: int,
    outfit_id: int,
    rating: float = Query(..., ge=0, le=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate outfit and trigger personalized model training every 10 ratings"""
    
    # Store rating
    outfit.user_rating = rating
    db.commit()
    
    # Automatically trigger training every 10 ratings
    learner_manager = get_preference_learner_manager()
    learner_manager.save_outfit_rating(user.username, outfit_tensor, rating)
    # Internally checks: if rating_count % 10 == 0 → train_personal_model()
```

**Process:**
```
User rates outfit
    ↓
Rating #1 → Saved
    ↓
Rating #2-9 → Saved
    ↓
Rating #10 ✓ TRIGGER
    ├── Load personal HGNN model (or create from base)
    ├── Gather last 10 rated outfits
    ├── Extract features from outfit embeddings
    ├── Train for 5 epochs on rating data
    ├── Evaluate accuracy
    ├── Save as hgnn_v{N}.pth with metrics
    ├── Reset counter to 0
    └── Rating #11 uses new personal model
```

**Implementation Code:**
```python
async def check_and_trigger_training(
    user_id: UUID,
    db: Session
):
    """
    Check if user reached 10 ratings and trigger training
    """
    
    # Get user's rated outfits
    rated_outfits = db.query(Outfit).filter(
        Outfit.wardrobe_id.in_(
            db.query(Wardrobe.id).filter(Wardrobe.user_id == user_id)
        ),
        Outfit.rating != None
    ).all()
    
    # Check if we have 10 new ratings since last training
    user_data = get_user_training_data(user_id)
    
    if len(rated_outfits) >= 10 and not user_data.get("trained_recently"):
        # Trigger async training
        await train_personal_model(
            username=get_user(user_id).username,
            ratings_data=prepare_training_data(rated_outfits)
        )
        
        # Mark training as done
        update_training_status(user_id, completed=True)
```

---

#### 2. Tagger Fine-Tuning (Every 100 Category Corrections)

**Trigger Location:** `app/backend/routes/items.py` - `update_item()` endpoint

When users correct item categories, the system automatically fine-tunes the hierarchical tagger every 100 corrections (shared across all users):

```python
# In update_item endpoint (items.py)
@router.put("/{wardrobe_id}/items/{item_id}", response_model=ItemResponse)
def update_item(
    wardrobe_id: int,
    item_id: int,
    item_update: ItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update item and trigger tagger retraining every 100 user corrections"""
    
    # Track if user is correcting categories
    if item_update.is_correction and has_category_changes:
        # Save change record
        change = ItemChange(
            user_id=user.id,
            item_id=item.id,
            original_main_category_indices=old_main_categories,
            corrected_main_category_indices=new_main_categories,
            # ... other category changes
            is_user_feedback=True
        )
        db.add(change)
        db.commit()
        
        # Trigger retraining every 100 user corrections
        user_feedback_count = db.query(ItemChange).filter(
            ItemChange.is_user_feedback == True
        ).count()
        
        if user_feedback_count % 100 == 0 and user_feedback_count > 0:
            # Collect all user corrections for retraining
            all_corrections = db.query(ItemChange).filter(
                ItemChange.is_user_feedback == True
            ).all()
            
            training_samples = []
            for change in all_corrections:
                item = db.query(Item).filter(Item.id == change.item_id).first()
                if item and item.img_embedding:
                    sample = {
                        'embedding': np.array(item.img_embedding),
                        'original_main': change.original_main_category_indices or [],
                        'original_sub': change.original_sub_category_indices or [],
                        'corrected_main': change.corrected_main_category_indices or [],
                        'corrected_sub': change.corrected_sub_category_indices or [],
                        'confidence': change.confidence_feedback or 1.0
                    }
                    training_samples.append(sample)
            
            # Train tagger
            if len(training_samples) >= 2:
                tagger_learner = get_tagger_feedback_learner()
                result = tagger_learner.train_on_corrections(
                    training_samples,
                    epochs=5
                )
                print(f"✅ Tagger retrained on {len(training_samples)} corrections")
```

**Process:**
```
User corrects item category
    ↓
Correction #1 → Saved to ItemChange table
    ↓
Correction #2-99 → Saved
    ↓
Correction #100 ✓ TRIGGER
    ├── Collect all 100 user corrections
    ├── Extract embeddings from corrected items
    ├── Fine-tune hierarchical tagger for 5 epochs
    ├── Update learned weights in tagger_finetuned.pt
    ├── Save training history
    ├── Reset counter to 0
    └── Correction #101 uses improved tagger
```

**Key Differences:**

| Aspect | HGNN Personal (10 ratings) | Tagger (100 corrections) | HGNN Base (100 ratings) |
|--------|---------------|----------------------|------------------------|
| **Trigger** | Every 10 ratings per user | Every 100 corrections (global) | Every 100 ratings (global) |
| **Scope** | Per-user personalized | Shared across all users | Shared across all users |
| **Model** | HGNN copy (outfit compatibility) | Hierarchical Tagger (category classification) | HGNN base (outfit compatibility) |
| **Training Data** | User's rated outfits | User corrections to categories | All users' ratings combined |
| **Storage** | `personal/{username}/hgnn_vN.pth` | `tagger_finetuned.pt` | `base_model_finetuned.pt` |
| **Epochs** | 5 | 5 | 3 |
| **Input Features** | Outfit embeddings (768-dim) | Item embeddings (512-dim CLIP) | Outfit embeddings (768-dim) |
| **Output** | Compatibility scores (0-1) | Category predictions | Compatibility scores (0-1) |
| **Benefits** | Better personal recommendations | Better category auto-tagging for all | Improved base model for all users |

---

#### 3. HGNN Base Model Training (Every 100 Ratings Global)

**Trigger Condition:** `total_ratings_across_all_users % 100 == 0`

**Process Flow:**
```
User #1 rates outfit
    ↓
User #2 rates outfit
    ├── ...
    ↓
User #N rates outfit
    ↓
If total_global_ratings == 100: ✓ TRIGGER (Shared - affects all users)
    ├── Collect all 100 ratings from all users
    ├── Extract outfit embeddings (768-dim)
    ├── Prepare training data with ratings as targets
    ├── Fine-tune shared base HGNN model for 3 epochs
    ├── Update base model weights in base_model_finetuned.pt
    ├── Save training history with timestamp
    ├── Clear ratings buffer
    ├── Reset counter to 0
    └── Rating #101: Improved base model is now default for all users
```

**Code Location:** `app/models/user_preference_learner.py`
- **Class:** `PreferenceLearnerManager`
- **Method:** `save_outfit_rating()` + `_train_base_model()`

**Implementation:**
```python
class PreferenceLearnerManager:
    """
    Manages all user HGNN models.
    Each user gets their own fine-tuned copy of the base HGNN.
    Trains the base model collectively every 100 ratings.
    """
    
    def save_outfit_rating(self, username: str, outfit: torch.Tensor, 
                          user_score: float) -> None:
        """Save user's rating and trigger base model training if needed."""
        learner = self.get_learner(username)
        learner.save_rating(outfit, user_score)
        
        # Track for base model training
        self.global_rating_count += 1
        self.base_model_ratings_buffer.append({
            'username': username,
            'outfit': outfit.cpu().detach().clone(),
            'score': user_score
        })
        
        # Train base model every 100 ratings
        if self.global_rating_count % 100 == 0:
            self._train_base_model()
    
    def _train_base_model(self) -> None:
        """Train the base HGNN model on collected ratings from all users."""
        if self.base_model is None or len(self.base_model_ratings_buffer) == 0:
            return
        
        logger.info(f"🎯 Base Model Training: Starting on {len(self.base_model_ratings_buffer)} ratings from all users")
        
        device = next(self.base_model.parameters()).device
        optimizer = torch.optim.AdamW(self.base_model.parameters(), lr=1e-5)
        criterion = torch.nn.MSELoss()
        
        # Training loop
        num_epochs = 3
        for epoch in range(num_epochs):
            for rating_data in self.base_model_ratings_buffer:
                outfit = rating_data['outfit'].to(device)
                target_score = torch.tensor([rating_data['score']], dtype=torch.float32, device=device)
                
                # Forward pass
                prediction = self.base_model(outfit.unsqueeze(0))
                
                # Compute loss
                loss = criterion(prediction.unsqueeze(0), target_score)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        
        # Save updated base model
        base_model_path = self.storage_path / "base_model_finetuned.pt"
        torch.save({
            'model_state_dict': self.base_model.state_dict(),
            'global_ratings': self.global_rating_count,
            'timestamp': datetime.now().isoformat()
        }, base_model_path)
        
        # Record training
        self.base_model_training_history.append({
            'global_ratings': self.global_rating_count,
            'num_samples': len(self.base_model_ratings_buffer),
            'timestamp': datetime.now().isoformat()
        })
        
        # Clear buffer
        self.base_model_ratings_buffer.clear()
        self._save_base_model_training_state()
        
        logger.info(f"✨ Base Model Training Complete: Trained on {len(self.base_model_ratings_buffer)} ratings")
```

**Characteristics:**
- **Scope:** Global (shared across all users)
- **Frequency:** Every 100 total ratings (cumulative across all users)
- **Model:** HGNN (outfit compatibility scorer)
- **Output:** `base_model_finetuned.pt`
- **Training Time:** ~5 seconds per training cycle
- **Benefit:** Improves outfit scoring for ALL users by learning from collective data
- **Backward Compatibility:** New personal models copy from improved base model

---

## Model Persistence

### Saving Models

```python
import torch
from datetime import datetime

def save_personal_model(
    username: str,
    model: torch.nn.Module,
    metrics: dict
):
    """Save personalized model with metadata"""
    
    # Create directory
    model_dir = MODELS_PATH / "personal" / username
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Get version number
    existing = list(model_dir.glob("hgnn_v*.pth"))
    version = len(existing) + 1
    
    # Save checkpoint
    model_path = model_dir / f"hgnn_v{version}.pth"
    
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "username": username
    }
    
    torch.save(checkpoint, model_path)
    
    # Also save as current version
    current_path = model_dir / "hgnn_latest.pth"
    torch.save(checkpoint, current_path)
    
    return str(model_path)
```

### Loading Personal Models

```python
def load_personal_model(username: str) -> torch.nn.Module:
    """Load user's personal model if exists"""
    
    model_dir = MODELS_PATH / "personal" / username
    latest = model_dir / "hgnn_latest.pth"
    
    if latest.exists():
        checkpoint = torch.load(latest, map_location="cpu")
        model = get_hgnn_model()  # Load base architecture
        model.load_state_dict(checkpoint["model_state_dict"])
        return model
    else:
        # Return base model if no personal model exists
        return get_hgnn_model()
```

---

## Evaluation & Metrics

### Training Metrics

```python
def calculate_metrics(predictions, targets):
    """Calculate training metrics"""
    
    # Mean Squared Error
    mse = np.mean((predictions - targets) ** 2)
    
    # Mean Absolute Error
    mae = np.mean(np.abs(predictions - targets))
    
    # Accuracy (round to nearest star)
    pred_stars = np.round(predictions * 5)
    target_stars = np.round(targets * 5)
    accuracy = np.mean(pred_stars == target_stars)
    
    return {
        "mse": float(mse),
        "mae": float(mae),
        "accuracy": float(accuracy)
    }
```

---

## Performance Optimization

### Batch Processing

```python
def score_outfits_batch(outfits, batch_size=32):
    """Score multiple outfits efficiently"""
    
    model = get_hgnn_model()
    model.eval()
    
    scores = []
    
    with torch.no_grad():
        for i in range(0, len(outfits), batch_size):
            batch = outfits[i:i+batch_size]
            
            # Create batch tensor
            batch_embeddings = torch.stack([
                torch.tensor(create_outfit_embedding(outfit))
                for outfit in batch
            ])
            
            # Score batch
            batch_scores = model(batch_embeddings)
            scores.extend(batch_scores.cpu().numpy().flatten())
    
    return scores
```

### GPU Support

```python
import torch

def use_gpu_if_available():
    """Configure GPU usage"""
    
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using GPU: {torch.cuda.get_device_name()}")
    else:
        device = torch.device("cpu")
        print("Using CPU")
    
    return device

# Configure model
device = use_gpu_if_available()
model = get_hgnn_model()
model.to(device)
```

---

## Future Enhancements

**Planned Improvements:**
- 🎯 Attention mechanisms for interpretability
- 📊 Ensemble models for better accuracy
- 🔄 Online learning (continuous updates)
- 🌍 Transfer learning from other domains
- 📈 Hyperparameter optimization
- 🚀 Distributed training

---

## Next Steps

- Read [Testing Strategy](testing.md)
- Explore [Code Style](code-style.md)
- Review [Database Design](database.md)
