"""
Google Drive router for Google Drive specific operations
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

# Import core functionality
from pkg.utils.google_drive import setup_google_drive_credentials, GOOGLE_DRIVE_AVAILABLE
from pkg.indexer.google_drive import build_google_drive_index, search_google_drive

from api.models import APIResponse, GoogleDriveIndexRequest

router = APIRouter()

@router.post("/setup", response_model=APIResponse)
async def setup_gdrive_endpoint(credentials_path: str):
    """
    Setup Google Drive credentials
    """
    try:
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=400, detail="Google Drive integration not available")
        
        success = setup_google_drive_credentials(credentials_path)
        
        if success:
            return APIResponse(
                success=True,
                message="Google Drive credentials configured successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to setup Google Drive credentials")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive setup failed: {str(e)}")

@router.get("/status", response_model=APIResponse)
async def gdrive_status():
    """
    Check Google Drive integration status
    """
    return APIResponse(
        success=True,
        message="Google Drive status",
        data={
            "available": GOOGLE_DRIVE_AVAILABLE,
            "configured": GOOGLE_DRIVE_AVAILABLE  # This would need to be checked in a real implementation
        }
    )

@router.post("/index", response_model=APIResponse)
async def index_gdrive_endpoint(request: GoogleDriveIndexRequest):
    """
    Index Google Drive files
    """
    try:
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=400, detail="Google Drive integration not available")
        
        # Build Google Drive index
        index_data = build_google_drive_index(
            folder_id=request.folder_id,
            query=request.query
        )
        
        if not index_data:
            raise HTTPException(status_code=500, detail="Failed to build Google Drive index")
        
        return APIResponse(
            success=True,
            message="Google Drive index built successfully",
            data={
                "files_indexed": len(index_data.get('documents', [])),
                "save_path": request.save_path
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive indexing failed: {str(e)}")

@router.get("/search", response_model=APIResponse)
async def search_gdrive_endpoint(
    query: str,
    folder_id: Optional[str] = None,
    limit: int = 10
):
    """
    Search Google Drive files
    """
    try:
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=400, detail="Google Drive integration not available")
        
        # Search Google Drive
        results = search_google_drive(
            query=query,
            folder_id=folder_id,
            limit=limit
        )
        
        return APIResponse(
            success=True,
            message="Google Drive search completed",
            data={
                "query": query,
                "results": results,
                "total_results": len(results)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive search failed: {str(e)}") 