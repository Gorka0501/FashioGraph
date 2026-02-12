# Outfits API

Outfit generation and management endpoints for creating recommendations and rating outfits.

## Overview

The Outfits API provides intelligent outfit recommendations using the HGNN (Heterogeneous Graph Neural Network) model. Features include:

- Neural network-based compatibility scoring
- User preference learning through ratings
- Outfit persistence and history
- Rating-based model auto-training
- Personalization per user

**Key Concepts:**
- Outfits: Collections of compatible items
- Compatibility Score: 0-1 (backend) or 0-5 stars (frontend)
- Auto-training: Triggered every 10 rated outfits
- User Models: Per-user personal HGNN copies

## Endpoints

### Generate Outfit

**Endpoint:** `POST /outfits/generate`

Generates an outfit recommendation from a wardrobe.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "wardrobe_id": "wardrobe-uuid",
  "occasion": "casual",
  "num_items": 3
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| wardrobe_id | string | Yes | Source wardrobe |
| occasion | string | No | Type: casual, formal, sports, evening |
| num_items | integer | No | Items per outfit (default: 3, max: 5) |
| exclude_items | array | No | Item IDs to exclude |

**Response (200):**
```json
{
  "id": "outfit-uuid",
  "wardrobe_id": "wardrobe-uuid",
  "items": [
    {
      "id": "item-uuid-1",
      "name": "Blue T-shirt",
      "category": "shirts",
      "image_url": "http://localhost:8000/images/..."
    },
    {
      "id": "item-uuid-2",
      "name": "Black Jeans",
      "category": "pants",
      "image_url": "http://localhost:8000/images/..."
    },
    {
      "id": "item-uuid-3",
      "name": "White Sneakers",
      "category": "shoes",
      "image_url": "http://localhost:8000/images/..."
    }
  ],
  "compatibility_score": 0.87,
  "occasion": "casual",
  "created_at": "2024-01-01T12:00:00Z",
  "rated": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/outfits/generate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "wardrobe_id": "550e8400-e29b-41d4-a716-446655440000",
    "occasion": "casual",
    "num_items": 3
  }'
```

---

### Get Outfit

**Endpoint:** `GET /outfits/{outfit_id}`

Retrieves details about a specific outfit.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| outfit_id | string (UUID) | Outfit identifier |

**Response (200):**
```json
{
  "id": "outfit-uuid",
  "wardrobe_id": "wardrobe-uuid",
  "items": [
    {
      "id": "item-uuid-1",
      "name": "Blue T-shirt",
      "category": "shirts",
      "color": "blue",
      "image_url": "http://localhost:8000/images/..."
    },
    {
      "id": "item-uuid-2",
      "name": "Black Jeans",
      "category": "pants",
      "color": "black",
      "image_url": "http://localhost:8000/images/..."
    },
    {
      "id": "item-uuid-3",
      "name": "White Sneakers",
      "category": "shoes",
      "color": "white",
      "image_url": "http://localhost:8000/images/..."
    }
  ],
  "compatibility_score": 0.87,
  "occasion": "casual",
  "rating": 4,
  "created_at": "2024-01-01T12:00:00Z",
  "rated_at": "2024-01-01T12:30:00Z"
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/outfits/outfit-uuid \
  -H "Authorization: Bearer {token}"
```

---

### List Outfits

**Endpoint:** `GET /outfits`

Retrieves outfit history for the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| wardrobe_id | string | Filter by wardrobe |
| rated | boolean | Only rated (true) or unrated (false) |
| occasion | string | Filter by occasion type |
| skip | integer | Pagination offset |
| limit | integer | Results per page (default: 20) |

**Response (200):**
```json
{
  "total": 42,
  "outfits": [
    {
      "id": "outfit-uuid-1",
      "items": [...],
      "compatibility_score": 0.87,
      "occasion": "casual",
      "rating": 4,
      "created_at": "2024-01-02T10:00:00Z"
    },
    {
      "id": "outfit-uuid-2",
      "items": [...],
      "compatibility_score": 0.92,
      "occasion": "formal",
      "rating": 5,
      "created_at": "2024-01-01T15:00:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/outfits?wardrobe_id=wardrobe-uuid&rated=true" \
  -H "Authorization: Bearer {token}"
```

---

### Rate Outfit

**Endpoint:** `POST /outfits/{outfit_id}/rate`

Rates an outfit (triggers auto-training after 10 ratings).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "rating": 4,
  "notes": "Nice combination, would wear this"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| rating | integer | Yes | Rating 0-5 stars (backend converts to 0-1) |
| notes | string | No | Optional feedback |

**Response (200):**
```json
{
  "id": "outfit-uuid",
  "rating": 4,
  "notes": "Nice combination, would wear this",
  "rated_at": "2024-01-02T12:00:00Z",
  "auto_training": {
    "triggered": false,
    "ratings_count": 7,
    "ratings_needed": 3
  }
}
```

**Auto-Training Response (when triggered):**
```json
{
  "id": "outfit-uuid",
  "rating": 4,
  "rated_at": "2024-01-02T12:00:00Z",
  "auto_training": {
    "triggered": true,
    "ratings_count": 10,
    "training_status": "completed",
    "training_time_ms": 5230
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/outfits/outfit-uuid/rate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "notes": "Nice combination"
  }'
```

