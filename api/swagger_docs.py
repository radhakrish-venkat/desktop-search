"""
Comprehensive Swagger/OpenAPI documentation for Desktop Search API
This module provides detailed API documentation with examples and schemas
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with detailed documentation"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Desktop Search API",
        version="1.0.0",
        description="""
# Desktop Search API

A comprehensive REST API for indexing and searching local documents with semantic search capabilities.

## Features

- **Multi-format Support**: Indexes PDF, DOCX, XLSX, PPTX, and TXT files
- **Semantic Search**: Advanced semantic search using sentence transformers
- **Hybrid Search**: Combines semantic and keyword matching
- **Google Drive Integration**: Search Google Drive files
- **Directory Management**: Manage multiple indexed directories
- **API Key Authentication**: Secure API key management system
- **Real-time Progress**: Background task processing with progress tracking

## Authentication

The API supports two authentication methods:
1. **API Key Authentication** - Simple key-based access
2. **JWT Token Authentication** - Token-based with expiration

### Getting Started

1. **Set up admin key** (first time only):
   ```bash
   export API_KEY="your-super-secret-admin-key-here"
   ```

2. **Create your first API key**:
   ```bash
   curl -X POST "https://localhost:8443/api/v1/auth/create-key" \\
        -H "X-Admin-Key: your-admin-key" \\
        -H "Content-Type: application/json" \\
        -d '{
          "name": "My First Key",
          "description": "For testing",
          "permissions": ["read", "search"]
        }'
   ```

3. **Use your API key**:
   ```bash
   curl -X POST "https://localhost:8443/api/v1/searcher/search" \\
        -H "Authorization: Bearer YOUR_API_KEY" \\
        -H "Content-Type: application/json" \\
        -d '{
          "query": "machine learning",
          "search_type": "semantic",
          "limit": 10
        }'
   ```

## Base URL

