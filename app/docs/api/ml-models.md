# ML Models API

Machine learning model endpoints for managing personal models and training.

## Overview

The ML Models API provides endpoints for:
- Checking personal model status
- Triggering manual training
- Retrieving model statistics
- Resetting models
- Viewing training history

**Key Concepts:**
- Base Models: Pre-trained, shared across all users
- Personal Models: Per-user copies trained on user ratings
- Auto-Training: Automatic after every 10 rated outfits
- Model Versioning: History of model iterations
- Training Metrics: Accuracy, loss, training time

## Base Models

### Available Models

| Model | Purpose | Input | Output |
|-------|---------|-------|--------|
| **HGNN** | Outfit compatibility | Item embeddings | 0-1 score |
| **CLIP** | Image embeddings | Images | 768-dim vector |
| **ResNet50** | Category classification | Images | Category label |
| **Attribute Encoder** | Attribute detection | Images | Attributes |

### Model Details

**HGNN (Heterogeneous Graph Neural Network)**
- Architecture: GNN with heterogeneous nodes (items, categories)
- Training: Learns compatibility patterns
- Output: Compatibility score 0-1
- Location: `app/models/base/hgnn.pth`

**CLIP (Contrastive Language-Image Pre-training)**
- Purpose: Generate embeddings for items
- Dimensions: 768-dimensional vectors
- Pre-trained: OpenAI model
- Used for: Similarity matching, outfit compatibility

**ResNet50 (Residual Network)**
- Purpose: Classify clothing items
- Categories: 50+ clothing types
- Pre-trained: ImageNet
- Used for: Auto-tagging items

## Endpoints

### Get Model Status

**Endpoint:** `GET /models/status`

Retrieves the status of personal and base models.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "personal_models": {
    "hgnn": {
      "exists": true,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-02T15:30:00Z",
      "training_count": 1,
      "accuracy": 0.87,
      "training_time_ms": 5230
    },
    "clip": {
      "exists": false,
      "reason": "CLIP uses base model"
    },
    "resnet50": {
      "exists": false,
      "reason": "ResNet50 uses base model"
    }
  },
  "base_models": {
    "hgnn": {
      "version": "1.0",
      "loaded": true,
      "size_mb": 45.2
    },
    "clip": {
      "version": "1.0",
      "loaded": true,
      "size_mb": 340.5
    },
    "resnet50": {
      "version": "1.0",
      "loaded": true,
      "size_mb": 98.3
    }
  },
  "auto_training": {
    "enabled": true,
    "trigger_count": 10,
    "current_count": 7,
    "next_training_at": "3 more ratings"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/models/status \
  -H "Authorization: Bearer {token}"
```

---

### Get Model Statistics

**Endpoint:** `GET /models/stats`

Retrieves detailed statistics about personal models.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "personal_model": {
    "type": "hgnn",
    "created_at": "2024-01-01T12:00:00Z",
    "training_history": [
      {
        "training_num": 1,
        "timestamp": "2024-01-02T15:30:00Z",
        "ratings_processed": 10,
        "accuracy": 0.87,
        "loss": 0.245,
        "training_time_ms": 5230,
        "improvement": "+3.2%"
      }
    ],
    "total_ratings": 10,
    "avg_accuracy": 0.87,
    "model_path": "~/.fashion_wardrobe_app/models/personal/{user_id}/hgnn.pth"
  },
  "embedding_stats": {
    "items_with_embeddings": 25,
    "embedding_dimension": 768,
    "last_update": "2024-01-02T15:35:00Z"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/models/stats \
  -H "Authorization: Bearer {token}"
```

---

### Train Model Manually

**Endpoint:** `POST /models/train`

Manually triggers model training (usually automatic).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "model_type": "hgnn",
  "force": false
}
```

**Request Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| model_type | string | Which model to train (hgnn) |
| force | boolean | Force training even if < 10 ratings |

**Response (200):**
```json
{
  "model_type": "hgnn",
  "status": "completed",
  "training_time_ms": 5230,
  "ratings_processed": 10,
  "accuracy": 0.87,
  "improvement": "+3.2%",
  "message": "Model trained successfully",
  "next_training_at": "10 more ratings"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/models/train \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"model_type": "hgnn"}'
```

---

### Reset Personal Model

**Endpoint:** `POST /models/reset`

Resets personal model to base model, clearing training history.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "model_type": "hgnn"
}
```

