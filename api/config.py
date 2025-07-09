"""
Configuration settings for the Desktop Search API
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")  # 0.0.0.0 = all interfaces, "127.0.0.1" = localhost only
    PORT: int = int(os.getenv("PORT", "8443"))  # Default to 8443 for static port
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        "https://localhost",      # HTTPS localhost (any port)
        "http://localhost",       # HTTP localhost (any port)
        "https://127.0.0.1",     # HTTPS 127.0.0.1 (any port)
        "http://127.0.0.1",      # HTTP 127.0.0.1 (any port)
        "https://localhost:8443", # HTTPS localhost with specific port
        "http://localhost:8443",  # HTTP localhost with specific port
        "https://127.0.0.1:8443", # HTTPS 127.0.0.1 with specific port
        "http://127.0.0.1:8443", # HTTP 127.0.0.1 with specific port
    ]
    
    # Production CORS settings (set via environment variable)
    PRODUCTION_ORIGINS: List[str] = [
        # Add your production domains here
        # "https://yourdomain.com",
        # "https://app.yourdomain.com",
    ]
    
    # Default paths - use only one index.pkl and one metadata file
    DEFAULT_DATA_PATH: str = os.getenv("DATA_PATH", "./data")
    DEFAULT_INDEX_PATH: str = os.path.join(DEFAULT_DATA_PATH, "index.pkl")
    DEFAULT_METADATA_PATH: str = os.path.join(DEFAULT_DATA_PATH, "index_metadata.json")
    DEFAULT_CHROMA_DB_PATH: str = os.path.join(DEFAULT_DATA_PATH, "chroma_db")
    
    # Search settings
    DEFAULT_SEARCH_LIMIT: int = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
    DEFAULT_SIMILARITY_THRESHOLD: float = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.3"))
    
    # Model settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "all-MiniLM-L6-v2")
    
    # File size limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Background task settings
    MAX_BACKGROUND_TASKS: int = int(os.getenv("MAX_BACKGROUND_TASKS", "5"))
    
    # Security settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    API_KEY: str = os.getenv("API_KEY", "")
    
    # SSL/HTTPS settings
    SSL_ENABLED: bool = os.getenv("SSL_ENABLED", "False").lower() == "true"
    SSL_KEY_FILE: str = os.getenv("SSL_KEY_FILE", "./certs/key.pem")
    SSL_CERT_FILE: str = os.getenv("SSL_CERT_FILE", "./certs/cert.pem")
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

settings = Settings() 