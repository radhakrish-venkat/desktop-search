# Desktop Search FastAPI Backend

This FastAPI backend provides a REST API for the Desktop Search application, enabling web-based access to document indexing and search capabilities with a unified ChromaDB approach.

## Features

- **Unified ChromaDB Storage**: All search types (keyword, semantic, hybrid) use a single ChromaDB instance
- **Directory Management**: Add, remove, and refresh multiple directories with real-time progress tracking
- **Multiple Search Types**: Keyword, semantic, and hybrid search across all indexed directories
- **Background Processing**: Support for long-running indexing tasks with progress updates
- **CORS Support**: Ready for frontend integration (React, Vue, etc.)
- **Auto-generated Documentation**: Interactive API docs with Swagger UI
- **Type Safety**: Full Pydantic model validation
- **Real-time Progress**: Live progress tracking for indexing operations

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Automatic Initialization

The API server automatically initializes all necessary components on startup:

- **SSL Certificates**: Auto-generates self-signed certificates for HTTPS
- **Database Setup**: Creates ChromaDB directories and structure
- **Configuration Files**: Initializes default directories.json and metadata
- **API Key Validation**: Checks environment variables and provides guidance

You can also manage initialization manually:

```bash
# Check application status
python main.py status

# Initialize components
python main.py init

# Reinitialize everything from scratch
python main.py reinitialize --force
```

### 3. Start the API Server

```bash
# Option 1: Using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8443 --reload

# Option 2: Using the startup script
python start_api.py

# Option 3: Using HTTPS (recommended)
python start_https.py
```

### 4. Access the API

- **API Documentation**: https://localhost:8443/docs
- **Alternative Docs**: https://localhost:8443/redoc
- **Health Check**: https://localhost:8443/health
- **API Base URL**: https://localhost:8443/api/v1
- **Web Interface**: https://localhost:8443

**Note**: The frontend automatically uses `localhost` for API calls to avoid connection issues. If you experience "failed to fetch" errors, ensure you're accessing the web interface via `https://localhost:8443` rather than `https://127.0.0.1:8443`.

## API Endpoints

### Directory Management Endpoints

#### Add Directory
```http
POST /api/v1/directories/add?path=/path/to/documents
Content-Type: application/json
```

#### List Directories
```http
GET /api/v1/directories/list
```

#### Get Directory Status
```http
GET /api/v1/directories/status/{path}
```

#### Refresh Directory (Re-index)
```http
POST /api/v1/directories/refresh/{path}
Content-Type: application/json
```

#### Remove Directory
```http
DELETE /api/v1/directories/remove/{path}
```

### Search Endpoints

#### Search Documents (Unified)
```http
POST /api/v1/searcher/search
Content-Type: application/json

{
  "query": "search query",
  "search_type": "semantic",
  "limit": 10,
  "threshold": 0.3
}
```

**Search Types:**
- `semantic` - Semantic similarity search (default)
- `keyword` - Keyword/substring search
- `hybrid` - Combines semantic and keyword matching

### Statistics Endpoints

#### Get System Statistics
```http
GET /api/v1/stats/system
```

Returns comprehensive statistics about the unified index and directory management system.

## Response Models

### Search Response
```json
{
  "total_results": 5,
  "search_time_ms": 45.2,
  "results": [
    {
      "filepath": "/path/to/document.pdf",
      "filename": "document.pdf",
      "snippet": "Relevant text snippet...",
      "score": 0.85,
      "file_type": "pdf",
      "file_size": 1024000
    }
  ]
}
```

### Directory Response
```json
{
  "directories": [
    {
      "path": "/path/to/documents",
      "name": "documents",
      "status": "indexed",
      "indexed_files": 150,
      "total_files": 150,
      "progress": 1.0,
      "last_indexed": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### System Statistics Response
```json
{
  "data": {
    "total_chunks": 1500,
    "model_name": "all-MiniLM-L6-v2",
    "persist_directory": "./data/chroma_db",
    "total_directories": 3,
    "indexed_directories": 2,
    "total_files": 300
  }
}
```

## Frontend Integration

### CORS Configuration

The API is configured with CORS support for common frontend development servers:

- React (localhost:3000)
- Vue (localhost:8080)
- Vite (localhost:5173)
- Any localhost port for development

### Example Frontend Usage

```javascript
const API_BASE = 'https://localhost:8443/api/v1';

