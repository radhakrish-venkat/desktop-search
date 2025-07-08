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
    directory: Optional[str] = Field(None, description="Directory to search in")
    index_path: Optional[str] = Field(None, description="Path to index file")
    db_path: Optional[str] = Field(None, description="ChromaDB path for semantic search")

class IndexRequest(BaseModel):
    """Index request model"""
    directory: str = Field(..., description="Directory to index")
    index_type: IndexType = Field(IndexType.FULL, description="Type of indexing to perform")
    force_full: bool = Field(False, description="Force full indexing even if incremental is possible")
    save_path: Optional[str] = Field(None, description="Custom path to save index")
    model: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model for semantic indexing")
    db_path: Optional[str] = Field(None, description="ChromaDB path for semantic indexing")

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