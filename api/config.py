"""
Configuration settings for the Desktop Search API
"""

import os
from typing import List

class Settings:
    """Application settings"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ]
    
    # Default paths
    DEFAULT_CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    DEFAULT_INDEX_PATH: str = os.getenv("INDEX_PATH", "./chroma_db/index.pkl")
    DEFAULT_METADATA_PATH: str = os.getenv("METADATA_PATH", "./chroma_db/index_metadata.json")
    
    # Search settings
    DEFAULT_SEARCH_LIMIT: int = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
    DEFAULT_SIMILARITY_THRESHOLD: float = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.3"))
    
    # Model settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "all-MiniLM-L6-v2")
    
    # File size limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Background task settings
    MAX_BACKGROUND_TASKS: int = int(os.getenv("MAX_BACKGROUND_TASKS", "5"))

settings = Settings() 