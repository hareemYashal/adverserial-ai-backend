# API Endpoints Documentation

## Overview

The Adversarial AI Writing Assistant API provides comprehensive endpoints for managing users, projects, documents, and AI personas. All endpoints return JSON responses and use standard HTTP status codes.

**Base URL**: `http://localhost:8000`

## Authentication

Currently, the API operates without authentication. JWT authentication is planned for future implementation.

## Core Endpoints

### Health & Status

#### GET `/`
Get API information and status.

**Response:**
```json
{
  "message": "Adversarial AI Writing Assistant API",
  "status": "running",
  "framework": "FastAPI",
  "endpoints": {
    "users": "/users",
    "projects": "/projects",
    "documents": "/documents",
    "personas": "/personas",
    "docs": "/docs"
  }
}
```

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET `/api/test`
Test endpoint for API verification.

**Response:**
```json
{
  "message": "API is working!",
  "python_version": "3.13",
  "framework": "FastAPI"
}
```

## Users Endpoints

### GET `/users/`
Get all users with pagination.

**Query Parameters:**
- `skip` (int, optional): Number of users to skip (default: 0)
- `limit` (int, optional): Maximum number of users to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET `/users/{user_id}`
Get a specific user by ID.

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### GET `/users/{user_id}/with-projects`
Get a user with all their associated projects.

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "projects": [
    {
      "id": 1,
      "title": "My Project",
      "description": "A sample project",
      "user_id": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### GET `/users/by-username/{username}`
Get a user by username.

### GET `/users/by-email/{email}`
Get a user by email address.

### POST `/users/`
Create a new user.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`

### PUT `/users/{user_id}`
Update an existing user.

**Request Body:**
```json
{
  "username": "updated_username",
  "email": "updated@example.com"
}
```

### DELETE `/users/{user_id}`
Delete a user.

**Response:** `204 No Content`

### GET `/users/active/count`
Get the count of active users.

**Response:**
```json
{
  "active_users_count": 5
}
```

## Projects Endpoints

### GET `/projects/`
Get all projects with optional filtering.

**Query Parameters:**
- `skip` (int, optional): Number of projects to skip (default: 0)
- `limit` (int, optional): Maximum number of projects to return (default: 100)
- `user_id` (int, optional): Filter projects by user ID

**Response:**
```json
[
  {
    "id": 1,
    "title": "My Project",
    "description": "A sample project",
    "user_id": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET `/projects/{project_id}`
Get a specific project by ID.

### GET `/projects/{project_id}/with-documents`
Get a project with all its associated documents.

**Response:**
```json
{
  "id": 1,
  "title": "My Project",
  "description": "A sample project",
  "user_id": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "documents": [
    {
      "id": 1,
      "filename": "document.txt",
      "content": "Document content",
      "file_type": "text/plain",
      "project_id": 1,
      "file_path": null,
      "file_size": null,
      "uploaded_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### GET `/projects/user/{user_id}`
Get all projects for a specific user.

**Query Parameters:**
- `skip` (int, optional): Number of projects to skip (default: 0)
- `limit` (int, optional): Maximum number of projects to return (default: 100)

### POST `/projects/`
Create a new project.

**Query Parameters:**
- `user_id` (int, required): The ID of the user who will own the project

**Request Body:**
```json
{
  "title": "New Project",
  "description": "A new project description"
}
```

**Response:** `201 Created`

### PUT `/projects/{project_id}`
Update an existing project.

**Request Body:**
```json
{
  "title": "Updated Project Title",
  "description": "Updated description"
}
```

### DELETE `/projects/{project_id}`
Delete a project and all its associated documents.

**Response:** `204 No Content`

### GET `/projects/search/{title}`
Search projects by title (case-insensitive partial match).

### GET `/projects/user/{user_id}/count`
Get the count of projects for a specific user.

**Response:**
```json
{
  "user_id": 1,
  "project_count": 3
}
```

## Documents Endpoints

### GET `/documents/`
Get all documents with optional filtering.

**Query Parameters:**
- `skip` (int, optional): Number of documents to skip (default: 0)
- `limit` (int, optional): Maximum number of documents to return (default: 100)
- `project_id` (int, optional): Filter documents by project ID
- `file_type` (str, optional): Filter documents by file type

**Response:**
```json
[
  {
    "id": 1,
    "filename": "document.txt",
    "content": "Document content",
    "file_type": "text/plain",
    "project_id": 1,
    "file_path": null,
    "file_size": null,
    "uploaded_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET `/documents/{document_id}`
Get a specific document by ID.

### GET `/documents/project/{project_id}`
Get all documents for a specific project.

**Query Parameters:**
- `skip` (int, optional): Number of documents to skip (default: 0)
- `limit` (int, optional): Maximum number of documents to return (default: 100)

### POST `/documents/`
Create a new document.

**Request Body:**
```json
{
  "filename": "new_document.txt",
  "content": "Document content here",
  "file_type": "text/plain",
  "project_id": 1
}
```

**Response:** `201 Created`

### PUT `/documents/{document_id}`
Update an existing document.

**Request Body:**
```json
{
  "filename": "updated_document.txt",
  "content": "Updated content",
  "file_type": "text/plain"
}
```

### DELETE `/documents/{document_id}`
Delete a document.

**Response:** `204 No Content`

### GET `/documents/search/{filename}`
Search documents by filename (case-insensitive partial match).

### GET `/documents/by-type/{file_type}`
Get documents by file type.

### GET `/documents/project/{project_id}/count`
Get the count of documents for a specific project.

**Response:**
```json
{
  "project_id": 1,
  "document_count": 5
}
```

### GET `/documents/stats/file-types`
Get statistics about documents grouped by file type.

**Response:**
```json
[
  {
    "file_type": "text/plain",
    "count": 10
  },
  {
    "file_type": "application/pdf",
    "count": 5
  }
]
```

## Personas Endpoints

### GET `/personas/`
Get all personas with optional filtering.

**Query Parameters:**
- `skip` (int, optional): Number of personas to skip (default: 0)
- `limit` (int, optional): Maximum number of personas to return (default: 100)
- `active_only` (bool, optional): Filter to only active personas (default: false)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Critical Reviewer",
    "description": "A persona focused on critical analysis",
    "personality_traits": {
      "style": "critical",
      "tone": "analytical"
    },
    "system_prompt": "You are a critical reviewer...",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET `/personas/{persona_id}`
Get a specific persona by ID.

### GET `/personas/by-name/{name}`
Get personas by name (case-insensitive partial match).

### POST `/personas/`
Create a new AI persona.

**Request Body:**
```json
{
  "name": "New Critic",
  "description": "A new critical persona",
  "personality_traits": {
    "style": "critical",
    "tone": "analytical",
    "focus": "clarity"
  },
  "system_prompt": "You are a critical reviewer focused on improving writing clarity and structure."
}
```

**Response:** `201 Created`

### PUT `/personas/{persona_id}`
Update an existing persona.

**Request Body:**
```json
{
  "name": "Updated Critic",
  "description": "Updated description",
  "personality_traits": {
    "style": "constructive",
    "tone": "helpful"
  },
  "system_prompt": "Updated system prompt",
  "is_active": true
}
```

### DELETE `/personas/{persona_id}`
Delete a persona.

**Response:** `204 No Content`

### PATCH `/personas/{persona_id}/activate`
Activate a persona (set is_active to True).

### PATCH `/personas/{persona_id}/deactivate`
Deactivate a persona (set is_active to False).

### GET `/personas/active`
Get all active personas.

**Query Parameters:**
- `skip` (int, optional): Number of personas to skip (default: 0)
- `limit` (int, optional): Maximum number of personas to return (default: 100)

### GET `/personas/stats/status`
Get statistics about personas grouped by active status.

**Response:**
```json
[
  {
    "is_active": true,
    "count": 8
  },
  {
    "is_active": false,
    "count": 2
  }
]
```

### GET `/personas/search/traits`
Search personas by personality traits.

**Query Parameters:**
- `trait_key` (str, required): The trait key to search for
- `trait_value` (str, required): The trait value to search for
- `skip` (int, optional): Number of personas to skip (default: 0)
- `limit` (int, optional): Maximum number of personas to return (default: 100)

## Reference Extraction Endpoint

### POST `/api/extract_references`
Extracts and returns structured references from a document or references section.

**Request Body:**
```json
{
  "text": "string (full document or references section)"
}
```

**Response:**
```json
{
  "references": [
    "Smith J, 2020, Title of Paper, Journal Name, 12(3), 45-56.",
    "Doe A, 2019, Another Article, Another Journal, 5(1), 10-20."
  ]
}
```

**Description:**
- Accepts raw text (full document or just the references section).
- Returns a list of parsed reference strings, each representing a single reference entry.
- Handles multi-line, numbered, and author-year references robustly.

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

## Pagination

Most list endpoints support pagination using `skip` and `limit` query parameters:

- `skip`: Number of items to skip (for pagination)
- `limit`: Maximum number of items to return

**Example:**
```
GET /users/?skip=20&limit=10
```

This would return users 21-30 (skipping the first 20, returning up to 10).

## Testing

Use the provided test script to verify all endpoints:

```bash
python test_api_endpoints.py
```

## Interactive Documentation

Visit the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Examples

### Creating a Complete Workflow

1. **Create a user:**
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "writer", "email": "writer@example.com", "password": "password123"}'
```

2. **Create a project:**
```bash
curl -X POST "http://localhost:8000/projects/?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Writing Project", "description": "A project for writing and critique"}'
```

3. **Create a document:**
```bash
curl -X POST "http://localhost:8000/documents/" \
  -H "Content-Type: application/json" \
  -d '{"filename": "essay.txt", "content": "This is my essay content...", "file_type": "text/plain", "project_id": 1}'
```

4. **Create a persona:**
```bash
curl -X POST "http://localhost:8000/personas/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Grammar Critic", "description": "Focuses on grammar and style", "personality_traits": {"focus": "grammar"}, "system_prompt": "You are a grammar expert..."}'
```

5. **Get project with documents:**
```bash
curl "http://localhost:8000/projects/1/with-documents"
``` 

6. **Analysis of the document with respect to Persona**
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze/?project_id=ID&document_id=ID&persona_name=PERSONA_NAME" \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_JWT_ACCESS_TOKEN>' \
  -d ''
```


7. **Analysis of the document with respect to Multi-Persona**
```bash
curl -X POST "http://127.0.0.1:8000/api/multi_analyze/?project_id=ID&document_id=ID&persona_name={PERSONA_NAME,PERSONA_NAME}" \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_JWT_ACCESS_TOKEN>' \
  -d ''
```