- **Development**: `https://localhost:8443`
- **Production**: Configure your domain

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Search endpoints**: 50 requests per minute per API key
- **Indexing endpoints**: 10 requests per minute per API key

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
        """,
        routes=app.routes,
    )
    
    # Add detailed path documentation
    openapi_schema["paths"] = {
        # Health Check
        "/health": {
            "get": {
                "summary": "Health Check",
                "description": "Check if the API is running and healthy",
                "tags": ["system"],
                "responses": {
                    "200": {
                        "description": "API is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Desktop Search API is running"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string", "example": "healthy"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        # API Info
        "/api/info": {
            "get": {
                "summary": "API Information",
                "description": "Get basic information about the API",
                "tags": ["system"],
                "responses": {
                    "200": {
                        "description": "API information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Desktop Search API"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "version": {"type": "string", "example": "1.0.0"},
                                                "docs": {"type": "string", "example": "/docs"},
                                                "health": {"type": "string", "example": "/health"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        # Authentication Endpoints
        "/api/v1/auth/create-key": {
            "post": {
                "summary": "Create API Key",
                "description": "Create a new API key with specified permissions",
                "tags": ["authentication"],
                "security": [{"AdminKey": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "example": "My Search Key"},
                                    "description": {"type": "string", "example": "Key for search operations"},
                                    "expires_days": {"type": "integer", "minimum": 1, "maximum": 365, "example": 30},
                                    "permissions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "example": ["read", "search"]
                                    }
                                },
                                "required": ["name"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "API key created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "API key created successfully"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "api_key": {"type": "string", "example": "ds_abc123..."},
                                                "key_info": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "string"},
                                                        "name": {"type": "string"},
                                                        "description": {"type": "string"},
                                                        "created_at": {"type": "string"},
                                                        "expires_at": {"type": "string"},
                                                        "permissions": {"type": "array", "items": {"type": "string"}}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Invalid admin key"},
                    "500": {"description": "Internal server error"}
                }
            }
        },
        
        "/api/v1/auth/list-keys": {
            "get": {
                "summary": "List API Keys",
                "description": "List all API keys (admin only)",
                "tags": ["authentication"],
                "security": [{"AdminKey": []}],
                "responses": {
                    "200": {
                        "description": "List of API keys",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "keys": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "name": {"type": "string"},
                                                    "description": {"type": "string"},
                                                    "created_at": {"type": "string"},
                                                    "expires_at": {"type": "string"},
                                                    "permissions": {"type": "array", "items": {"type": "string"}},
                                                    "is_active": {"type": "boolean"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Admin key required"},
                    "500": {"description": "Internal server error"}
                }
            }
        },
        
        "/api/v1/auth/revoke-key/{key_id}": {
            "delete": {
                "summary": "Revoke API Key",
                "description": "Revoke an API key (admin only)",
                "tags": ["authentication"],
                "security": [{"AdminKey": []}],
                "parameters": [
                    {
                        "name": "key_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "ID of the API key to revoke"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "API key revoked successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "API key 'My Key' revoked successfully"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Admin key required"},
                    "404": {"description": "API key not found"},
                    "500": {"description": "Internal server error"}
                }
            }
        },
        
        "/api/v1/auth/validate-key": {
            "post": {
                "summary": "Validate API Key",
                "description": "Validate an API key and get its information",
                "tags": ["authentication"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "api_key": {"type": "string", "example": "ds_abc123..."}
                                },
                                "required": ["api_key"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "API key is valid",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "API key is valid"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "key_info": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "string"},
                                                        "name": {"type": "string"},
                                                        "permissions": {"type": "array", "items": {"type": "string"}}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Invalid or expired API key"}
                }
            }
        },
        
        "/api/v1/auth/login": {
            "post": {
                "summary": "Login with API Key",
                "description": "Get JWT token using API key",
                "tags": ["authentication"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "api_key": {"type": "string", "example": "ds_abc123..."}
                                },
                                "required": ["api_key"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Login successful"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "access_token": {"type": "string", "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                                                "token_type": {"type": "string", "example": "bearer"},
                                                "expires_in": {"type": "integer", "example": 3600}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Invalid API key"}
                }
            }
        },
        
        # Search Endpoints
        "/api/v1/searcher/search": {
            "post": {
                "summary": "Search Documents",
                "description": "Search indexed documents using semantic, keyword, or hybrid search",
                "tags": ["searcher"],
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "example": "machine learning algorithms"},
                                    "search_type": {
                                        "type": "string",
                                        "enum": ["keyword", "semantic", "hybrid"],
                                        "default": "semantic",
                                        "example": "semantic"
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 100,
                                        "default": 10,
                                        "example": 10
                                    },
                                    "threshold": {
                                        "type": "number",
                                        "minimum": 0.0,
                                        "maximum": 1.0,
                                        "default": 0.3,
                                        "example": 0.3
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Search results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "example": "machine learning algorithms"},
                                        "search_type": {"type": "string", "example": "semantic"},
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "filepath": {"type": "string", "example": "/path/to/document.pdf"},
                                                    "filename": {"type": "string", "example": "document.pdf"},
                                                    "snippet": {"type": "string", "example": "This document discusses machine learning algorithms..."},
                                                    "score": {"type": "number", "example": 0.85},
                                                    "file_type": {"type": "string", "example": "pdf"},
                                                    "file_size": {"type": "integer", "example": 1024000},
                                                    "last_modified": {"type": "string", "example": "2024-01-15T10:30:00Z"}
                                                }
                                            }
                                        },
                                        "total_results": {"type": "integer", "example": 5},
                                        "search_time_ms": {"type": "number", "example": 45.2}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid request parameters"},
                    "401": {"description": "Invalid API key"},
                    "429": {"description": "Rate limit exceeded"},
                    "500": {"description": "Search failed"}
                }
            }
        },
        
        "/api/v1/searcher/gdrive": {
            "post": {
                "summary": "Search Google Drive",
                "description": "Search Google Drive files directly (requires Google Drive setup)",
                "tags": ["searcher"],
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "example": "project proposal"},
                                    "search_type": {
                                        "type": "string",
                                        "enum": ["keyword", "semantic", "hybrid"],
                                        "default": "semantic",
                                        "example": "semantic"
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 100,
                                        "default": 10,
                                        "example": 10
                                    },
                                    "threshold": {
                                        "type": "number",
                                        "minimum": 0.0,
                                        "maximum": 1.0,
                                        "default": 0.3,
                                        "example": 0.3
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Google Drive search results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "example": "project proposal"},
                                        "search_type": {"type": "string", "example": "semantic"},
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "filepath": {"type": "string", "example": "gdrive://document.docx"},
                                                    "filename": {"type": "string", "example": "document.docx"},
                                                    "snippet": {"type": "string", "example": "This document contains the project proposal..."},
                                                    "score": {"type": "number", "example": 0.92},
                                                    "file_type": {"type": "string", "example": "docx"},
                                                    "file_size": {"type": "integer", "example": 2048000},
                                                    "last_modified": {"type": "string", "example": "2024-01-15T10:30:00Z"}
                                                }
                                            }
                                        },
                                        "total_results": {"type": "integer", "example": 3},
                                        "search_time_ms": {"type": "number", "example": 120.5}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid request parameters"},
                    "401": {"description": "Invalid API key"},
                    "500": {"description": "Google Drive search failed"}
                }
            }
        },
        
        "/api/v1/searcher/suggestions": {
            "get": {
                "summary": "Get Search Suggestions",
                "description": "Get search suggestions based on partial query",
                "tags": ["searcher"],
                "parameters": [
                    {
                        "name": "query",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Partial search query"
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 5},
                        "description": "Maximum number of suggestions"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search suggestions",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Search suggestions retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "suggestions": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "example": ["machine learning document", "machine learning file", "machine learning report"]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get suggestions"}
                }
            }
        },
        
        # Directory Management Endpoints
        "/api/v1/directories/list": {
            "get": {
                "summary": "List Directories",
                "description": "Get list of all indexed directories",
                "tags": ["directories"],
                "responses": {
                    "200": {
                        "description": "List of directories",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "directories": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "path": {"type": "string", "example": "/path/to/documents"},
                                                    "name": {"type": "string", "example": "documents"},
                                                    "status": {"type": "string", "example": "indexed"},
                                                    "progress": {"type": "number", "example": 1.0},
                                                    "last_indexed": {"type": "string", "example": "2024-01-15T10:30:00Z"},
                                                    "total_files": {"type": "integer", "example": 150},
                                                    "indexed_files": {"type": "integer", "example": 150},
                                                    "task_id": {"type": "string", "example": "dir_1705312200_documents"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        "/api/v1/directories/add": {
            "post": {
                "summary": "Add Directory",
                "description": "Add a new directory to the index",
                "tags": ["directories"],
                "parameters": [
                    {
                        "name": "path",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Path to the directory to add"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Directory added successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Directory added: /path/to/documents"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "directory": {
                                                    "type": "object",
                                                    "properties": {
                                                        "path": {"type": "string", "example": "/path/to/documents"},
                                                        "name": {"type": "string", "example": "documents"},
                                                        "status": {"type": "string", "example": "not_indexed"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid directory path or directory already exists"},
                    "404": {"description": "Directory not found"}
                }
            }
        },
        
        "/api/v1/directories/refresh/{path}": {
            "post": {
                "summary": "Refresh Directory",
                "description": "Refresh/rebuild index for a specific directory",
                "tags": ["directories"],
                "parameters": [
                    {
                        "name": "path",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Path to the directory to refresh"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Indexing started successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Indexing started for: /path/to/documents"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "task_id": {"type": "string", "example": "dir_1705312200_documents"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Directory is already being indexed"},
                    "404": {"description": "Directory not found"}
                }
            }
        },
        
        "/api/v1/directories/status/{path}": {
            "get": {
                "summary": "Get Directory Status",
                "description": "Get indexing status for a specific directory",
                "tags": ["directories"],
                "parameters": [
                    {
                        "name": "path",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Path to the directory"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Directory status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string", "example": "/path/to/documents"},
                                        "status": {"type": "string", "example": "indexing"},
                                        "progress": {"type": "number", "example": 0.75},
                                        "message": {"type": "string", "example": "Indexing: document.pdf"},
                                        "task_id": {"type": "string", "example": "dir_1705312200_documents"},
                                        "total_files": {"type": "integer", "example": 150},
                                        "indexed_files": {"type": "integer", "example": 112}
                                    }
                                }
                            }
                        }
                    },
                    "404": {"description": "Directory not found"}
                }
            }
        },
        
        "/api/v1/directories/remove/{path}": {
            "delete": {
                "summary": "Remove Directory",
                "description": "Remove a directory from the index",
                "tags": ["directories"],
                "parameters": [
                    {
                        "name": "path",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Path to the directory to remove"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Directory removed successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Directory removed: /path/to/documents"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "directory": {
                                                    "type": "object",
                                                    "properties": {
                                                        "path": {"type": "string", "example": "/path/to/documents"},
                                                        "name": {"type": "string", "example": "documents"},
                                                        "status": {"type": "string", "example": "indexed"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Cannot remove directory while indexing"},
                    "404": {"description": "Directory not found"}
                }
            }
        },
        
        # Statistics Endpoints
        "/api/v1/stats/system": {
            "get": {
                "summary": "Get System Statistics",
                "description": "Get comprehensive system statistics including index and directory information",
                "tags": ["stats"],
                "responses": {
                    "200": {
                        "description": "System statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "System statistics retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "total_chunks": {"type": "integer", "example": 1500},
                                                "model_name": {"type": "string", "example": "all-MiniLM-L6-v2"},
                                                "persist_directory": {"type": "string", "example": "./data/chroma_db"},
                                                "db_size_bytes": {"type": "integer", "example": 52428800},
                                                "db_size_human": {"type": "string", "example": "50.0 MB"},
                                                "total_directories": {"type": "integer", "example": 3},
                                                "indexed_directories": {"type": "integer", "example": 2},
                                                "total_files": {"type": "integer", "example": 300},
                                                "system_info": {
                                                    "type": "object",
                                                    "properties": {
                                                        "cpu_usage": {"type": "number", "example": 25.5},
                                                        "memory_usage": {"type": "number", "example": 60.2},
                                                        "memory_available": {"type": "integer", "example": 8589934592},
                                                        "disk_usage": {"type": "number", "example": 75.8},
                                                        "disk_free": {"type": "integer", "example": 107374182400},
                                                        "uptime": {"type": "number", "example": 1705312200}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get system stats"}
                }
            }
        },
        
        "/api/v1/stats/index": {
            "get": {
                "summary": "Get Index Statistics",
                "description": "Get statistics about a specific index",
                "tags": ["stats"],
                "parameters": [
                    {
                        "name": "directory",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Directory path for the index"
                    },
                    {
                        "name": "index_path",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Path to the index file"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Index statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Index statistics retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "total_files": {"type": "integer", "example": 150},
                                                "total_size": {"type": "integer", "example": 52428800},
                                                "file_types": {
                                                    "type": "object",
                                                    "example": {
                                                        "pdf": 50,
                                                        "docx": 30,
                                                        "txt": 20
                                                    }
                                                },
                                                "last_updated": {"type": "string", "example": "2024-01-15T10:30:00Z"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get index stats"}
                }
            }
        },
        
        "/api/v1/stats/semantic": {
            "get": {
                "summary": "Get Semantic Index Statistics",
                "description": "Get statistics about the semantic index",
                "tags": ["stats"],
                "parameters": [
                    {
                        "name": "db_path",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Path to the ChromaDB directory"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Semantic index statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Semantic index statistics retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "total_chunks": {"type": "integer", "example": 1500},
                                                "total_documents": {"type": "integer", "example": 150},
                                                "model_name": {"type": "string", "example": "all-MiniLM-L6-v2"},
                                                "db_path": {"type": "string", "example": "./data/chroma_db"},
                                                "last_updated": {"type": "string", "example": "2024-01-15T10:30:00Z"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get semantic stats"}
                }
            }
        },
        
        "/api/v1/stats/hybrid": {
            "get": {
                "summary": "Get Hybrid Index Statistics",
                "description": "Get statistics about the hybrid index",
                "tags": ["stats"],
                "parameters": [
                    {
                        "name": "db_path",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Path to the ChromaDB directory"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Hybrid index statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Hybrid index statistics retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "local_files": {"type": "integer", "example": 150},
                                                "gdrive_files": {"type": "integer", "example": 50},
                                                "total_chunks": {"type": "integer", "example": 2000},
                                                "model_name": {"type": "string", "example": "all-MiniLM-L6-v2"},
                                                "db_path": {"type": "string", "example": "./data/chroma_db"},
                                                "last_updated": {"type": "string", "example": "2024-01-15T10:30:00Z"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get hybrid stats"}
                }
            }
        },
        
        "/api/v1/stats/performance": {
            "get": {
                "summary": "Get Performance Statistics",
                "description": "Get performance statistics and metrics",
                "tags": ["stats"],
                "responses": {
                    "200": {
                        "description": "Performance statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "message": {"type": "string", "example": "Performance statistics retrieved"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "avg_search_time_ms": {"type": "number", "example": 45.2},
                                                "total_searches": {"type": "integer", "example": 1250},
                                                "cache_hit_rate": {"type": "number", "example": 0.85},
                                                "memory_usage_mb": {"type": "number", "example": 512.5},
                                                "disk_usage_mb": {"type": "number", "example": 1024.0}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Failed to get performance stats"}
                }
            }
        }
    }
    
    # Add security schemes
    openapi_schema["components"] = {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "API key in format: Bearer YOUR_API_KEY"
            },
            "AdminKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Admin-Key",
                "description": "Admin key for administrative operations"
            }
        }
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "https://localhost:8443",
            "description": "Development server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_swagger_docs(app: FastAPI):
    """Setup custom OpenAPI documentation"""
    app.openapi = lambda: custom_openapi(app) 