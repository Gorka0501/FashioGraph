# Authentication API

User authentication, registration, and session management endpoints.

## Overview

The authentication system uses JWT (JSON Web Tokens) for stateless, secure API access. Passwords are hashed using bcrypt for security.

## Authentication Flow

```
1. User Registration
   └─→ POST /auth/register
       ├─ Username & password
       └─→ Returns: user_id, username

2. User Login
   └─→ POST /auth/login
       ├─ Username & password
       └─→ Returns: access_token (JWT)

3. Authenticated Request
   └─→ GET /wardrobes
       ├─ Header: Authorization: Bearer {token}
       └─→ Returns: User's wardrobes

4. Token Refresh (if implemented)
   └─→ POST /auth/refresh
       └─→ Returns: New access_token
```

## Endpoints

### Register User

**Endpoint:** `POST /auth/register`

Creates a new user account.

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Unique username (3-50 chars) |
| password | string | Yes | Password (8+ chars, uppercase, lowercase, digit) |

**Response (201):**
```json
{
  "id": "uuid-string",
  "username": "john_doe",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | INVALID_USERNAME | Username already taken |
| 400 | WEAK_PASSWORD | Password doesn't meet requirements |
| 422 | VALIDATION_ERROR | Invalid input format |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

---

### Login

**Endpoint:** `POST /auth/login`

Authenticates user and returns JWT token.

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Registered username |
| password | string | Yes | User password |

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 401 | INVALID_CREDENTIALS | Username or password incorrect |
| 404 | USER_NOT_FOUND | User doesn't exist |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

---

### Get Current User

**Endpoint:** `GET /auth/me`

Returns authenticated user's information.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "uuid-string",
  "username": "john_doe",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login": "2024-01-02T10:30:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Token expired |

**Example:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### Change Password

**Endpoint:** `POST /auth/change-password`

Updates user password.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| current_password | string | Yes | Current password for verification |
| new_password | string | Yes | New password (8+ chars) |

**Response (200):**
```json
{
  "message": "Password updated successfully"
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 401 | INVALID_PASSWORD | Current password incorrect |
| 400 | WEAK_PASSWORD | New password doesn't meet requirements |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword456!"
  }'
```

---

## JWT Token Format

**Token Structure:**
```
Header.Payload.Signature
```

**Decoded Payload:**
```json
{
  "sub": "user_id",
  "username": "john_doe",
  "exp": 1704110400,
  "iat": 1704024000,
  "type": "access"
}
```

**Token Details:**
| Field | Meaning | Value |
|-------|---------|-------|
| sub | Subject (User ID) | UUID |
| username | Username | string |
| exp | Expiration time | Unix timestamp |
| iat | Issued at time | Unix timestamp |
| type | Token type | "access" |

**Token Lifespan:**
- Default: 24 hours (86400 seconds)
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`

---

## Usage in Requests

### Include Token in Header

All authenticated endpoints require the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/wardrobes \
  -H "Authorization: Bearer {access_token}"
```

### Token Placement

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkODM3ZGMzMS02ZGJhLTQ4MzEtYTI3ZS1mZTI1OTAzODAxN2UiLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZXhwIjoxNzA0MTA2NDAwLCJpYXQiOjE3MDQwMjAwMDB9.signature
```

### Token Expiration

When token expires:
```json
{
  "detail": "Token has expired",
  "code": "TOKEN_EXPIRED"
}
```

Solution: Login again to get a new token.

---

## Security Best Practices

### 1. Password Requirements

✅ Minimum 8 characters  
✅ At least one uppercase letter  
✅ At least one lowercase letter  
✅ At least one digit  
✅ Special characters recommended  

### 2. Token Handling

✅ Store token in secure storage (not localStorage)  
✅ Use HTTPS in production  
✅ Include token only in Authorization header  
✅ Never expose token in logs  

### 3. Authentication Flow

✅ Always validate credentials on every request  
✅ Use password hashing (bcrypt)  
✅ Implement token expiration  
✅ Handle token refresh appropriately  

---

## Error Handling

### Common Errors

**Invalid Credentials (401):**
```json
{
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

**User Exists (400):**
```json
{
  "detail": "Username already exists",
  "code": "USER_EXISTS"
}
```

**Weak Password (400):**
```json
{
  "detail": "Password does not meet security requirements",
  "code": "WEAK_PASSWORD"
}
```

**Unauthorized (401):**
```json
{
  "detail": "Not authenticated",
  "code": "UNAUTHORIZED"
}
```

---

## Testing

### Test Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "TestPass123!"}'
```

### Test Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "TestPass123!"}'
```

### Test Authenticated Endpoint
```bash
TOKEN="your_token_here"
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Next Steps

- Explore [Wardrobe API](wardrobe.md)
- Learn about [Items API](items.md)
- Review [Error Handling](errors.md)
