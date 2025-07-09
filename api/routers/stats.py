"""
Statistics router for getting information about indexes and search performance
"""

from fastapi import APIRouter, HTTPException
import os
import json
from typing import Optional
import math

from api.models import APIResponse, StatsResponse, IndexStats
from api.config import settings

router = APIRouter()

@router.get("/index", response_model=APIResponse)
async def get_index_stats(directory: Optional[str] = None, index_path: Optional[str] = None):
    """
    Get statistics about an index
    """
    try:
        # This is a placeholder - in a real implementation, you'd load the index
        # and extract statistics from it
        stats = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "last_updated": None
        }
        
        if index_path and os.path.exists(index_path):
            # Load index and extract stats
            stats["total_files"] = 100  # Placeholder
            stats["last_updated"] = "2024-01-01T00:00:00Z"  # Placeholder
        
        return APIResponse(
            success=True,
            message="Index statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get index stats: {str(e)}")

@router.get("/semantic", response_model=APIResponse)
async def get_semantic_stats(db_path: Optional[str] = None):
    """
    Get statistics about semantic index
    """
    try:
        if not db_path:
            db_path = settings.DEFAULT_CHROMA_DB_PATH
        
        # This is a placeholder - in a real implementation, you'd connect to ChromaDB
        # and extract statistics
        stats = {
            "total_chunks": 0,
            "total_documents": 0,
            "model_name": settings.DEFAULT_MODEL,
            "db_path": db_path,
            "last_updated": None
        }
        
        if os.path.exists(db_path):
            # Check if ChromaDB has data
            stats["total_chunks"] = 500  # Placeholder
            stats["total_documents"] = 50  # Placeholder
            stats["last_updated"] = "2024-01-01T00:00:00Z"  # Placeholder
        
        return APIResponse(
            success=True,
            message="Semantic index statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get semantic stats: {str(e)}")

@router.get("/hybrid", response_model=APIResponse)
async def get_hybrid_stats(db_path: Optional[str] = None):
    """
    Get statistics about hybrid index
    """
    try:
        if not db_path:
            db_path = settings.DEFAULT_CHROMA_DB_PATH
        
        # This is a placeholder - in a real implementation, you'd combine
        # local index stats and semantic index stats
        stats = {
            "local_files": 0,
            "gdrive_files": 0,
            "total_chunks": 0,
            "model_name": settings.DEFAULT_MODEL,
            "db_path": db_path,
            "last_updated": None
        }
        
        return APIResponse(
            success=True,
            message="Hybrid index statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hybrid stats: {str(e)}")

def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total

def human_readable_size(size, decimal_places=2):
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, decimal_places)
    return f"{s} {units[i]}"

@router.get("/system", response_model=APIResponse)
async def get_system_stats():
    """
    Get comprehensive system statistics including index and directory information
    """
    try:
        # Get semantic index stats
        semantic_stats = await get_semantic_stats_internal()
        
        # Get directory information
        directories = await get_directory_stats()
        
        # Get DB size
        db_path = semantic_stats.get("db_path", settings.DEFAULT_CHROMA_DB_PATH)
        db_size_bytes = get_dir_size(db_path) if os.path.exists(db_path) else 0
        db_size_human = human_readable_size(db_size_bytes)
        
        # Combine all stats
        stats = {
            # Index statistics
            "total_chunks": semantic_stats.get("total_chunks", 0),
            "model_name": semantic_stats.get("model_name", settings.DEFAULT_MODEL),
            "persist_directory": db_path,
            "db_size_bytes": db_size_bytes,
            "db_size_human": db_size_human,
            # Directory statistics
            "total_directories": directories.get("total_directories", 0),
            "indexed_directories": directories.get("indexed_directories", 0),
            "total_files": directories.get("total_files", 0),
            # System information (if available)
            "system_info": {}
        }
        
        # Try to get system stats if psutil is available
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats["system_info"] = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available,
                "disk_usage": disk.percent,
                "disk_free": disk.free,
                "uptime": psutil.boot_time()
            }
        except ImportError:
            stats["system_info"] = {"note": "psutil not available for detailed system stats"}
        
        return APIResponse(
            success=True,
            message="System statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

async def get_semantic_stats_internal(db_path: Optional[str] = None):
    """Internal function to get semantic stats"""
    try:
        if not db_path:
            db_path = settings.DEFAULT_CHROMA_DB_PATH
        
        stats = {
            "total_chunks": 0,
            "total_documents": 0,
            "model_name": settings.DEFAULT_MODEL,
            "db_path": db_path,
            "last_updated": None
        }
        
        if os.path.exists(db_path):
            # Try to get actual ChromaDB stats
            try:
                import chromadb
                client = chromadb.PersistentClient(path=db_path)
                collections = client.list_collections()
                
                total_chunks = 0
                for collection in collections:
                    count = collection.count()
                    total_chunks += count
                
                stats["total_chunks"] = total_chunks
                stats["total_documents"] = len(collections)
                stats["last_updated"] = "2024-01-01T00:00:00Z"  # TODO: Get actual last update time
                
            except Exception:
                # Fallback to placeholder values
                stats["total_chunks"] = 0
                stats["total_documents"] = 0
        
        return stats
        
    except Exception:
        return {
            "total_chunks": 0,
            "total_documents": 0,
            "model_name": settings.DEFAULT_MODEL,
            "db_path": db_path,
            "last_updated": None
        }

async def get_directory_stats():
    """Get directory statistics"""
    try:
        directories_file = os.path.join(settings.DEFAULT_DATA_PATH, "directories.json")
        
        if not os.path.exists(directories_file):
            return {
                "total_directories": 0,
                "indexed_directories": 0,
                "total_files": 0
            }
        
        with open(directories_file, 'r') as f:
            data = json.load(f)
        
        # Handle both old format (direct array) and new format (with "directories" key)
        directories = data.get("directories", data) if isinstance(data, dict) else data
        
        total_directories = len(directories)
        indexed_directories = sum(1 for d in directories if d.get("status") == "indexed")
        total_files = sum(d.get("indexed_files", 0) for d in directories)
        
        return {
            "total_directories": total_directories,
            "indexed_directories": indexed_directories,
            "total_files": total_files
        }
        
    except Exception:
        return {
            "total_directories": 0,
            "indexed_directories": 0,
            "total_files": 0
        }

@router.get("/performance", response_model=APIResponse)
async def get_performance_stats():
    """
    Get search performance statistics
    """
    try:
        # This is a placeholder - in a real implementation, you'd track
        # search performance metrics over time
        stats = {
            "total_searches": 0,
            "average_search_time_ms": 0,
            "most_common_queries": [],
            "search_types": {
                "keyword": 0,
                "semantic": 0,
                "hybrid": 0
            }
        }
        
        return APIResponse(
            success=True,
            message="Performance statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}") 