**Response (200):**
```json
{
  "model_type": "hgnn",
  "status": "reset",
  "message": "Model reset to base version",
  "training_history_cleared": true,
  "next_training_available": "After 10 ratings"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/models/reset \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"model_type": "hgnn"}'
```

---

### Get Training History

**Endpoint:** `GET /models/training-history`

Retrieves complete training history for personal models.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Number of records (default: 20) |
| skip | integer | Offset for pagination |

**Response (200):**
```json
{
  "total": 3,
  "training_history": [
    {
      "training_num": 3,
      "timestamp": "2024-01-05T10:15:00Z",
      "ratings_processed": 10,
      "model_path": "~/.fashion_wardrobe_app/models/personal/{uid}/hgnn_v3.pth",
      "metrics": {
        "accuracy": 0.92,
        "loss": 0.189,
        "improvement": "+2.1%"
      },
      "training_time_ms": 4850
    },
    {
      "training_num": 2,
      "timestamp": "2024-01-03T14:45:00Z",
      "ratings_processed": 10,
      "model_path": "~/.fashion_wardrobe_app/models/personal/{uid}/hgnn_v2.pth",
      "metrics": {
        "accuracy": 0.90,
        "loss": 0.210,
        "improvement": "+2.5%"
      },
      "training_time_ms": 5120
    },
    {
      "training_num": 1,
      "timestamp": "2024-01-02T15:30:00Z",
      "ratings_processed": 10,
      "model_path": "~/.fashion_wardrobe_app/models/personal/{uid}/hgnn_v1.pth",
      "metrics": {
        "accuracy": 0.87,
        "loss": 0.245,
        "improvement": "+3.2%"
      },
      "training_time_ms": 5230
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/models/training-history?limit=10" \
  -H "Authorization: Bearer {token}"
```

---

### Compare Models

**Endpoint:** `GET /models/compare`

