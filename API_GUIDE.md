# 📖 API Usage Guide

This guide provides detailed examples of how to use the Adversarial AI Writing Assistant API.

## 🔐 Authentication

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "johndoe",
       "email": "john@example.com",
       "password": "securepassword123"
     }'
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 2. Login and Get JWT Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=johndoe&password=securepassword123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token for Authenticated Requests

Include the token in the `Authorization` header:
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/auth/me"
```

## 📁 Project Management

### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/projects/?user_id=1" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Research Paper Analysis",
       "description": "Analysis of AI research papers"
     }'
```

### 2. List Projects

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/projects/"
```

### 3. Get Specific Project

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/projects/1"
```

## 📄 Document Management

### 1. Create Text Document

```bash
curl -X POST "http://localhost:8000/documents/" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "filename": "research_paper.txt",
       "content": "This is the content of my research paper...",
       "file_type": "text/plain",
       "project_id": 1
     }'
```

### 2. Upload File Document

```bash
curl -X POST "http://localhost:8000/upload/document" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/path/to/document.pdf" \
     -F "project_id=1"
```

### 3. Upload Multiple Files

```bash
curl -X POST "http://localhost:8000/upload/documents/batch" \
     -H "Authorization: Bearer $TOKEN" \
     -F "files=@document1.pdf" \
     -F "files=@document2.docx" \
     -F "files=@document3.txt" \
     -F "project_id=1"
```

### 4. Check Processing Status

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/upload/document/1/status"
```

**Response:**
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "is_processed": true,
  "processing_error": null,
  "uploaded_at": "2024-01-15T10:00:00Z",
  "processed_at": "2024-01-15T10:01:00Z"
}
```

## 🎭 Persona Management

### 1. Create a Persona

```bash
curl -X POST "http://localhost:8000/personas/" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Critical Academic Reviewer",
       "description": "Rigorous academic reviewer focused on methodology",
       "personality_traits": {
         "style": "critical",
         "tone": "analytical",
         "focus": "methodology",
         "expertise": "academic_writing"
       },
       "system_prompt": "You are a critical academic reviewer..."
     }'
```

### 2. Search Personas by Traits

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/personas/search/traits?trait_key=style&trait_value=critical"
```

### 3. List All Personas

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/personas/"
```

### 4. Get Active Personas Only

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/personas/active"
```

## 🔍 Advanced Queries

### 1. Pagination

```bash
# Get projects with pagination
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/projects/?skip=0&limit=10"

# Get documents with pagination
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/documents/?skip=10&limit=5"
```

### 2. Filtering

```bash
# Get active personas only
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/personas/?active_only=true"

# Search personas by name
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/personas/by-name/Academic"
```

## 📊 API Response Formats

### Success Response Format
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Error Response Format
```json
{
  "detail": "Error description here"
}
```

### Validation Error Format
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🔄 Complete Workflow Example

Here's a complete workflow from user registration to document analysis:

```bash
# 1. Register user
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "researcher", "email": "researcher@university.edu", "password": "research123"}'

# 2. Login and get token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=researcher&password=research123" \
        | jq -r '.access_token')

# 3. Create a project
PROJECT_ID=$(curl -X POST "http://localhost:8000/projects/?user_id=1" \
             -H "Authorization: Bearer $TOKEN" \
             -H "Content-Type: application/json" \
             -d '{"title": "AI Ethics Research", "description": "Research on AI ethics"}' \
             | jq -r '.id')

# 4. Upload a document
DOCUMENT_ID=$(curl -X POST "http://localhost:8000/upload/document" \
              -H "Authorization: Bearer $TOKEN" \
              -F "file=@research_paper.pdf" \
              -F "project_id=$PROJECT_ID" \
              | jq -r '.id')

# 5. Create personas for analysis
curl -X POST "http://localhost:8000/personas/" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Ethics Reviewer",
       "description": "Focused on ethical implications",
       "personality_traits": {"focus": "ethics", "style": "thoughtful"},
       "system_prompt": "Analyze from ethical perspective..."
     }'

# 6. Check document processing status
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/upload/document/$DOCUMENT_ID/status"
```

## 🚀 Future Analysis Endpoint (Coming Soon)

```bash
# This endpoint will be available in Phase 2
curl -X POST "http://localhost:8000/analyze" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "document_id": 1,
       "persona_ids": [1, 2, 3],
       "analysis_type": "comprehensive"
     }'
```

## 🔧 Error Handling

### Common HTTP Status Codes

- `200` - Success
- `201` - Created successfully
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `422` - Unprocessable entity (validation error)
- `500` - Internal server error

### Example Error Handling in Python

```python
import requests

def make_api_request(url, token, data=None):
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        if data:
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("Token expired or invalid")
        elif response.status_code == 404:
            print("Resource not found")
        else:
            print(f"API error: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# Usage
result = make_api_request("http://localhost:8000/projects/", token)
```

## 📱 Frontend Integration

### JavaScript/React Example

```javascript
const API_BASE_URL = 'http://localhost:8000';

class AdversarialAIAPI {
  constructor(token) {
    this.token = token;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }

  async getProjects() {
    return this.makeRequest('/projects/');
  }

  async createProject(projectData) {
    return this.makeRequest('/projects/?user_id=1', {
      method: 'POST',
      body: JSON.stringify(projectData)
    });
  }

  async uploadDocument(file, projectId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);

    return this.makeRequest('/upload/document', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData
    });
  }
}

// Usage
const api = new AdversarialAIAPI(localStorage.getItem('token'));
api.getProjects().then(projects => console.log(projects));
```

---

For more detailed API documentation, visit the interactive docs at `http://localhost:8000/docs` when the server is running.
