"""
Indexer router for building and managing search indexes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict, Any
import os
import time
import uuid
from datetime import datetime

# Import core functionality
from pkg.indexer.core import build_index, save_index, load_index
from pkg.indexer.semantic import SemanticIndexer
from pkg.indexer.semantic_hybrid import HybridSemanticIndexer
from pkg.indexer.incremental import smart_index, smart_semantic_index
from pkg.indexer.google_drive import build_google_drive_index
from pkg.indexer.google_drive import merge_indices

from api.models import (
    IndexRequest, IndexResponse, IndexStats, APIResponse,
    GoogleDriveIndexRequest, HybridIndexRequest, TaskStatus
)
from api.config import settings

router = APIRouter()

# SQLite task storage
import sqlite3
import json
from datetime import datetime
import threading

class SQLiteTaskStorage:
    def __init__(self, db_path='tasks.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the database table"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    status TEXT,
                    progress REAL DEFAULT 0.0,
                    message TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
    
    def set_task(self, task_id: str, status: str, progress: float = 0.0, 
                 message: str = "", result: Optional[dict] = None, error: Optional[str] = None):
        """Store or update task status"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO tasks 
                (task_id, status, progress, message, result, error, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 
                status, 
                progress, 
                message, 
                json.dumps(result) if result else None,
                error,
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
    
    def get_task(self, task_id: str):
        """Get task status"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT task_id, status, progress, message, result, error, 
                       created_at, updated_at
                FROM tasks WHERE task_id = ?
            ''', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'task_id': row[0],
                    'status': row[1],
                    'progress': row[2],
                    'message': row[3],
                    'result': json.loads(row[4]) if row[4] else None,
                    'error': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
    
    def cleanup_old_tasks(self, days_old: int = 7):
        """Clean up old completed/failed tasks"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                DELETE FROM tasks 
                WHERE status IN ('completed', 'failed') 
                AND updated_at < datetime('now', '-{} days')
            '''.format(days_old))
            conn.commit()
            conn.close()

# Initialize SQLite task storage
task_storage = SQLiteTaskStorage()

def get_default_index_path(directory: str) -> str:
    """Get the default index file path for a directory"""
    # Use chroma_db folder for all index files
    directory_name = os.path.basename(directory.rstrip('/'))
    return os.path.join(settings.DEFAULT_CHROMA_DB_PATH, f"{directory_name}_index.pkl")

@router.post("/build", response_model=IndexResponse)
async def build_index_endpoint(request: IndexRequest):
    """
    Build a search index for the specified directory
    """
    try:
        start_time = time.time()
        
        # Determine index path
        if request.save_path:
            index_path = request.save_path
        else:
            index_path = get_default_index_path(request.directory)
        
        # Build index based on type
        if request.index_type.value == "semantic":
            # Semantic indexing
            stats = smart_semantic_index(
                directory_path=request.directory,
                persist_directory=request.db_path or settings.DEFAULT_CHROMA_DB_PATH,
                model_name=request.model,
                force_full=request.force_full
            )
            
            if not stats:
                raise HTTPException(status_code=500, detail="Failed to build semantic index")
            
            stats_data = stats.get('stats', {})
            indexing_type = stats_data.get('indexing_type', 'semantic')
            
        elif request.index_type.value == "hybrid":
            # Hybrid indexing (local + semantic)
            stats = smart_semantic_index(
                directory_path=request.directory,
                persist_directory=request.db_path or settings.DEFAULT_CHROMA_DB_PATH,
                model_name=request.model,
                force_full=request.force_full
            )
            
            if not stats:
                raise HTTPException(status_code=500, detail="Failed to build hybrid index")
            
            stats_data = stats.get('stats', {})
            indexing_type = stats_data.get('indexing_type', 'hybrid')
            
        else:
            # Standard keyword indexing
            index_data = smart_index(
                directory_path=request.directory,
                index_path=index_path,
                force_full=request.force_full
            )
            
            if not index_data:
                raise HTTPException(status_code=500, detail="Failed to build index")
            
            stats_data = index_data.get('stats', {})
            indexing_type = stats_data.get('indexing_type', 'keyword')
        
        end_time = time.time()
        
        # Create response
        index_stats = IndexStats(
            indexing_type=indexing_type,
            total_files=stats_data.get('total_files', 0),
            new_files=stats_data.get('new_files', 0),
            modified_files=stats_data.get('modified_files', 0),
            deleted_files=stats_data.get('deleted_files', 0),
            skipped_files=stats_data.get('skipped_files', 0),
            total_chunks=stats_data.get('total_chunks', 0),
            index_path=index_path if request.index_type.value != "semantic" else None,
            db_path=request.db_path or settings.DEFAULT_CHROMA_DB_PATH if request.index_type.value in ["semantic", "hybrid"] else None
        )
        
        return IndexResponse(
            success=True,
            message=f"Index built successfully in {end_time - start_time:.2f} seconds",
            stats=index_stats,
            index_path=index_path if request.index_type.value != "semantic" else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/gdrive", response_model=IndexResponse)
async def build_gdrive_index_endpoint(request: GoogleDriveIndexRequest):
    """
    Build a search index for Google Drive files
    """
    try:
        start_time = time.time()
        
        # Build Google Drive index
        index_data = build_google_drive_index(
            folder_id=request.folder_id,
            query=request.query
        )
        
        if not index_data:
            raise HTTPException(status_code=500, detail="Failed to build Google Drive index")
        
        end_time = time.time()
        
        # Create response
        index_stats = IndexStats(
            indexing_type="gdrive",
            total_files=len(index_data.get('documents', [])),
            index_path=request.save_path
        )
        
        return IndexResponse(
            success=True,
            message=f"Google Drive index built successfully in {end_time - start_time:.2f} seconds",
            stats=index_stats,
            index_path=request.save_path
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive indexing failed: {str(e)}")

@router.post("/hybrid", response_model=IndexResponse)
async def build_hybrid_index_endpoint(request: HybridIndexRequest):
    """
    Build a hybrid index combining local files and Google Drive
    """
    try:
        start_time = time.time()
        
        # Build hybrid index
        stats = smart_semantic_index(
            directory_path=request.directory,
            gdrive_folder_id=request.gdrive_folder_id,
            gdrive_query=request.gdrive_query,
            persist_directory=request.db_path or settings.DEFAULT_CHROMA_DB_PATH,
            model_name=request.model,
            force_full=request.force_full
        )
        
        if not stats:
            raise HTTPException(status_code=500, detail="Failed to build hybrid index")
        
        stats_data = stats.get('stats', {})
        end_time = time.time()
        
        # Create response
        index_stats = IndexStats(
            indexing_type="hybrid",
            total_files=stats_data.get('total_files', 0),
            new_files=stats_data.get('new_files', 0),
            modified_files=stats_data.get('modified_files', 0),
            deleted_files=stats_data.get('deleted_files', 0),
            skipped_files=stats_data.get('skipped_files', 0),
            total_chunks=stats_data.get('total_chunks', 0),
            db_path=request.db_path or settings.DEFAULT_CHROMA_DB_PATH
        )
        
        return IndexResponse(
            success=True,
            message=f"Hybrid index built successfully in {end_time - start_time:.2f} seconds",
            stats=index_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid indexing failed: {str(e)}")

@router.post("/build/background", response_model=APIResponse)
async def build_index_background(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a background indexing task
    """
    task_id = str(uuid.uuid4())
    
    # Create task status in SQLite
    task_storage.set_task(
        task_id=task_id,
        status="pending",
        message="Task created"
    )
    
    # Add background task
    background_tasks.add_task(
        run_indexing_task,
        task_id,
        request
    )
    
    return APIResponse(
        success=True,
        message="Background indexing task started",
        data={
            "task_id": task_id,
            "status_endpoint": f"/api/v1/indexer/task/{task_id}"
        }
    )

@router.get("/task/{task_id}", response_model=APIResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a background indexing task
    """
    task_data = task_storage.get_task(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return APIResponse(
        success=True,
        message="Task status retrieved",
        data=task_data
    )

@router.delete("/tasks/cleanup", response_model=APIResponse)
async def cleanup_old_tasks(days_old: int = 7):
    """
    Clean up old completed/failed tasks
    """
    try:
        task_storage.cleanup_old_tasks(days_old)
        return APIResponse(
            success=True,
            message=f"Cleaned up tasks older than {days_old} days"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

async def run_indexing_task(task_id: str, request: IndexRequest):
    """
    Run indexing task in background
    """
    try:
        # Update task status to running
        task_storage.set_task(
            task_id=task_id,
            status="running",
            message="Indexing started"
        )
        
        # Run indexing (simplified for background task)
        # In a real implementation, you'd want to track progress
        if request.index_type.value == "semantic":
            stats = smart_semantic_index(
                directory_path=request.directory,
                persist_directory=request.db_path or settings.DEFAULT_CHROMA_DB_PATH,
                model_name=request.model,
                force_full=request.force_full
            )
        else:
            index_path = request.save_path or get_default_index_path(request.directory)
            stats = smart_index(
                directory_path=request.directory,
                index_path=index_path,
                force_full=request.force_full
            )
        
        # Update task status to completed
        task_storage.set_task(
            task_id=task_id,
            status="completed",
            message="Indexing completed successfully",
            result=stats
        )
        
    except Exception as e:
        # Update task status with error
        task_storage.set_task(
            task_id=task_id,
            status="failed",
            message="Indexing failed",
            error=str(e)
        ) 