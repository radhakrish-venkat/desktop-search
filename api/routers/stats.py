"""
Statistics router for getting information about indexes and search performance
"""

from fastapi import APIRouter, HTTPException
import os
import json
from typing import Optional

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

@router.get("/system", response_model=APIResponse)
async def get_system_stats():
    """
    Get system statistics and health information
    """
    try:
        import psutil
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        stats = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available": memory.available,
            "disk_usage": disk.percent,
            "disk_free": disk.free,
            "uptime": psutil.boot_time()
        }
        
        return APIResponse(
            success=True,
            message="System statistics retrieved",
            data=stats
        )
        
    except ImportError:
        # psutil not available
        return APIResponse(
            success=True,
            message="System statistics retrieved (limited)",
            data={
                "note": "psutil not available for detailed system stats"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

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