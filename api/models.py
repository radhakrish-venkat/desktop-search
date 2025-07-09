"""
Pydantic models for API request and response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class SearchType(str, Enum):
    """Search type enumeration"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class IndexType(str, Enum):
    """Index type enumeration"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(SearchType.KEYWORD, description="Type of search to perform")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: float = Field(0.3, ge=0.0, le=1.0, description="Similarity threshold for semantic search")

class IndexRequest(BaseModel):
    """Index request model"""
    force_full: bool = Field(False, description="Force full indexing even if incremental is possible")
    model: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model for semantic indexing")
    directory: str = Field(..., description="Directory to index")

class GoogleDriveIndexRequest(BaseModel):
    """Google Drive index request model"""
    folder_id: Optional[str] = Field(None, description="Google Drive folder ID to index")
    query: Optional[str] = Field(None, description="Additional query to filter files")
    save_path: Optional[str] = Field(None, description="Path to save index")

class HybridIndexRequest(BaseModel):
    """Hybrid index request model"""
    directory: str = Field(..., description="Local directory to index")
    gdrive_folder_id: Optional[str] = Field(None, description="Google Drive folder ID to include")
    gdrive_query: Optional[str] = Field(None, description="Additional query to filter Google Drive files")
    save_path: Optional[str] = Field(None, description="Path to save index")
    force_full: bool = Field(False, description="Force full indexing")
    model: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model")
    db_path: Optional[str] = Field(None, description="ChromaDB path")

class SearchResult(BaseModel):
    """Search result model"""
    filepath: str
    filename: str
    snippet: str
    score: Optional[float] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    last_modified: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    search_type: SearchType
    results: List[SearchResult]
    total_results: int
    search_time_ms: float

class IndexStats(BaseModel):
    """Index statistics model"""
    indexing_type: str
    total_files: int
    new_files: int = 0
    modified_files: int = 0
    deleted_files: int = 0
    skipped_files: int = 0
    total_chunks: int = 0
    index_path: Optional[str] = None
    db_path: Optional[str] = None

class IndexResponse(BaseModel):
    """Index response model"""
    success: bool
    message: str
    stats: IndexStats
    index_path: Optional[str] = None

class TaskStatus(BaseModel):
    """Background task status model"""
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str

class StatsResponse(BaseModel):
    """Statistics response model"""
    index_stats: Optional[IndexStats] = None
    semantic_stats: Optional[Dict[str, Any]] = None
    hybrid_stats: Optional[Dict[str, Any]] = None

class DirectoryInfo(BaseModel):
    """Directory information model"""
    path: str
    name: str
    status: str = "not_indexed"  # not_indexed, indexing, indexed, error
    progress: float = 0.0
    last_indexed: Optional[str] = None
    total_files: int = 0
    indexed_files: int = 0
    task_id: Optional[str] = None

class DirectoryList(BaseModel):
    """List of indexed directories"""
    directories: List[DirectoryInfo]

class DirectoryStatus(BaseModel):
    """Directory indexing status"""
    path: str
    status: str
    progress: float = 0.0
    message: str = ""
    task_id: Optional[str] = None
    total_files: int = 0
    indexed_files: int = 0

class APIKeyCreate(BaseModel):
    """API key creation request model"""
    name: str = Field(..., description="Name for the API key")
    description: Optional[str] = Field(None, description="Description of the API key")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration")
    permissions: Optional[List[str]] = Field(None, description="List of permissions")
    admin_key: Optional[str] = Field(None, description="Admin key for authentication")

class APIKeyInfo(BaseModel):
    """API key information model"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None
    permissions: List[str]
    is_active: bool

class APIKeyList(BaseModel):
    """API key list response model"""
    keys: List[APIKeyInfo] 