Compares personal model with base model performance.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "comparison": {
    "base_model": {
      "type": "hgnn",
      "accuracy": 0.84,
      "characteristics": "General compatibility"
    },
    "personal_model": {
      "type": "hgnn",
      "accuracy": 0.92,
      "characteristics": "Personalized to user preferences",
      "improvement": "+8%"
    },
    "analysis": {
      "personal_is_better": true,
      "improvement_percent": 8.0,
      "recommendation": "Continue using personal model"
    }
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/models/compare \
  -H "Authorization: Bearer {token}"
```

---

## Training Details

### Auto-Training Triggers

The system has **three automatic training triggers** that work together:

#### 1. HGNN Personal Model (Every 10 Ratings Per-User)

When a user rates an outfit, the system automatically trains their personalized HGNN model:

**Trigger Condition:** `user_ratings_since_last_training == 10`

**Process Flow:**
```
User rates outfit
    ↓
Rating counter incremented
    ↓
If counter == 10: ✓ TRIGGER
    ├── Load personal HGNN model (or create from base)
    ├── Gather last 10 rated outfits
    ├── Extract outfit embeddings (768-dim vectors)
    ├── Prepare training labels (user ratings: 0-1)
    ├── Train model for 5 epochs
    ├── Evaluate accuracy on rating data
    ├── Calculate metrics (MSE, MAE, accuracy)
    ├── Save as hgnn_v{N}.pth with timestamp
    ├── Reset counter to 0
    └── Next rating (rating #11) uses improved personal model
```

**Code Location:** `app/backend/routes/outfits.py` - `rate_outfit()` endpoint

**Implementation:**
```python
def rate_outfit(wardrobe_id, outfit_id, rating, user, db):
    # Store rating
    outfit.user_rating = rating
    db.commit()
    
    # Automatically manages training via preference learner manager
    learner_manager = get_preference_learner_manager()
    outfit_tensor = extract_outfit_embedding(outfit)
    
    # This internally checks: if count % 10 == 0 → auto-train personal model
    learner_manager.save_outfit_rating(user.username, outfit_tensor, rating)
```

**Characteristics:**
- **Scope:** Per-user (personalized models)
- **Frequency:** Every 10 ratings per user
- **Model:** HGNN (outfit compatibility scorer)
- **Output:** `personal/{username}/hgnn_v{N}.pth`
- **Async:** Background task to avoid blocking API
- **Training Time:** ~5 seconds per training cycle

---

#### 2. Tagger Fine-Tuning (Every 100 Category Corrections)

When users correct item categories, the system automatically fine-tunes the hierarchical tagger:

**Trigger Condition:** `total_user_corrections % 100 == 0`

**Process Flow:**
```
User corrects item category (marks as correction)
    ↓
Correction saved to ItemChange table
    ↓
If total_corrections == 100: ✓ TRIGGER (Global - shared across all users)
    ├── Collect all 100 user corrections
    ├── Extract CLIP embeddings from corrected items
    ├── Prepare training samples with original/corrected categories
    ├── Fine-tune hierarchical tagger for 5 epochs
    ├── Update learned weights in tagger_finetuned.pt
    ├── Save training history JSON with timestamp
    ├── Reset counter to 0
    └── Next correction (#101) uses improved tagger predictions
```

**Code Location:** `app/backend/routes/items.py` - `update_item()` endpoint

**Implementation:**
```python
def update_item(wardrobe_id, item_id, item_update, user, db):
    # Update item categories
    item.main_category_indices = item_update.main_category_indices
    
    # Track if this is a user correction
    if item_update.is_correction:
        change = ItemChange(
            user_id=user.id,
            item_id=item.id,
            original_main_category_indices=old_categories,
            corrected_main_category_indices=new_categories,
            is_user_feedback=True
        )
        db.add(change)
        db.commit()
        
        # Check trigger: every 100 corrections
        correction_count = db.query(ItemChange).filter(
            ItemChange.is_user_feedback == True
        ).count()
        
        if correction_count % 100 == 0 and correction_count > 0:
            # Gather all corrections for training
            all_corrections = db.query(ItemChange).filter(
                ItemChange.is_user_feedback == True
            ).all()
            
            # Prepare training samples
            training_samples = []
            for change in all_corrections:
                item = db.query(Item).filter(Item.id == change.item_id).first()
                if item and item.img_embedding:
                    training_samples.append({
                        'embedding': np.array(item.img_embedding),
                        'original_main': change.original_main_category_indices or [],
                        'corrected_main': change.corrected_main_category_indices or [],
                        'confidence': change.confidence_feedback or 1.0
                    })
            
            # Train tagger
            tagger_learner = get_tagger_feedback_learner()
            tagger_learner.train_on_corrections(training_samples, epochs=5)
```

**Characteristics:**
- **Scope:** Global (shared across all users)
- **Frequency:** Every 100 total corrections (cumulative)
- **Model:** Hierarchical Tagger (category classifier)
- **Output:** `tagger_finetuned.pt` + `tagger_training_history.json`
- **Training Time:** ~8 seconds per training cycle
- **Benefit:** Improves category auto-tagging for all users

---

#### 3. HGNN Base Model Training (Every 100 Ratings Global)

When users rate outfits, the system automatically improves the shared base model:

**Trigger Condition:** `total_global_ratings % 100 == 0`

**Process Flow:**
```
User #1 rates outfit (rating count = 1)
    ↓
User #2 rates outfit (rating count = 2)
    ├── ... (other users)
    ↓
User #N rates outfit (rating count = 100) ✓ TRIGGER
    ├── Collect all 100 ratings from all users combined
    ├── Extract outfit embeddings (768-dim)
    ├── Prepare training data with ratings as targets
    ├── Fine-tune shared base HGNN for 3 epochs
    ├── Update base model weights in base_model_finetuned.pt
    ├── Save training history with global rating count
    ├── Clear ratings buffer
    ├── Reset counter to 0
    └── Rating #101: Improved base model becomes new default
```

**Code Location:** `app/models/user_preference_learner.py`
- **Class:** `PreferenceLearnerManager`
- **Methods:** `save_outfit_rating()` + `_train_base_model()`

**Implementation:**
```python
class PreferenceLearnerManager:
    """Manages all user HGNN models and trains base model from global ratings."""
    
    def save_outfit_rating(self, username: str, outfit: torch.Tensor, 
                          user_score: float) -> None:
        """Save user's rating and check for base model training trigger."""
        learner = self.get_learner(username)
        learner.save_rating(outfit, user_score)
        
        # Track for base model training
        self.global_rating_count += 1
        self.base_model_ratings_buffer.append({
            'username': username,
            'outfit': outfit.cpu().detach().clone(),
            'score': user_score
        })
        
        # Train base model every 100 global ratings
        if self.global_rating_count % 100 == 0:
            self._train_base_model()
    
    def _train_base_model(self) -> None:
        """Train base HGNN on all collected ratings from all users."""
        # Collects 100 ratings from all users
        # Fine-tunes base model for 3 epochs
        # Updates base_model_finetuned.pt
        # Personal models inherit improvements on next training
```

**Characteristics:**
- **Scope:** Global (shared across all users)
- **Frequency:** Every 100 total ratings (cumulative across all users)
- **Model:** HGNN base model (outfit compatibility scorer)
- **Output:** `base_model_finetuned.pt` + `base_model_training_history.json`
- **Training Time:** ~5 seconds per training cycle
- **Benefit:** Improves outfit scoring for ALL users by learning from collective data
- **Multiplier Effect:** New personal models copy from improved base model

---

### Training Metrics Comparison

| Metric | HGNN Personal (10 ratings) | Tagger (100 corrections) | HGNN Base (100 ratings) |
|--------|---|---|---|
| **Trigger** | Every 10 ratings per user | Every 100 corrections (global) | Every 100 ratings (global) |
| **Scope** | Per-user personalized | Global (all users) | Global (all users) |
| **Model Type** | HGNN outfit scorer | Category classifier | HGNN outfit scorer |
| **Training Data** | One user's rated outfits | All user corrections combined | All users' ratings combined |
| **Feature Dim** | 768 (outfit embeddings) | 512 (CLIP embeddings) | 768 (outfit embeddings) |
| **Output Type** | Compatibility scores | Category predictions | Compatibility scores |
| **Epochs** | 5 | 5 | 3 |
| **Model File** | `personal/{username}/hgnn_v{N}.pth` | `tagger_finetuned.pt` | `base_model_finetuned.pt` |
| **History Tracking** | Per-user training log | Global JSON log | Global JSON log |
| **Learning Rate** | 0.001 | 0.0001 | 0.00001 |
| **Async Task** | Yes (non-blocking) | Yes (non-blocking) | Yes (non-blocking) |
| **Benefits** | Better personal recommendations | Better auto-tagging | Improved base for all users |

### Manual Training

Users and admins can also trigger training manually via API endpoints (see endpoints section above).

### Training Metrics

| Metric | Description | Value |
|--------|-------------|-------|
| **Accuracy** | Prediction accuracy on test data | 0.0-1.0 |
| **MSE** | Mean squared error | Lower is better |
| **MAE** | Mean absolute error | Lower is better |
| **Loss** | Training loss value | Decreases over epochs |
| **Improvement** | vs previous version | % change |
| **Time** | Training duration | milliseconds |
| **Epochs** | Training iterations | 3-5 (depends on model) |

### Model Versioning

Personal models are versioned:
```
hgnn_base.pth          ← Base model
hgnn_v1.pth (2024-01-02)   ← First training
hgnn_v2.pth (2024-01-03)   ← Second training
hgnn_v3.pth (2024-01-05)   ← Third training
```

Latest version always in use.

---

## Model Management Workflow

### 1. Check Status

```bash
curl -X GET http://localhost:8000/models/status \
  -H "Authorization: Bearer {token}"
```

Response shows if personal model exists and auto-training status.

### 2. Rate Outfits

```bash
# Rate 10 outfits (in your app)
# Auto-training triggers after 10th rating
```

### 3. View Statistics

```bash
curl -X GET http://localhost:8000/models/stats \
  -H "Authorization: Bearer {token}"
```

Shows training history and accuracy metrics.

### 4. Monitor Improvements

```bash
curl -X GET http://localhost:8000/models/compare \
  -H "Authorization: Bearer {token}"
```

Compare personal vs base model performance.

---

## Best Practices

✅ Rate outfits consistently for better training  
✅ Provide diverse training examples (different occasions)  
✅ Monitor accuracy improvements over time  
✅ Reset model if it's not improving  
✅ Train with variety of item combinations  
✅ Review training history regularly  

---

## Troubleshooting

### Slow Training

**Cause:** Large item count or slow hardware  
**Solution:** Manual training happens in background; patience recommended

### Low Accuracy

**Cause:** Insufficient or inconsistent ratings  
**Solution:** Rate more outfits with consistent preferences

### Model Not Training

**Cause:** < 10 ratings, < 3 items, or disabled  
**Solution:** Rate more outfits (need 10 minimum) and check status

---

## Next Steps

- Learn about [Outfits API](outfits.md)
- Explore [Items API](items.md)
- Read [Error Handling](errors.md)
