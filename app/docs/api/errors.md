# Error Handling

Common errors, error codes, and solutions.

## HTTP Status Codes

### Success (2xx)

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Successful GET/PUT/POST |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful DELETE |

### Client Errors (4xx)

| Status | Meaning | Common Cause |
|--------|---------|-------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid request data |

### Server Errors (5xx)

| Status | Meaning | Action |
|--------|---------|--------|
| 500 | Internal Server Error | Report to support |
| 503 | Service Unavailable | Try again later |

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Example Error Response

```json
{
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Authentication Errors

### UNAUTHORIZED (401)

**Cause:** Missing or invalid authentication token

**Response:**
```json
{
  "detail": "Not authenticated",
  "code": "UNAUTHORIZED"
}
```

**Solutions:**
1. Check token is in `Authorization` header
2. Use format: `Authorization: Bearer {token}`
3. Login again to get fresh token

---

### TOKEN_EXPIRED (403)

**Cause:** JWT token has expired

**Response:**
```json
{
  "detail": "Token has expired",
  "code": "TOKEN_EXPIRED"
}
```

**Solutions:**
1. Login again: `POST /auth/login`
2. Use new token in subsequent requests
3. Tokens expire after 24 hours by default

---

### INVALID_CREDENTIALS (401)

**Cause:** Username or password incorrect

**Response:**
```json
{
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

**Solutions:**
1. Verify username spelling
2. Confirm password is correct
3. Check Caps Lock
4. Reset password if forgotten

---

## Registration Errors

### USER_EXISTS (400)

**Cause:** Username already taken

**Response:**
```json
{
  "detail": "Username already exists",
  "code": "USER_EXISTS"
}
```

**Solutions:**
1. Choose different username
2. Login with existing account
3. Username is case-sensitive

---

### WEAK_PASSWORD (400)

**Cause:** Password doesn't meet requirements

**Response:**
```json
{
  "detail": "Password does not meet security requirements",
  "code": "WEAK_PASSWORD",
  "requirements": {
    "min_length": 8,
    "uppercase": true,
    "lowercase": true,
    "digit": true
  }
}
```

**Solutions:**
1. Use at least 8 characters
2. Include uppercase letter (A-Z)
3. Include lowercase letter (a-z)
4. Include digit (0-9)
5. Add special character for extra security

**Good password examples:**
- `SecurePass123!`
- `MyPassword456@`
- `Wardrobe2024#`

---

## Resource Errors

### NOT_FOUND (404)

**Cause:** Resource doesn't exist

**Response:**
```json
{
  "detail": "Wardrobe not found",
  "code": "NOT_FOUND"
}
```

**Solutions:**
1. Verify resource ID is correct
2. Check resource hasn't been deleted
3. Ensure user owns the resource
4. Use correct endpoint

---

### FORBIDDEN (403)

**Cause:** User doesn't have permission

**Response:**
```json
{
  "detail": "You don't have permission to access this resource",
  "code": "FORBIDDEN"
}
```

**Solutions:**
1. Ensure you own the resource
2. Check you're using correct user account
3. Verify you have required permissions
4. Can't access other users' resources

---

## Validation Errors

### VALIDATION_ERROR (422)

**Cause:** Invalid request data format

**Response:**
```json
{
  "detail": "Validation error",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "username",
      "message": "Username must be 3-50 characters"
    }
  ]
}
```

**Solutions:**
1. Check field types (string, integer, etc.)
2. Verify required fields present
3. Check value ranges/formats
4. See API documentation for valid values

---

### INVALID_FORMAT (400)

**Cause:** Request format invalid (e.g., wrong image type)

**Response:**
```json
{
  "detail": "Unsupported image format. Use jpg, png, or webp",
  "code": "INVALID_FORMAT"
}
```

**Solutions:**
1. Use supported file types
2. For images: JPG, PNG, WebP
3. Check file extension
4. Verify file not corrupted

---

## File Upload Errors

### FILE_TOO_LARGE (400)

**Cause:** Uploaded file exceeds size limit (5MB)

**Response:**
```json
{
  "detail": "File size exceeds 5MB limit",
  "code": "FILE_TOO_LARGE",
  "max_size_mb": 5,
  "your_size_mb": 8.5
}
```

**Solutions:**
1. Compress image before upload
2. Reduce image quality/resolution
3. Use online image compressor
4. Try different image format

---

### IMAGE_PROCESSING_ERROR (400)

**Cause:** Error processing image file

**Response:**
```json
{
  "detail": "Failed to process image: corrupt file",
  "code": "IMAGE_PROCESSING_ERROR"
}
```

**Solutions:**
1. Verify image file not corrupted
2. Try different image
3. Re-save image in supported format
4. Check file is actually an image

---

## Database Errors

### DATABASE_ERROR (500)

**Cause:** Database operation failed

**Response:**
```json
{
  "detail": "Database error occurred",
  "code": "DATABASE_ERROR"
}
```

**Solutions:**
1. Try request again
2. Check database connection
3. Contact system administrator
4. Check logs for details

---

### CONSTRAINT_VIOLATION (400)

**Cause:** Data violates database constraint

**Response:**
```json
{
  "detail": "Item with this name already exists",
  "code": "CONSTRAINT_VIOLATION"
}
```

**Solutions:**
1. Use unique value (e.g., different name)
2. Update existing item instead of creating new
3. Check item already exists

---

## ML/Training Errors

### MODEL_NOT_READY (503)

**Cause:** Model still loading or training

**Response:**
```json
{
  "detail": "Model is still loading. Please try again in a moment",
  "code": "MODEL_NOT_READY",
  "retry_after_seconds": 30
}
```

**Solutions:**
1. Wait 30 seconds and retry
2. Check model status with `/models/status`
3. Try generating outfit again

---

### INSUFFICIENT_DATA (400)

**Cause:** Not enough data for operation

**Response:**
```json
{
  "detail": "Insufficient items for outfit generation. Need at least 3 items",
  "code": "INSUFFICIENT_DATA",
  "required": 3,
  "available": 1
}
```

**Solutions:**
1. Upload more items to wardrobe
2. Need minimum 3 items for outfits
3. Add items from different categories

---

## Common Scenarios and Solutions

### Scenario: Getting 401 Unauthorized

**Steps to debug:**
1. Check token in header: `Authorization: Bearer {token}`
2. Verify token from `/auth/login` endpoint
3. Login again to get fresh token
4. Check token format (no extra spaces)
5. Ensure token not expired

**Example fix:**
```bash
# Get new token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}' \
  | jq -r '.access_token')

# Use in request
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Scenario: Getting 404 Not Found

**Steps to debug:**
1. Verify resource ID is correct
2. Check resource type matches endpoint
3. Confirm resource hasn't been deleted
4. Ensure correct endpoint path
5. Verify you own the resource

**Example:**
```bash
# Get correct ID first
WARDROBE_ID=$(curl -X GET http://localhost:8000/wardrobes \
  -H "Authorization: Bearer {token}" \
  | jq -r '.wardrobes[0].id')

# Then use correct ID
curl -X GET http://localhost:8000/wardrobes/$WARDROBE_ID \
  -H "Authorization: Bearer {token}"
```

---

### Scenario: File Upload Fails

**Steps to debug:**
1. Check file format (jpg, png, webp)
2. Verify file size < 5MB
3. Test file not corrupted
4. Check multipart form encoding
5. Verify all required fields present

**Example:**
```bash
# Check file size
ls -lh image.jpg

# Compress if needed
convert image.jpg -resize 1200x1200 -quality 85 image_small.jpg

# Try upload
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer {token}" \
  -F "wardrobe_id=wardrobe-uuid" \
  -F "name=My Item" \
  -F "image=@image_small.jpg"
```

---

## Retry Strategy

For transient errors (5xx, timeouts):

```python
import time

def retry_request(endpoint, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = make_request(endpoint)
            return response
        except (ServerError, Timeout):
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

### Backoff Strategy

| Attempt | Wait Time | Total Time |
|---------|-----------|-----------|
| 1 | 1 second | 1s |
| 2 | 2 seconds | 3s |
| 3 | 4 seconds | 7s |

---

## Getting Help

### Debug Information to Provide

When reporting errors, include:
1. **Error message**: Exact error text
2. **Error code**: The error code from response
3. **HTTP status**: The status code (401, 404, etc.)
4. **Endpoint**: Which API endpoint
5. **Timestamp**: When it occurred
6. **Steps to reproduce**: How to recreate error

### Checking Logs

```bash
# View application logs
tail -f app/logs/app.log

# View error logs only
grep ERROR app/logs/app.log

# View specific time period
grep "2024-01-01 12:" app/logs/app.log
```

---

## Next Steps

- Review [API Reference](authentication.md)
- Read [Troubleshooting Guide](../troubleshooting/common-issues.md)
- Learn about [Debugging](../troubleshooting/debugging.md)