---

### Get Outfit Recommendations

**Endpoint:** `GET /outfits/recommendations`

Gets AI-generated outfit recommendations based on user preferences.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| wardrobe_id | string | Target wardrobe |
| count | integer | Number of recommendations (default: 5) |
| occasion | string | Occasion type |

**Response (200):**
```json
{
  "recommendations": [
    {
      "id": "outfit-uuid-1",
      "items": [...],
      "compatibility_score": 0.95,
      "reason": "Matches your recent preferences",
      "created_at": "2024-01-02T12:00:00Z"
    },
    {
      "id": "outfit-uuid-2",
      "items": [...],
      "compatibility_score": 0.89,
      "reason": "Good color combination",
      "created_at": "2024-01-02T12:05:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/outfits/recommendations?wardrobe_id=wardrobe-uuid&count=5" \
  -H "Authorization: Bearer {token}"
```

---

## Rating System

### Frontend Display vs Backend Storage

| Frontend | Backend | Description |
|----------|---------|-------------|
| ⭐ 5 stars | 1.0 | Excellent fit |
| ⭐ 4 stars | 0.8 | Good fit |
| ⭐ 3 stars | 0.6 | Acceptable |
| ⭐ 2 stars | 0.4 | Poor fit |
| ⭐ 1 star | 0.2 | Unacceptable |
| ⭐ 0 stars (unrated) | N/A | Not yet rated |

### Conversion Logic

**Frontend to Backend:**
```python
backend_rating = (frontend_rating * 0.2)  # 5 → 1.0, 1 → 0.2
```

**Backend to Frontend:**
```python
frontend_rating = round(backend_rating * 5)  # 1.0 → 5, 0.2 → 1
```

---

## Auto-Training System

### Trigger Conditions

Auto-training activates when a user has:
- ✅ 10 rated outfits
- ✅ At least 3 different items in wardrobe

### Training Process

```
User rates outfit 10
    ↓
Rating counter reaches 10
    ↓
Load user's personal HGNN model
    ↓
Train on last 10 ratings
    ↓
Save updated model
    ↓
Reset counter to 0
    ↓
Next generation uses improved model
```

### Training Response

```json
{
  "training_status": "completed",
  "ratings_processed": 10,
  "model_accuracy": 0.89,
  "training_time_ms": 5230,
  "next_training_at": "10 more ratings"
}
```

---

## Compatibility Scoring

### How Scores are Calculated

1. **HGNN Model**: Neural network analyzes item combinations
2. **Color Harmony**: Evaluates color compatibility
3. **Category Compatibility**: Checks category appropriateness
4. **User Preference**: Uses personal model if trained
5. **Final Score**: Normalized to 0-1 range

### Score Interpretation

| Score | Interpretation | Recommendation |
|-------|-----------------|-----------------|
| 0.90-1.00 | Excellent | Definitely wear |
| 0.80-0.89 | Good | Great choice |
| 0.70-0.79 | Acceptable | Will look fine |
| 0.60-0.69 | Fair | Not ideal |
| < 0.60 | Poor | Consider alternatives |

---

## Outfit Occasions

Supported occasion types for outfit generation:

| Occasion | Use Case | Examples |
|----------|----------|----------|
| **casual** | Everyday wear | Coffee, shopping, friends |
| **formal** | Business/events | Work, interviews, meetings |
| **sports** | Athletic activity | Gym, running, sports |
| **evening** | Night out/events | Dinner, parties, dates |
| **beach** | Summer/outdoor | Beach, pool, outdoor |

---

## Workflow Example

### Complete Outfit Workflow

```
1. User has wardrobe with items
2. Generate outfit
   ↓
   POST /outfits/generate
   ↓
   Returns outfit + score

3. User rates outfit
   ↓
   POST /outfits/{id}/rate
   ↓
   Rating saved

4. After 10 ratings
   ↓
   Auto-training triggered
   ↓
   Personal model updated

5. Next generation
   ↓
   Uses improved personal model
   ↓
   Better recommendations
```

### API Example Flow

```bash
# 1. Generate outfit
OUTFIT=$(curl -X POST http://localhost:8000/outfits/generate \
  -H "Authorization: Bearer {token}" \
  -d '{"wardrobe_id": "wardrobe-uuid"}')

OUTFIT_ID=$(echo $OUTFIT | jq -r '.id')

# 2. Rate it
curl -X POST http://localhost:8000/outfits/$OUTFIT_ID/rate \
  -H "Authorization: Bearer {token}" \
  -d '{"rating": 4}'

# 3. Get recommendations
curl -X GET http://localhost:8000/outfits/recommendations \
  -H "Authorization: Bearer {token}" \
  -d '{"wardrobe_id": "wardrobe-uuid"}'
```

---

## Best Practices

✅ Rate outfits to improve recommendations  
✅ Mix different item categories  
✅ Provide quality item metadata  
✅ Try different occasions  
✅ Check recommendations after training  
✅ Remove poor-fitting items  

---

## Next Steps

- Learn about [ML Models API](ml-models.md)
- Explore [Items API](items.md)
- Read [Error Handling](errors.md)
