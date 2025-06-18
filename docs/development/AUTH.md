# Authentication & Authorization Guide

## Overview

Palantir uses a robust authentication and authorization system based on JWT (JSON Web Tokens) and RBAC (Role-Based Access Control). This guide explains how to use and manage these security features.

## Authentication

### 1. Login
```http
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

Response:
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

### 2. Using the Token
Include the token in the `Authorization` header:
```http
GET /api/endpoint
Authorization: Bearer eyJ...
```

### 3. Password Reset
```http
POST /auth/forgot-password
Content-Type: application/json

{
    "email": "user@example.com"
}
```

## Authorization (RBAC)

### 1. Available Roles
- **Admin**: Full system access
- **Developer**: Code writing and testing
- **Reviewer**: Code review and approval
- **User**: Basic access

### 2. Permissions by Role

#### Admin
- manage:users
- manage:roles
- manage:system
- write:code
- run:tests
- manage:pipelines
- review:code
- approve:changes
- read:docs
- read:metrics
- use:api

#### Developer
- write:code
- run:tests
- manage:pipelines
- read:docs
- read:metrics
- use:api

#### Reviewer
- review:code
- approve:changes
- read:docs
- read:metrics
- use:api

#### User
- read:docs
- read:metrics
- use:api

### 3. Managing Roles

Only admins can manage user roles:
```http
PUT /auth/users/{user_id}/roles
Authorization: Bearer eyJ...
Content-Type: application/json

{
    "roles": ["developer", "reviewer"]
}
```

## Security Policies

### 1. Password Requirements
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, and special characters
- Cannot reuse last 5 passwords
- Expires after 90 days

### 2. Token Policies
- Access tokens expire after 1 hour
- Refresh tokens expire after 7 days
- Maximum 3 active sessions per user

### 3. Rate Limiting
- Default: 1000 requests per hour
- Burst: 50 requests
- Admin endpoints: 100 requests per minute

## Example Usage

### 1. Creating a New User (Admin only)
```http
POST /auth/register
Authorization: Bearer eyJ...
Content-Type: application/json

{
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "username": "newuser"
}
```

### 2. Updating User Roles (Admin only)
```http
PUT /auth/users/123/roles
Authorization: Bearer eyJ...
Content-Type: application/json

{
    "roles": ["developer"]
}
```

### 3. Accessing Protected Endpoints
```http
# Developer endpoint
POST /api/code/submit
Authorization: Bearer eyJ...

# Reviewer endpoint
POST /api/review/approve
Authorization: Bearer eyJ...

# User endpoint
GET /api/docs
Authorization: Bearer eyJ...
```

## Troubleshooting

### Common Issues

1. **Invalid Token**
   - Check token expiration
   - Ensure correct token format
   - Verify token in Authorization header

2. **Permission Denied**
   - Verify user roles
   - Check required permissions
   - Ensure token is not expired

3. **Rate Limit Exceeded**
   - Wait for rate limit reset
   - Check current usage
   - Consider upgrading access tier

### Security Contacts

For security-related issues:
- Email: security@palantir.local
- Emergency: security-emergency@palantir.local 