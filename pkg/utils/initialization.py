"""
Initialization utilities for the Desktop Search application
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AppInitializer:
    """Handles application initialization and setup"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.certs_dir = self.project_root / "certs"
        self.data_dir = self.project_root / "data"
        self.chroma_db_dir = self.data_dir / "chroma_db"
        
    def reinitialize_all(self) -> bool:
        """Reinitialize everything from scratch - removes existing data and recreates"""
        print("🔄 Reinitializing Desktop Search Application from scratch...")
        
        try:
            # Remove existing components
            if not self._remove_existing_components():
                return False
                
            # Initialize all components fresh
            if not self.initialize_all():
                return False
                
            print("✅ Application reinitialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Reinitialization failed: {e}")
            logger.error(f"Reinitialization failed: {e}")
            return False
    
    def _remove_existing_components(self) -> bool:
        """Remove existing certificates, database, and configuration"""
        print("🗑️  Removing existing components...")
        
        try:
            # Remove certificates
            if self.certs_dir.exists():
                import shutil
                shutil.rmtree(self.certs_dir)
                print("   ✅ Removed existing certificates")
            
            # Remove database
            if self.chroma_db_dir.exists():
                import shutil
                shutil.rmtree(self.chroma_db_dir)
                print("   ✅ Removed existing database")
            
            # Remove directories.json
            directories_file = self.data_dir / "directories.json"
            if directories_file.exists():
                directories_file.unlink()
                print("   ✅ Removed existing directories configuration")
            
            # Remove index metadata
            metadata_file = self.data_dir / "index_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
                print("   ✅ Removed existing index metadata")
            
            # Remove index.pkl if exists
            index_file = self.data_dir / "index.pkl"
            if index_file.exists():
                index_file.unlink()
                print("   ✅ Removed existing index file")
            
            print("✅ All existing components removed")
            return True
            
        except Exception as e:
            print(f"❌ Error removing existing components: {e}")
            return False
        
    def initialize_all(self) -> bool:
        """Initialize all application components"""
        print("🚀 Initializing Desktop Search Application...")
        
        try:
            # Check and create certificates
            if not self._check_and_create_certs():
                return False
                
            # Check and create database
            if not self._check_and_create_database():
                return False
                
            # Check and create API keys
            if not self._check_and_create_api_keys():
                return False
                
            # Check and create directories.json
            if not self._check_and_create_directories():
                return False
                
            print("✅ Application initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            logger.error(f"Initialization failed: {e}")
            return False
    
    def _check_and_create_certs(self) -> bool:
        """Check if SSL certificates exist, create if missing"""
        print("🔐 Checking SSL certificates...")
        
        key_file = self.certs_dir / "key.pem"
        cert_file = self.certs_dir / "cert.pem"
        
        if key_file.exists() and cert_file.exists():
            print("✅ SSL certificates found")
            return True
        
        print("📝 SSL certificates not found, generating...")
        
        # Create certs directory
        self.certs_dir.mkdir(exist_ok=True)
        
        # Check if OpenSSL is available
        try:
            subprocess.run(["openssl", "version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ OpenSSL not found. Please install OpenSSL first:")
            print("   Ubuntu/Debian: sudo apt-get install openssl")
            print("   macOS: brew install openssl")
            print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
            return False
        
        try:
            # Generate private key
            print("📝 Generating private key...")
            subprocess.run([
                "openssl", "genrsa", "-out", str(key_file), "2048"
            ], check=True, capture_output=True)
            
            # Generate certificate
            print("📜 Generating certificate...")
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(key_file),
                "-out", str(cert_file), "-days", "365", "-subj",
                "/C=US/ST=State/L=City/O=Organization/CN=localhost"
            ], check=True, capture_output=True)
            
            # Set proper permissions
            os.chmod(key_file, 0o600)
            os.chmod(cert_file, 0o644)
            
            print("✅ SSL certificates generated successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating certificates: {e}")
            return False
    
    def _check_and_create_database(self) -> bool:
        """Check if ChromaDB exists, create if missing"""
        print("🗄️  Checking database...")
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Create chroma_db directory if it doesn't exist
        self.chroma_db_dir.mkdir(exist_ok=True)
        
        # Check if ChromaDB has been initialized (look for some files)
        db_files = list(self.chroma_db_dir.glob("*"))
        if db_files:
            print("✅ Database found")
            return True
        
        print("📊 Database not found, will be created on first indexing")
        return True
    
    def _check_and_create_api_keys(self) -> bool:
        """Check if API keys are configured"""
        print("🔑 Checking API keys...")
        
        # Check for required API keys in environment
        api_key = os.getenv("API_KEY", "")
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        
        if not api_key:
            print("⚠️  API_KEY not set in environment")
            print("   Set it with: export API_KEY=your_api_key_here")
            print("   Or create a .env file with: API_KEY=your_api_key_here")
        
        if not jwt_secret:
            print("⚠️  JWT_SECRET_KEY not set in environment")
            print("   Set it with: export JWT_SECRET_KEY=your_jwt_secret_here")
            print("   Or create a .env file with: JWT_SECRET_KEY=your_jwt_secret_here")
        
        # For development, we can continue without API keys
        # In production, you might want to return False here
        print("✅ API key check completed (development mode)")
        return True
    
    def _check_and_create_directories(self) -> bool:
        """Check if directories.json exists, create if missing"""
        print("📁 Checking directories configuration...")
        
        directories_file = self.data_dir / "directories.json"
        
        if directories_file.exists():
            print("✅ Directories configuration found")
            return True
        
        print("📝 Creating default directories configuration...")
        
        default_directories = {
            "directories": [],
            "last_updated": None
        }
        
        try:
            with open(directories_file, 'w') as f:
                json.dump(default_directories, f, indent=2)
            print("✅ Directories configuration created")
            return True
        except Exception as e:
            print(f"❌ Error creating directories configuration: {e}")
            return False
    
    def check_environment(self) -> Dict[str, Any]:
        """Check the current environment and return status"""
        status = {
            "certs": {
                "key_exists": (self.certs_dir / "key.pem").exists(),
                "cert_exists": (self.certs_dir / "cert.pem").exists()
            },
            "database": {
                "data_dir_exists": self.data_dir.exists(),
                "chroma_db_exists": self.chroma_db_dir.exists(),
                "has_data": len(list(self.chroma_db_dir.glob("*"))) > 0
            },
            "api_keys": {
                "api_key_set": bool(os.getenv("API_KEY", "")),
                "jwt_secret_set": bool(os.getenv("JWT_SECRET_KEY", ""))
            },
            "directories": {
                "config_exists": (self.data_dir / "directories.json").exists()
            }
        }
        
        return status

def initialize_app(project_root: Optional[str] = None) -> bool:
    """Convenience function to initialize the application"""
    initializer = AppInitializer(project_root)
    return initializer.initialize_all()

def reinitialize_app(project_root: Optional[str] = None) -> bool:
    """Convenience function to reinitialize the application from scratch"""
    initializer = AppInitializer(project_root)
    return initializer.reinitialize_all()

def check_app_status(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Check the current status of the application"""
    initializer = AppInitializer(project_root)
    return initializer.check_environment() 