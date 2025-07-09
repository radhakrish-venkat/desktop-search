"""
Directory management router for handling multiple indexed directories
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import os
import json
import time
from datetime import datetime
import re

from api.models import (
    DirectoryInfo, DirectoryList, DirectoryStatus, APIResponse
)
from api.config import settings
from pkg.indexer.incremental import smart_semantic_index

def validate_directory_path(path: str) -> str:
    """Validate and sanitize directory path"""
    # Remove any path traversal attempts
    path = os.path.normpath(path)
    
    # Check for suspicious patterns - allow absolute paths but prevent traversal
    if re.search(r'\.\.', path) or '~' in path:
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    # Ensure path exists and is a directory
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    return path

router = APIRouter()

# Directory metadata storage
DIRECTORIES_FILE = os.path.join(settings.DEFAULT_DATA_PATH, "directories.json")

def load_directories() -> List[DirectoryInfo]:
    """Load directory list from file"""
    if not os.path.exists(DIRECTORIES_FILE):
        return []
    
    try:
        with open(DIRECTORIES_FILE, 'r') as f:
            data = json.load(f)
            return [DirectoryInfo(**dir_data) for dir_data in data.get('directories', [])]
    except Exception as e:
        print(f"Error loading directories: {e}")
        return []

def save_directories(directories: List[DirectoryInfo]):
    """Save directory list to file"""
    os.makedirs(os.path.dirname(DIRECTORIES_FILE), exist_ok=True)
    try:
        with open(DIRECTORIES_FILE, 'w') as f:
            json.dump({
                'directories': [dir_info.model_dump() for dir_info in directories],
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving directories: {e}")

def update_directory_status(path: str, status: str, progress: float = 0.0, 
                           message: str = "", task_id: Optional[str] = None,
                           total_files: int = 0, indexed_files: int = 0):
    """Update status of a specific directory"""
    directories = load_directories()
    
    for dir_info in directories:
        if dir_info.path == path:
            dir_info.status = status
            dir_info.progress = progress
            dir_info.task_id = task_id
            dir_info.total_files = total_files
            dir_info.indexed_files = indexed_files
            if status == "indexed":
                dir_info.last_indexed = datetime.now().isoformat()
            break
    
    save_directories(directories)

@router.get("/list", response_model=DirectoryList)
async def list_directories():
    """Get list of all indexed directories"""
    directories = load_directories()
    return DirectoryList(directories=directories)

@router.post("/add", response_model=APIResponse)
async def add_directory(path: str):
    """Add a new directory to the index"""
    # Validate and sanitize path
    path = validate_directory_path(path)
    
    directories = load_directories()
    
    # Check if directory already exists
    for dir_info in directories:
        if dir_info.path == path:
            raise HTTPException(status_code=400, detail=f"Directory already exists: {path}")
    
    # Add new directory
    new_dir = DirectoryInfo(
        path=path,
        name=os.path.basename(path),
        status="not_indexed"
    )
    directories.append(new_dir)
    save_directories(directories)
    
    return APIResponse(
        success=True,
        message=f"Directory added: {path}",
        data={"directory": new_dir.model_dump()}
    )

@router.post("/refresh/{path:path}", response_model=APIResponse)
async def refresh_directory(path: str, background_tasks: BackgroundTasks):
    """Refresh/rebuild index for a specific directory"""
    directories = load_directories()
    
    # Find the directory
    dir_info = None
    for d in directories:
        if d.path == path:
            dir_info = d
            break
    
    if not dir_info:
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    
    if dir_info.status == "indexing":
        raise HTTPException(status_code=400, detail="Directory is already being indexed")
    
    # Generate task ID
    task_id = f"dir_{int(time.time())}_{os.path.basename(path)}"
    
    # Update status to indexing
    update_directory_status(path, "indexing", 0.0, "Starting indexing...", task_id)
    
    # Add background task
    background_tasks.add_task(
        index_directory_task,
        path,
        task_id
    )
    
    return APIResponse(
        success=True,
        message=f"Indexing started for: {path}",
        data={"task_id": task_id}
    )

@router.get("/status/{path:path}", response_model=DirectoryStatus)
async def get_directory_status(path: str):
    """Get indexing status for a specific directory"""
    directories = load_directories()
    
    for dir_info in directories:
        if dir_info.path == path:
            return DirectoryStatus(
                path=dir_info.path,
                status=dir_info.status,
                progress=dir_info.progress,
                task_id=dir_info.task_id,
                total_files=dir_info.total_files,
                indexed_files=dir_info.indexed_files
            )
    
    raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

@router.delete("/remove/{path:path}", response_model=APIResponse)
async def remove_directory(path: str):
    """Remove a directory from the index"""
    directories = load_directories()
    
    # Find and remove the directory
    for i, dir_info in enumerate(directories):
        if dir_info.path == path:
            if dir_info.status == "indexing":
                raise HTTPException(status_code=400, detail="Cannot remove directory while indexing")
            
            removed_dir = directories.pop(i)
            save_directories(directories)
            
            return APIResponse(
                success=True,
                message=f"Directory removed: {path}",
                data={"directory": removed_dir.model_dump()}
            )
    
    raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

async def index_directory_task(path: str, task_id: str):
    """Background task to index a directory with real-time progress updates"""
    def progress_callback(indexed_files, total_files, filepath):
        update_directory_status(path, "indexing", (indexed_files / total_files) if total_files else 0.0, f"Indexing: {filepath}", task_id, total_files, indexed_files)
    try:
        # Update progress
        update_directory_status(path, "indexing", 0.1, "Initializing...", task_id)
        # Perform indexing with progress callback
        from pkg.indexer.incremental import smart_semantic_index
        stats = smart_semantic_index(
            directory_path=path,
            persist_directory=settings.DEFAULT_CHROMA_DB_PATH,
            model_name="all-MiniLM-L6-v2",
            force_full=True,
            progress_callback=progress_callback
        )
        if stats:
            stats_data = stats.get('stats', {})
            update_directory_status(
                path, "indexed", 1.0, "Indexing completed",
                task_id, stats_data.get('total_files', 0), stats_data.get('total_files', 0)
            )
        else:
            update_directory_status(path, "error", 0.0, "Indexing failed", task_id)
    except Exception as e:
        update_directory_status(path, "error", 0.0, f"Error: {str(e)}", task_id) 