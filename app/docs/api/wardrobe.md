# Wardrobe API

Wardrobe management endpoints for creating and managing clothing collections.

## Overview

A wardrobe is a user's collection of clothing. Each user has one main wardrobe that contains items (clothing pieces). The wardrobe system provides endpoints for creating, retrieving, updating, and deleting wardrobes.

**Key Concepts:**
- One wardrobe per user (one-to-one relationship)
- Wardrobes contain multiple items
- Items have categories, attributes, and embeddings
- Auto-tagging using ResNet50 classification

## Endpoints

### Create Wardrobe

**Endpoint:** `POST /wardrobes`

Creates a new wardrobe for the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "name": "Summer Collection 2024",
  "description": "Light clothes for warm weather"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Wardrobe name (1-100 chars) |
| description | string | No | Optional description |

**Response (201):**
```json
{
  "id": "uuid-string",
  "user_id": "user-uuid",
  "name": "Summer Collection 2024",
  "description": "Light clothes for warm weather",
  "item_count": 0,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/wardrobes \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Collection 2024",
    "description": "Light clothes for warm weather"
  }'
```

---

### Get All Wardrobes

**Endpoint:** `GET /wardrobes`

Retrieves all wardrobes for the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| skip | integer | Items to skip (pagination) |
| limit | integer | Items to return (default: 10) |

**Response (200):**
```json
{
  "total": 1,
  "wardrobes": [
    {
      "id": "uuid-string",
      "user_id": "user-uuid",
      "name": "Summer Collection 2024",
      "description": "Light clothes for warm weather",
      "item_count": 5,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-02T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/wardrobes?skip=0&limit=10" \
  -H "Authorization: Bearer {token}"
```

---

### Get Wardrobe by ID

**Endpoint:** `GET /wardrobes/{wardrobe_id}`

Retrieves a specific wardrobe by ID.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| wardrobe_id | string (UUID) | Wardrobe identifier |

**Response (200):**
```json
{
  "id": "uuid-string",
  "user_id": "user-uuid",
  "name": "Summer Collection 2024",
  "description": "Light clothes for warm weather",
  "item_count": 5,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-02T10:30:00Z",
  "items": [
    {
      "id": "item-uuid",
      "name": "Blue T-shirt",
      "category": "shirts",
      "color": "blue",
      "image_url": "http://localhost:8000/images/..."
    }
  ]
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 404 | NOT_FOUND | Wardrobe doesn't exist |
| 403 | FORBIDDEN | User doesn't own this wardrobe |

**Example:**
```bash
curl -X GET http://localhost:8000/wardrobes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}"
```

---

### Update Wardrobe

**Endpoint:** `PUT /wardrobes/{wardrobe_id}`

Updates a wardrobe's information.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "name": "Summer Collection 2024 (Updated)",
  "description": "Updated description"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | New wardrobe name |
| description | string | No | New description |

**Response (200):**
```json
{
  "id": "uuid-string",
  "user_id": "user-uuid",
  "name": "Summer Collection 2024 (Updated)",
  "description": "Updated description",
  "item_count": 5,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-03T15:45:00Z"
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/wardrobes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Collection 2024 (Updated)"
  }'
```

---

### Delete Wardrobe

**Endpoint:** `DELETE /wardrobes/{wardrobe_id}`

Deletes a wardrobe and all associated items.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| wardrobe_id | string (UUID) | Wardrobe to delete |

**Response (204):**
No content returned.

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 404 | NOT_FOUND | Wardrobe doesn't exist |
| 403 | FORBIDDEN | User doesn't own this wardrobe |

**Example:**
```bash
curl -X DELETE http://localhost:8000/wardrobes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}"
```

---

### Get Wardrobe Statistics

**Endpoint:** `GET /wardrobes/{wardrobe_id}/stats`

Retrieves statistics about a wardrobe.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "wardrobe_id": "uuid-string",
  "total_items": 25,
  "items_by_category": {
    "shirts": 8,
    "pants": 5,
    "dresses": 4,
    "jackets": 3,
    "shoes": 5
  },
  "items_by_color": {
    "blue": 6,
    "black": 5,
    "white": 4,
    "red": 3,
    "other": 7
  },
  "total_outfits": 42,
  "avg_compatibility_score": 0.82
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/wardrobes/550e8400-e29b-41d4-a716-446655440000/stats \
  -H "Authorization: Bearer {token}"
```

---

## Wardrobe Structure

### Wardrobe Object

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid",
  "name": "Summer Collection",
  "description": "Light clothes for warm weather",
  "item_count": 25,
  "items": [...],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-02T10:30:00Z"
}
```

### Item in Wardrobe

```json
{
  "id": "item-uuid",
  "wardrobe_id": "wardrobe-uuid",
  "name": "Blue Summer T-shirt",
  "category": "shirts",
  "subcategory": "casual",
  "color": "blue",
  "brand": "Nike",
  "image_url": "http://localhost:8000/images/...",
  "created_at": "2024-01-01T14:20:00Z"
}
```

---

## Workflow Example

### 1. Create a Wardrobe
```bash
curl -X POST http://localhost:8000/wardrobes \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Summer Wardrobe"}'
```

### 2. Get Wardrobe ID
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Summer Wardrobe",
  ...
}
```

### 3. Add Items to Wardrobe
See [Items API](items.md) for uploading items.

### 4. View Wardrobe Contents
```bash
curl -X GET http://localhost:8000/wardrobes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}"
```

### 5. Generate Outfits
See [Outfits API](outfits.md) for generating outfit recommendations.

---

## Best Practices

✅ Create meaningful wardrobe names  
✅ Use descriptions for organization  
✅ Organize items by category  
✅ Keep related items together  
✅ Delete unused wardrobes to save storage  

---

## Next Steps

- Learn about [Items API](items.md)
- Explore [Outfits API](outfits.md)
- Read [Error Handling](errors.md)
