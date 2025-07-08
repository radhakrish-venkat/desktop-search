# Desktop Search FastAPI Backend

This FastAPI backend provides a REST API for the Desktop Search application, enabling web-based access to document indexing and search capabilities.

## Features

- **RESTful API**: Full REST API for all desktop search functionality
- **Multiple Search Types**: Keyword, semantic, and hybrid search
- **Background Processing**: Support for long-running indexing tasks
- **CORS Support**: Ready for frontend integration (React, Vue, etc.)
- **Auto-generated Documentation**: Interactive API docs with Swagger UI
- **Type Safety**: Full Pydantic model validation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Option 1: Using the startup script
python start_api.py

# Option 2: Using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Base URL**: http://localhost:8000/api/v1

## API Endpoints

### Indexer Endpoints

#### Build Index
```http
POST /api/v1/indexer/build
Content-Type: application/json

{
  "directory": "/path/to/documents",
  "index_type": "full",
  "force_full": false,
  "save_path": null,
  "model": "all-MiniLM-L6-v2",
  "db_path": null
}
```

#### Build Google Drive Index
```http
POST /api/v1/indexer/gdrive
Content-Type: application/json

{
  "folder_id": "optional_folder_id",
  "query": "optional_query_filter",
  "save_path": null
}
```

#### Build Hybrid Index
```http
POST /api/v1/indexer/hybrid
Content-Type: application/json

{
  "directory": "/path/to/documents",
  "gdrive_folder_id": "optional_folder_id",
  "gdrive_query": "optional_query_filter",
  "save_path": null,
  "force_full": false,
  "model": "all-MiniLM-L6-v2",
  "db_path": null
}
```

#### Background Indexing
```http
POST /api/v1/indexer/build/background
Content-Type: application/json

{
  "directory": "/path/to/documents",
  "index_type": "semantic",
  "force_full": false
}
```

#### Check Task Status
```http
GET /api/v1/indexer/task/{task_id}
```

### Searcher Endpoints

#### Search Documents
```http
POST /api/v1/searcher/search
Content-Type: application/json

{
  "query": "search query",
  "search_type": "keyword",
  "limit": 10,
  "threshold": 0.3,
  "directory": "/path/to/documents",
  "index_path": null,
  "db_path": null
}
```

#### Search Google Drive
```http
POST /api/v1/searcher/gdrive
Content-Type: application/json

{
  "query": "search query",
  "search_type": "keyword",
  "limit": 10,
  "threshold": 0.3
}
```

#### Get Search Suggestions
```http
GET /api/v1/searcher/suggestions?query=partial&limit=5
```

### Google Drive Endpoints

#### Setup Google Drive
```http
POST /api/v1/gdrive/setup
Content-Type: application/json

{
  "credentials_path": "/path/to/credentials.json"
}
```

#### Check Google Drive Status
```http
GET /api/v1/gdrive/status
```

#### Index Google Drive
```http
POST /api/v1/gdrive/index
Content-Type: application/json

{
  "folder_id": "optional_folder_id",
  "query": "optional_query_filter",
  "save_path": null
}
```

#### Search Google Drive
```http
GET /api/v1/gdrive/search?query=search_query&folder_id=optional&limit=10
```

### Statistics Endpoints

#### Get Index Statistics
```http
GET /api/v1/stats/index?directory=/path/to/documents&index_path=null
```

#### Get Semantic Index Statistics
```http
GET /api/v1/stats/semantic?db_path=./chroma_db
```

#### Get Hybrid Index Statistics
```http
GET /api/v1/stats/hybrid?db_path=./chroma_db
```

#### Get System Statistics
```http
GET /api/v1/stats/system
```

#### Get Performance Statistics
```http
GET /api/v1/stats/performance
```

## Frontend Integration

### CORS Configuration

The API is configured with CORS support for common frontend development servers:

- React (localhost:3000)
- Vue (localhost:8080)
- Vite (localhost:5173)

### Example Frontend Usage

```javascript
// Search documents
const searchResponse = await fetch('http://localhost:8000/api/v1/searcher/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'machine learning',
    search_type: 'semantic',
    limit: 10,
    threshold: 0.3
  })
});

const searchData = await searchResponse.json();
console.log(searchData.results);

// Build index
const indexResponse = await fetch('http://localhost:8000/api/v1/indexer/build', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    directory: '/path/to/documents',
    index_type: 'semantic',
    force_full: false
  })
});

const indexData = await indexResponse.json();
console.log(indexData.stats);
```

## Configuration

### Environment Variables

You can configure the API using environment variables:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Default paths
CHROMA_DB_PATH=./chroma_db
INDEX_PATH=./index.pkl
METADATA_PATH=./index_metadata.json

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

The configuration is managed in `api/config.py` and can be extended for additional settings.

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
    ├── indexer.py       # Indexing endpoints
    ├── searcher.py      # Search endpoints
    ├── google_drive.py  # Google Drive endpoints
    └── stats.py         # Statistics endpoints
```

### Adding New Endpoints

1. Create or modify a router in `api/routers/`
2. Add Pydantic models in `api/models.py` if needed
3. Update the main app in `api/main.py` to include the router

### Testing

```bash
# Run the API server
python start_api.py

# Test endpoints using curl
curl -X GET http://localhost:8000/health

# Test search endpoint
curl -X POST http://localhost:8000/api/v1/searcher/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "keyword", "limit": 5}'
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

For production, set appropriate environment variables:

```bash
export DEBUG=False
export HOST=0.0.0.0
export PORT=8000
export ALLOWED_ORIGINS="https://yourdomain.com"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **CORS Issues**: Check the `ALLOWED_ORIGINS` configuration
3. **File Permissions**: Ensure the API has read access to indexed directories
4. **Memory Issues**: Adjust file size limits and background task limits

### Logs

The API uses standard Python logging. Check logs for detailed error information.

## Next Steps

- [ ] Add authentication and authorization
- [ ] Implement rate limiting
- [ ] Add caching layer (Redis)
- [ ] Create comprehensive test suite
- [ ] Add monitoring and metrics
- [ ] Implement WebSocket support for real-time updates 