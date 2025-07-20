#!/usr/bin/env python3
"""
Start the Desktop Search API with HTTPS support on a static port
"""

import os
import sys
from pathlib import Path
import uvicorn
from api.config import settings

def check_certificates():
    """Check if SSL certificates exist"""
    certs_dir = Path("certs")
    key_file = certs_dir / "key.pem"
    cert_file = certs_dir / "cert.pem"
    
    if not key_file.exists() or not cert_file.exists():
        print("❌ SSL certificates not found!")
        print("   Run: python generate_certs.py")
        return None, None
    
    return str(key_file), str(cert_file)

def main():
    """Start the API server with HTTPS on a static port"""
    
    print("🔐 Starting Desktop Search API with HTTPS...")
    
    # Initialize application before starting
    try:
        from pkg.utils.initialization import initialize_app
        from pkg.utils.llm_initialization import initialize_llm_system
        
        if not initialize_app():
            print("❌ Application initialization failed!")
            sys.exit(1)
        
        # Initialize LLM system
        print("🤖 Initializing LLM system...")
        llm_results = initialize_llm_system()
        if llm_results.get("errors"):
            print("⚠️  LLM initialization warnings:")
            for error in llm_results["errors"]:
                print(f"   - {error}")
            print("💡 LLM features may not be available")
        else:
            print("✅ LLM system initialized successfully!")
            
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        sys.exit(1)
    
    # Check for certificates
    key_file, cert_file = check_certificates()
    if not key_file or not cert_file:
        sys.exit(1)
    
    # Use HTTPS port from settings (default 8443)
    port = settings.HTTPS_PORT
    
    # SSL configuration
    ssl_config = {
        "ssl_keyfile": key_file,
        "ssl_certfile": cert_file
    }
    
    # Server configuration
    server_config = {
        "app": "api.main:app",
        "host": settings.HOST,
        "port": port,
        "reload": settings.DEBUG,
        "log_level": "info" if not settings.DEBUG else "debug",
        "access_log": True,
        "use_colors": True,
        **ssl_config
    }
    
    print(f"🌐 Server will be available at: https://localhost:{port}")
    print(f"📚 API Documentation: https://localhost:{port}/docs")
    print(f"🔧 Debug mode: {'Enabled' if settings.DEBUG else 'Disabled'}")
    print(f"🔐 SSL: Enabled (TLS 1.2+)")
    print("\n🚀 Starting server...")
    print("   Press Ctrl+C to stop")
    
    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 