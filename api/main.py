"""
FastAPI application for Desktop Search API
Provides REST endpoints for indexing and searching documents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.routers import indexer, searcher, google_drive, stats
from api.models import APIResponse, ErrorResponse
from api.config import settings

# Create FastAPI app
app = FastAPI(
    title="Desktop Search API",
    description="A REST API for indexing and searching local documents with semantic search capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(indexer.router, prefix="/api/v1/indexer", tags=["Indexer"])
app.include_router(searcher.router, prefix="/api/v1/searcher", tags=["Searcher"])
app.include_router(google_drive.router, prefix="/api/v1/gdrive", tags=["Google Drive"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistics"])

# Health check endpoint
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        message="Desktop Search API is running",
        data={"status": "healthy"}
    )

# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        message="Desktop Search API",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return ErrorResponse(
        success=False,
        message="Internal server error",
        error=str(exc)
    )

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 