// Search documents
async function searchDocuments(query, searchType = 'semantic') {
  const response = await fetch(`${API_BASE}/searcher/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      search_type: searchType,
      limit: 10,
      threshold: 0.3
    })
  });

  const data = await response.json();
  return data;
}

// Add directory
async function addDirectory(path) {
  const response = await fetch(`${API_BASE}/directories/add?path=${encodeURIComponent(path)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  const data = await response.json();
  return data;
}

// List directories
async function listDirectories() {
  const response = await fetch(`${API_BASE}/directories/list`);
  const data = await response.json();
  return data;
}

// Refresh directory
async function refreshDirectory(path) {
  const response = await fetch(`${API_BASE}/directories/refresh/${encodeURIComponent(path)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  const data = await response.json();
  return data;
}

// Get system statistics
async function getSystemStats() {
  const response = await fetch(`${API_BASE}/stats/system`);
  const data = await response.json();
  return data;
}
```

### Real-time Progress Tracking

For real-time progress updates during indexing:

```javascript
// Poll for directory updates during indexing
function startProgressPolling() {
  const interval = setInterval(async () => {
    const directories = await listDirectories();
    
    // Check if any directory is still indexing
    const indexingDirs = directories.directories.filter(dir => dir.status === 'indexing');
    
    if (indexingDirs.length === 0) {
      clearInterval(interval);
      console.log('Indexing complete!');
    } else {
      // Update UI with progress
      updateProgressUI(directories.directories);
    }
  }, 2000); // Poll every 2 seconds
}
```

## Configuration

### Environment Variables

You can configure the API using environment variables:

```bash
# Server settings
HOST=0.0.0.0
PORT=8443
DEBUG=False

# Default paths (unified ChromaDB approach)
DATA_PATH=./data
CHROMA_DB_PATH=./data/chroma_db

# Search settings
DEFAULT_SEARCH_LIMIT=10
DEFAULT_SIMILARITY_THRESHOLD=0.3

# Model settings
DEFAULT_MODEL=all-MiniLM-L6-v2

# File size limits
MAX_FILE_SIZE_MB=50

# Background task settings
MAX_BACKGROUND_TASKS=5
```

### Configuration File

The configuration is managed in `api/config.py` and uses Pydantic settings for type safety.

## Development

### Project Structure

```
api/
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── models.py            # Pydantic models for request/response
└── routers/
    ├── __init__.py
    ├── directories.py   # Directory management endpoints
    ├── searcher.py      # Search endpoints
    └── stats.py         # Statistics endpoints
```

### Adding New Endpoints

1. Create or modify a router in `api/routers/`
2. Add Pydantic models in `api/models.py` if needed
3. Update the main app in `api/main.py` to include the router

### Testing

```bash
# Run the API server
uvicorn api.main:app --host 0.0.0.0 --port 8443 --reload

# Test endpoints using curl
curl -X GET http://localhost:8443/health

# Test search endpoint
curl -X POST http://localhost:8443/api/v1/searcher/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "semantic", "limit": 5}'

# Test directory management
curl -X GET http://localhost:8443/api/v1/directories/list

# Test adding a directory
curl -X POST "http://localhost:8443/api/v1/directories/add?path=/path/to/documents" \
  -H "Content-Type: application/json"
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8443
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8443

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8443"]
```

### Environment Configuration

For production, set appropriate environment variables:

```bash
export DEBUG=False
export HOST=0.0.0.0
export PORT=8443
export ALLOWED_ORIGINS="https://yourdomain.com"
```

## Key Features

### Unified ChromaDB Storage

- All search types (keyword, semantic, hybrid) use a single ChromaDB instance
- Consistent data storage in `data/chroma_db`
- No separate index files or pickle files
- Simplified data management

### Directory Management

- Add multiple directories to the index
- Real-time progress tracking during indexing
- Individual directory refresh capabilities
- Directory status monitoring
- Remove directories from the index

### Real-time Progress

- Live progress bars during indexing
- File count updates in real-time
- Background task status tracking
- Polling-based progress updates

### Search Capabilities

- **Semantic Search**: Find related content using embeddings
- **Keyword Search**: Traditional substring matching
- **Hybrid Search**: Combines semantic and keyword approaches
- **Unified Results**: Consistent ranking across all search types

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **CORS Issues**: Check the `ALLOWED_ORIGINS` configuration
3. **File Permissions**: Ensure the API has read access to indexed directories
4. **Memory Issues**: Adjust file size limits and background task limits
5. **ChromaDB Issues**: Check that the `data/chroma_db` directory is writable

### Logs

The API uses standard Python logging. Check logs for detailed error information.

### Directory Status Issues

- **"not_indexed"**: Directory exists but hasn't been indexed yet
- **"indexing"**: Directory is currently being indexed
- **"indexed"**: Directory has been successfully indexed
- **"error"**: An error occurred during indexing

## Next Steps

- [ ] Add authentication and authorization
- [ ] Implement rate limiting
- [ ] Add caching layer (Redis)
- [ ] Create comprehensive test suite
- [ ] Add monitoring and metrics
- [ ] Implement WebSocket support for real-time updates
- [ ] Add Google Drive integration endpoints
- [ ] Implement search result caching 