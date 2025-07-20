"""
FastAPI application for Desktop Search API
Provides REST endpoints for indexing and searching documents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.routers import indexer, searcher, google_drive, stats, directories, auth, llm_search, enhanced_search_router
from api.models import APIResponse, ErrorResponse
from api.config import settings
from api.middleware.security import SecurityMiddleware
from api.middleware.rate_limit import rate_limit_middleware

# Initialize application on startup
try:
    from pkg.utils.initialization import initialize_app
    print("🚀 Starting Desktop Search API...")
    if not initialize_app(project_root):
        print("❌ Application initialization failed!")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="Desktop Search API",
    description="A REST API for indexing and searching local documents with semantic search capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup custom Swagger documentation
from api.swagger_docs import setup_swagger_docs
setup_swagger_docs(app)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.ALLOWED_ORIGINS + (settings.PRODUCTION_ORIGINS if not settings.DEBUG else []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit(request, call_next):
    return await rate_limit_middleware(request, call_next)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(indexer.router, prefix="/api/v1/indexer", tags=["indexer"])
app.include_router(searcher.router, prefix="/api/v1/searcher", tags=["searcher"])
app.include_router(google_drive.router, prefix="/api/v1/gdrive", tags=["google_drive"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(directories.router, prefix="/api/v1/directories", tags=["directories"])
app.include_router(llm_search.router, prefix="/api/v1/llm", tags=["llm_search"])
app.include_router(enhanced_search_router.router, prefix="/api/v1/enhanced-search", tags=["enhanced-search"])

# Mount static files for frontend (after API routes)
frontend_path = os.path.join(project_root, "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Root redirect to frontend
@app.get("/")
async def root_redirect():
    """Redirect root to frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/")

# Health check endpoint
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        message="Desktop Search API is running",
        data={"status": "healthy"}
    )



# API info endpoint (since root serves frontend)
@app.get("/api/info", response_model=APIResponse)
async def api_info():
    """API information endpoint"""
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
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    # Check if SSL is enabled
    if settings.SSL_ENABLED:
        # Verify SSL certificates exist
        import os.path
        if not os.path.exists(settings.SSL_KEY_FILE) or not os.path.exists(settings.SSL_CERT_FILE):
            print("❌ SSL certificates not found!")
            print(f"   Key file: {settings.SSL_KEY_FILE}")
            print(f"   Cert file: {settings.SSL_CERT_FILE}")
            print("   Run: python generate_certs.py")
            sys.exit(1)
        
        print("🔐 Starting server with HTTPS...")
        uvicorn.run(
            "api.main:app",
            host=settings.HOST,
            port=settings.HTTPS_PORT,
            reload=settings.DEBUG,
            log_level="info",
            ssl_keyfile=settings.SSL_KEY_FILE,
            ssl_certfile=settings.SSL_CERT_FILE
        )
    else:
        print("🌐 Starting server with HTTP...")
        uvicorn.run(
            "api.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info"
        ) 