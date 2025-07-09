# Desktop Search API Documentation

## Overview

The Desktop Search API provides a comprehensive REST interface for indexing and searching local documents with advanced semantic search capabilities. The API supports multiple search types, Google Drive integration, and secure API key authentication.

## Base URL

- **Development**: `https://localhost:8443`
- **Production**: Configure your domain

## Authentication

The API supports two authentication methods:

### 1. API Key Authentication
```bash
# Include in request headers
Authorization: Bearer YOUR_API_KEY
```

### 2. Admin Key Authentication (for administrative operations)
```bash
# Include in request headers
X-Admin-Key: YOUR_ADMIN_KEY
```

## Getting Started

### 1. Set up Admin Key
```bash
export API_KEY="your-super-secret-admin-key-here"
```

### 2. Create Your First API Key
```bash
curl -X POST "https://localhost:8443/api/v1/auth/create-key" \
     -H "X-Admin-Key: your-admin-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "My First Key",
       "description": "For testing",
       "permissions": ["read", "search"]
     }'
```

### 3. Use Your API Key
```bash
curl -X POST "https://localhost:8443/api/v1/searcher/search" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "machine learning",
       "search_type": "semantic",
       "limit": 10
     }'
```

## API Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

**Description**: Check if the API is running and healthy

**Response**:
```json
{
  "success": true,
  "message": "Desktop Search API is running",
  "data": {
    "status": "healthy"
  }
}
```

#### API Information
```http
GET /api/info
```

**Description**: Get basic information about the API

**Response**:
```json
{
  "success": true,
  "message": "Desktop Search API",
  "data": {
    "version": "1.0.0",
    "docs": "/docs",
    "health": "/health"
  }
}
```

### Authentication Endpoints

#### Create API Key
```http
POST /api/v1/auth/create-key
```

**Description**: Create a new API key with specified permissions

**Headers**:
- `X-Admin-Key`: Admin key for authentication

**Request Body**:
```json
{
  "name": "My Search Key",
  "description": "Key for search operations",
  "expires_days": 30,
  "permissions": ["read", "search"]
}
```

**Response**:
```json
{
  "success": true,
  "message": "API key created successfully",
  "data": {
    "api_key": "ds_abc123...",
    "key_info": {
      "id": "key_123",
      "name": "My Search Key",
      "description": "Key for search operations",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-02-14T10:30:00Z",
      "permissions": ["read", "search"]
    }
  }
}
```

#### List API Keys
```http
GET /api/v1/auth/list-keys
```

**Description**: List all API keys (admin only)

**Headers**:
- `X-Admin-Key`: Admin key for authentication

**Response**:
```json
{
  "keys": [
    {
      "id": "key_123",
      "name": "My Search Key",
      "description": "Key for search operations",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-02-14T10:30:00Z",
      "permissions": ["read", "search"],
      "is_active": true
    }
  ]
}
```

#### Revoke API Key
```http
DELETE /api/v1/auth/revoke-key/{key_id}
```

**Description**: Revoke an API key (admin only)

**Headers**:
- `X-Admin-Key`: Admin key for authentication

**Response**:
```json
{
  "success": true,
  "message": "API key 'My Search Key' revoked successfully"
}
```

#### Validate API Key
```http
POST /api/v1/auth/validate-key
```

**Description**: Validate an API key and get its information

**Request Body**:
```json
{
  "api_key": "ds_abc123..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "API key is valid",
  "data": {
    "key_info": {
      "id": "key_123",
      "name": "My Search Key",
      "permissions": ["read", "search"]
    }
  }
}
```

#### Login with API Key
```http
POST /api/v1/auth/login
```

**Description**: Get JWT token using API key

