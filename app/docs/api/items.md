# Items API

Clothing item management endpoints for uploading, updating, and managing wardrobe items.

## Overview

Items represent individual clothing pieces in a wardrobe. Each item has:
- Visual data (image)
- Metadata (name, category, color, brand)
- Auto-generated embeddings (for outfit compatibility)
- Category classification (using ResNet50)

**Features:**
- Image upload with auto-sizing
- Automatic category detection
- CLIP embeddings for compatibility
- Per-item metadata storage
- Image URL retrieval

## Endpoints

### Upload Item

**Endpoint:** `POST /items`

Uploads a new clothing item with image.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| wardrobe_id | string (UUID) | Yes | Target wardrobe |
| name | string | Yes | Item name (e.g., "Blue T-shirt") |
| image | file | Yes | Image file (jpg, png, webp) |
| category | string | No | Override auto-detected category |
| color | string | No | Item color |
| brand | string | No | Item brand/manufacturer |
| size | string | No | Size (XS, S, M, L, XL) |
| notes | string | No | Additional notes |

**Response (201):**
```json
{
  "id": "item-uuid",
  "wardrobe_id": "wardrobe-uuid",
  "name": "Blue T-shirt",
  "category": "shirts",
  "color": "blue",
  "brand": "Nike",
  "image_url": "http://localhost:8000/images/user123/item-uuid.jpg",
  "embedding": [0.12, 0.45, 0.67, ...],
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer {token}" \
  -F "wardrobe_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "name=Blue Summer T-shirt" \
  -F "color=blue" \
  -F "brand=Nike" \
  -F "image=@/path/to/image.jpg"
```

---

### Get Item

**Endpoint:** `GET /items/{item_id}`

Retrieves details about a specific item.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| item_id | string (UUID) | Item identifier |

**Response (200):**
```json
{
  "id": "item-uuid",
  "wardrobe_id": "wardrobe-uuid",
  "name": "Blue T-shirt",
  "category": "shirts",
  "subcategory": "casual",
  "color": "blue",
  "brand": "Nike",
  "size": "M",
  "image_url": "http://localhost:8000/images/user123/item-uuid.jpg",
  "embedding": [0.12, 0.45, 0.67, ...],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-02T10:30:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 404 | NOT_FOUND | Item doesn't exist |
| 403 | FORBIDDEN | User doesn't own this item |

**Example:**
```bash
curl -X GET http://localhost:8000/items/item-uuid \
  -H "Authorization: Bearer {token}"
```

---

### Get Wardrobe Items

**Endpoint:** `GET /wardrobes/{wardrobe_id}/items`

Retrieves all items in a wardrobe.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category |
| color | string | Filter by color |
| skip | integer | Pagination offset |
| limit | integer | Results per page (default: 20) |

**Response (200):**
```json
{
  "total": 25,
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
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/wardrobes/wardrobe-uuid/items?category=shirts" \
  -H "Authorization: Bearer {token}"
```

---

### Update Item

**Endpoint:** `PUT /items/{item_id}`

Updates item metadata.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Navy Blue T-shirt",
  "color": "navy blue",
  "size": "L",
  "notes": "Favorite casual shirt"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | No | New item name |
| category | string | No | New category |
| color | string | No | New color |
| brand | string | No | New brand |
| size | string | No | New size |
| notes | string | No | New notes |

**Response (200):**
```json
{
  "id": "item-uuid",
  "name": "Navy Blue T-shirt",
  "category": "shirts",
  "color": "navy blue",
  "size": "L",
  "updated_at": "2024-01-03T14:20:00Z"
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/items/item-uuid \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Navy Blue T-shirt",
    "size": "L"
  }'
```

---

### Delete Item

**Endpoint:** `DELETE /items/{item_id}`

Removes an item from the wardrobe.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| item_id | string (UUID) | Item to delete |

**Response (204):**
No content returned.

**Example:**
```bash
curl -X DELETE http://localhost:8000/items/item-uuid \
  -H "Authorization: Bearer {token}"
```

---

### Batch Upload Items

**Endpoint:** `POST /items/batch`

Uploads multiple items at once.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| wardrobe_id | string | Target wardrobe |
| items | array[file] | Multiple image files |

**Response (201):**
```json
{
  "uploaded": 3,
  "failed": 0,
  "items": [
    {
      "id": "item-uuid-1",
      "name": "Item 1",
      "image_url": "..."
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/items/batch \
  -H "Authorization: Bearer {token}" \
  -F "wardrobe_id=wardrobe-uuid" \
  -F "items=@image1.jpg" \
  -F "items=@image2.jpg" \
  -F "items=@image3.jpg"
```

---

## Item Categories

Supported clothing categories:

| Category | Examples | Subcategories |
|----------|----------|----------------|
| **shirts** | T-shirts, polos, dress shirts | casual, formal, sports |
| **pants** | Jeans, khakis, trousers | casual, formal, sports |
| **dresses** | Casual, formal, cocktail | casual, formal, evening |
| **jackets** | Blazers, hoodies, coats | casual, formal, outerwear |
| **skirts** | Casual, formal, midi | casual, formal |
| **shoes** | Sneakers, heels, boots | casual, formal, sports |
| **accessories** | Belts, scarves, hats | jewelry, bags, hats |
| **underwear** | Basics | socks, bras, boxers |

---

## File Upload Requirements

### Image Specifications

- **Formats**: JPEG, PNG, WebP
- **Size**: Max 5MB
- **Dimensions**: Recommended 800x800px or larger
- **Quality**: Minimum 72 DPI

### Supported Image Extensions
- `.jpg`, `.jpeg` (JPEG)
- `.png` (PNG)
- `.webp` (WebP)

---

## Item Embedding System

### Automatic Embeddings

Each item gets CLIP embeddings (768 dimensions) for:
- Outfit compatibility calculations
- Similarity matching
- Recommendation generation

### Embedding Update

Embeddings are auto-generated on:
- Item upload
- Category change
- Color attribute update

---

## Workflow Example

### 1. Create Wardrobe
```bash
curl -X POST http://localhost:8000/wardrobes \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Summer Wardrobe"}'
```
Response: `wardrobe_id: 550e8400...`

### 2. Upload Item
```bash
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer {token}" \
  -F "wardrobe_id=550e8400..." \
  -F "name=Blue T-shirt" \
  -F "color=blue" \
  -F "image=@tshirt.jpg"
```
Response: `item_id: abc123...`

### 3. List Items
```bash
curl -X GET http://localhost:8000/wardrobes/550e8400.../items \
  -H "Authorization: Bearer {token}"
```

### 4. Update Item
```bash
curl -X PUT http://localhost:8000/items/abc123... \
  -H "Authorization: Bearer {token}" \
  -d '{"color": "navy blue"}'
```

### 5. Use in Outfit Generation
See [Outfits API](outfits.md).

---

## Best Practices

✅ Upload clear, well-lit item photos  
✅ Use descriptive item names  
✅ Set accurate color information  
✅ Include brand when available  
✅ Organize items by category  
✅ Update metadata when items change appearance  

---

## Error Handling

### Invalid Image Format
```json
{
  "detail": "Unsupported image format. Use jpg, png, or webp",
  "code": "INVALID_FORMAT"
}
```

### File Too Large
```json
{
  "detail": "File size exceeds 5MB limit",
  "code": "FILE_TOO_LARGE"
}
```

### Item Not Found
```json
{
  "detail": "Item not found",
  "code": "NOT_FOUND"
}
```

---

## Next Steps

- Learn about [Outfits API](outfits.md)
- Explore [ML Models API](ml-models.md)
- Read [Error Handling](errors.md)