**Request Body**:
```json
{
  "api_key": "ds_abc123..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Search Endpoints

#### Search Documents
```http
POST /api/v1/searcher/search
```

**Description**: Search indexed documents using semantic, keyword, or hybrid search

**Headers**:
- `Authorization`: Bearer YOUR_API_KEY

**Request Body**:
```json
{
  "query": "machine learning algorithms",
  "search_type": "semantic",
  "limit": 10,
  "threshold": 0.3
}
```

**Search Types**:
- `keyword`: Traditional keyword/substring search
- `semantic`: Semantic similarity search (default)
- `hybrid`: Combines semantic and keyword matching

**Response**:
```json
{
  "query": "machine learning algorithms",
  "search_type": "semantic",
  "results": [
    {
      "filepath": "/path/to/document.pdf",
      "filename": "document.pdf",
      "snippet": "This document discusses machine learning algorithms...",
      "score": 0.85,
      "file_type": "pdf",
      "file_size": 1024000,
      "last_modified": "2024-01-15T10:30:00Z"
    }
  ],
  "total_results": 5,
  "search_time_ms": 45.2
}
```

#### Search Google Drive
```http
POST /api/v1/searcher/gdrive
```

**Description**: Search Google Drive files directly (requires Google Drive setup)

**Headers**:
- `Authorization`: Bearer YOUR_API_KEY

**Request Body**:
```json
{
  "query": "project proposal",
  "search_type": "semantic",
  "limit": 10,
  "threshold": 0.3
}
```

**Response**:
```json
{
  "query": "project proposal",
  "search_type": "semantic",
  "results": [
    {
      "filepath": "gdrive://document.docx",
      "filename": "document.docx",
      "snippet": "This document contains the project proposal...",
      "score": 0.92,
      "file_type": "docx",
      "file_size": 2048000,
      "last_modified": "2024-01-15T10:30:00Z"
    }
  ],
  "total_results": 3,
  "search_time_ms": 120.5
}
```

#### Get Search Suggestions
```http
GET /api/v1/searcher/suggestions?query=machine&limit=5
```

**Description**: Get search suggestions based on partial query

**Parameters**:
- `query`: Partial search query
- `limit`: Maximum number of suggestions (default: 5)

**Response**:
```json
{
  "success": true,
  "message": "Search suggestions retrieved",
  "data": {
    "suggestions": [
      "machine learning document",
      "machine learning file",
      "machine learning report",
      "machine learning analysis",
      "machine learning data"
    ]
  }
}
```

### Directory Management Endpoints

#### List Directories
```http
GET /api/v1/directories/list
```

**Description**: Get list of all indexed directories

**Response**:
```json
{
  "directories": [
    {
      "path": "/path/to/documents",
      "name": "documents",
      "status": "indexed",
      "progress": 1.0,
      "last_indexed": "2024-01-15T10:30:00Z",
      "total_files": 150,
      "indexed_files": 150,
      "task_id": "dir_1705312200_documents"
    }
  ]
}
```

#### Add Directory
```http
POST /api/v1/directories/add?path=/path/to/documents
```

**Description**: Add a new directory to the index

**Parameters**:
- `path`: Path to the directory to add

**Response**:
```json
{
  "success": true,
  "message": "Directory added: /path/to/documents",
  "data": {
    "directory": {
      "path": "/path/to/documents",
      "name": "documents",
      "status": "not_indexed"
    }
  }
}
```

#### Refresh Directory
```http
POST /api/v1/directories/refresh/{path}
```

**Description**: Refresh/rebuild index for a specific directory

**Parameters**:
- `path`: Path to the directory to refresh

**Response**:
```json
{
  "success": true,
  "message": "Indexing started for: /path/to/documents",
  "data": {
    "task_id": "dir_1705312200_documents"
  }
}
```

#### Get Directory Status
```http
GET /api/v1/directories/status/{path}
```

**Description**: Get indexing status for a specific directory

**Parameters**:
- `path`: Path to the directory

**Response**:
```json
{
  "path": "/path/to/documents",
  "status": "indexing",
  "progress": 0.75,
  "message": "Indexing: document.pdf",
  "task_id": "dir_1705312200_documents",
  "total_files": 150,
  "indexed_files": 112
}
```

#### Remove Directory
```http
DELETE /api/v1/directories/remove/{path}
```

**Description**: Remove a directory from the index

**Parameters**:
- `path`: Path to the directory to remove

**Response**:
```json
{
  "success": true,
  "message": "Directory removed: /path/to/documents",
  "data": {
    "directory": {
      "path": "/path/to/documents",
      "name": "documents",
      "status": "indexed"
    }
  }
}
```

### Statistics Endpoints

#### Get System Statistics
```http
GET /api/v1/stats/system
```

**Description**: Get comprehensive system statistics including index and directory information

**Response**:
```json
{
  "success": true,
  "message": "System statistics retrieved",
  "data": {
    "total_chunks": 1500,
    "model_name": "all-MiniLM-L6-v2",
    "persist_directory": "./data/chroma_db",
    "db_size_bytes": 52428800,
    "db_size_human": "50.0 MB",
    "total_directories": 3,
    "indexed_directories": 2,
    "total_files": 300,
    "system_info": {
      "cpu_usage": 25.5,
      "memory_usage": 60.2,
      "memory_available": 8589934592,
      "disk_usage": 75.8,
      "disk_free": 107374182400,
      "uptime": 1705312200
    }
  }
}
```

#### Get Index Statistics
```http
GET /api/v1/stats/index?directory=/path/to/documents
```

**Description**: Get statistics about a specific index

**Parameters**:
- `directory`: Directory path for the index
- `index_path`: Path to the index file

**Response**:
```json
{
  "success": true,
  "message": "Index statistics retrieved",
  "data": {
    "total_files": 150,
    "total_size": 52428800,
    "file_types": {
      "pdf": 50,
      "docx": 30,
      "txt": 20
    },
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Semantic Index Statistics
```http
GET /api/v1/stats/semantic?db_path=./data/chroma_db
```

**Description**: Get statistics about the semantic index

**Parameters**:
- `db_path`: Path to the ChromaDB directory

**Response**:
```json
{
  "success": true,
  "message": "Semantic index statistics retrieved",
  "data": {
    "total_chunks": 1500,
    "total_documents": 150,
    "model_name": "all-MiniLM-L6-v2",
    "db_path": "./data/chroma_db",
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Hybrid Index Statistics
```http
GET /api/v1/stats/hybrid?db_path=./data/chroma_db
```

**Description**: Get statistics about the hybrid index

**Parameters**:
- `db_path`: Path to the ChromaDB directory

**Response**:
```json
{
  "success": true,
  "message": "Hybrid index statistics retrieved",
  "data": {
    "local_files": 150,
    "gdrive_files": 50,
    "total_chunks": 2000,
    "model_name": "all-MiniLM-L6-v2",
    "db_path": "./data/chroma_db",
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Performance Statistics
```http
GET /api/v1/stats/performance
```

**Description**: Get performance statistics and metrics

**Response**:
```json
{
  "success": true,
  "message": "Performance statistics retrieved",
  "data": {
    "avg_search_time_ms": 45.2,
    "total_searches": 1250,
    "cache_hit_rate": 0.85,
    "memory_usage_mb": 512.5,
    "disk_usage_mb": 1024.0
  }
}
```

## LLM-Enhanced Search Endpoints

Desktop Search supports advanced, ChatGPT-like search and summarization using local LLMs and embeddings. All LLM features are 100% local—no data leaves your machine. You can choose your own embedding and LLM models (Ollama/LocalAI supported).

### Get LLM Provider Status
```http
GET /api/v1/llm/status
```
**Description**: Get the status of LLM providers, active model, and embedding model.

**Response**:
```json
{
  "active_provider": "OllamaProvider",
  "available_providers": [
    {"name": "ollama", "type": "OllamaProvider", "available": true, "loaded": true, "llm_model": "phi3"}
  ],
  "detected_providers": ["ollama"],
  "embedding_model": {"model_name": "bge-small-en", "dimension": 384, "loaded": true},
  "llm_model": "phi3"
}
```

### List Available Models
```http
GET /api/v1/llm/models/available
```
**Description**: List supported LLM and embedding models.

**Response**:
```json
{
  "llm_models": [
    {"name": "phi3", "description": "Fast, efficient model good for reasoning"},
    {"name": "mistral", "description": "Powerful model for complex tasks"}
  ],
  "embedding_models": [
    {"name": "bge-small-en", "description": "High quality English embeddings"},
    {"name": "nomic-embed-text", "description": "Good multilingual support"}
  ]
}
```

### List Available Providers
```http
GET /api/v1/llm/providers/available
```
**Description**: List detected LLM providers (Ollama, LocalAI, etc).

**Response**:
```json
{
  "detected_providers": ["ollama"],
  "providers": [
    {"name": "ollama", "description": "Local LLM server with easy model management", "url": "https://ollama.ai", "models": ["phi3", "mistral"]}
  ]
}
```

### Configure LLM/Embedding Models
```http
POST /api/v1/llm/config
```
**Description**: Set the active LLM and embedding models.

**Request Body**:
```json
{
  "llm_model": "phi3",
  "embedding_model": "bge-small-en",
  "llm_max_tokens": 1024,
  "llm_temperature": 0.7,
  "llm_top_p": 0.9
}
```
**Response**:
```json
{
  "success": true,
  "message": "Configuration updated. Embedding model loaded: true, Active provider: ollama",
  "config": {
    "llm_model": "phi3",
    "embedding_model": "bge-small-en",
    "llm_max_tokens": 1024,
    "llm_temperature": 0.7,
    "llm_top_p": 0.9
  }
}
```

### Enhanced Search (LLM-powered)
```http
POST /api/v1/llm/search
```
**Description**: Perform a search and get LLM-generated insights, summary, or recommendations.

**Request Body**:
```json
{
  "query": "project summary",
  "max_results": 5,
  "use_llm": true,
  "llm_model": "phi3",
  "embedding_model": "bge-small-en"
}
```
**Response**:
```json
{
  "enhanced": true,
  "query": "project summary",
  "llm_response": "This project is about...",
  "results": [ ... ],
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en"
}
```

### Ask a Question (Q&A)
```http
POST /api/v1/llm/question
```
**Description**: Ask a question about your documents and get an LLM-generated answer.

**Request Body**:
```json
{
  "question": "What is this project about?",
  "query": "project summary",
  "max_results": 5,
  "llm_model": "phi3"
}
```
**Response**:
```json
{
  "answered": true,
  "question": "What is this project about?",
  "answer": "This project is about...",
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en",
  "sources": ["/path/to/doc1.txt"]
}
```

### Summarize Search Results
```http
POST /api/v1/llm/summary
```
**Description**: Get a summary of the top search results using the LLM.

**Request Body**:
```json
{
  "query": "project summary",
  "max_results": 5,
  "llm_model": "phi3"
}
```
**Response**:
```json
{
  "summarized": true,
  "summary": "The main points are...",
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en",
  "result_count": 5
}
```

### Example: Enhanced Search with curl
```bash
curl -X POST "https://localhost:8443/api/v1/llm/search" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "project summary",
       "max_results": 5,
       "use_llm": true,
       "llm_model": "phi3",
       "embedding_model": "bge-small-en"
     }'
```

### Example: Q&A with Python
```python
import requests
resp = requests.post(
    "https://localhost:8443/api/v1/llm/question",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "question": "What is this project about?",
        "query": "project summary",
        "max_results": 5,
        "llm_model": "phi3"
    },
    verify=False
)
print(resp.json())
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information"
}
```

## Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Search endpoints**: 50 requests per minute per API key
- **Indexing endpoints**: 10 requests per minute per API key

## Permissions

API keys can have the following permissions:

- `read`: Read access to system information
- `search`: Perform searches on indexed documents
- `index`: Create and manage indexes
- `admin`: Full administrative access

## Examples

### Complete Search Workflow

1. **Create an API key**:
```bash
curl -X POST "https://localhost:8443/api/v1/auth/create-key" \
     -H "X-Admin-Key: your-admin-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Search Key",
       "description": "For search operations",
       "permissions": ["read", "search"]
     }'
```

2. **Add a directory**:
```bash
curl -X POST "https://localhost:8443/api/v1/directories/add?path=/path/to/documents"
```

3. **Refresh the directory** (start indexing):
```bash
curl -X POST "https://localhost:8443/api/v1/directories/refresh/%2Fpath%2Fto%2Fdocuments"
```

4. **Check indexing status**:
```bash
curl -X GET "https://localhost:8443/api/v1/directories/status/%2Fpath%2Fto%2Fdocuments"
```

5. **Search documents**:
```bash
curl -X POST "https://localhost:8443/api/v1/searcher/search" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "machine learning",
       "search_type": "semantic",
       "limit": 10
     }'
```

### Google Drive Integration

1. **Search Google Drive files**:
```bash
curl -X POST "https://localhost:8443/api/v1/searcher/gdrive" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "project proposal",
       "search_type": "semantic",
       "limit": 10
     }'
```

### System Monitoring

1. **Get system statistics**:
```bash
curl -X GET "https://localhost:8443/api/v1/stats/system"
```

2. **Get performance metrics**:
```bash
curl -X GET "https://localhost:8443/api/v1/stats/performance"
```

## Interactive Documentation

Access the interactive API documentation at:
- **Swagger UI**: https://localhost:8443/docs
- **ReDoc**: https://localhost:8443/redoc

## SDK Examples

### Python
```python
import requests

# Create API key
response = requests.post(
    "https://localhost:8443/api/v1/auth/create-key",
    headers={"X-Admin-Key": "your-admin-key"},
    json={
        "name": "Python SDK Key",
        "permissions": ["read", "search"]
    }
)
api_key = response.json()["data"]["api_key"]

# Search documents
response = requests.post(
    "https://localhost:8443/api/v1/searcher/search",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "query": "machine learning",
        "search_type": "semantic",
        "limit": 10
    }
)
results = response.json()
```

### JavaScript
```javascript
// Create API key
const createKeyResponse = await fetch('https://localhost:8443/api/v1/auth/create-key', {
  method: 'POST',
  headers: {
    'X-Admin-Key': 'your-admin-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'JavaScript SDK Key',
    permissions: ['read', 'search']
  })
});
const { api_key } = (await createKeyResponse.json()).data;

// Search documents
const searchResponse = await fetch('https://localhost:8443/api/v1/searcher/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${api_key}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'machine learning',
    search_type: 'semantic',
    limit: 10
  })
});
const results = await searchResponse.json();
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**: Accept the self-signed certificate in your browser or use `-k` flag with curl
2. **API Key Errors**: Ensure the API key is valid and has the required permissions
3. **Rate Limiting**: Wait before making additional requests
4. **Directory Not Found**: Ensure the directory path exists and is accessible

### Debug Mode

Enable debug mode for detailed logging:
```bash
export DEBUG=true
python start_https.py
```

### Health Check

Always check the health endpoint first:
```bash
curl -k https://localhost:8443/health
``` 