#!/usr/bin/env python3
"""
Simple test script for the FastAPI application
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import fastapi
        print("✓ FastAPI imported successfully")
        
        import uvicorn
        print("✓ Uvicorn imported successfully")
        
        # Test API imports
        import api.config
        print("✓ API config imported successfully")
        
        import api.models
        print("✓ API models imported successfully")
        
        # Test router imports
        import api.routers.indexer
        print("✓ Indexer router imported successfully")
        
        import api.routers.searcher
        print("✓ Searcher router imported successfully")
        
        import api.routers.google_drive
        print("✓ Google Drive router imported successfully")
        
        import api.routers.stats
        print("✓ Stats router imported successfully")
        
        # Test main app
        import api.main
        print("✓ Main app imported successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test if the FastAPI app can be created"""
    try:
        print("\nTesting app creation...")
        
        from api.main import app
        print("✓ FastAPI app created successfully")
        
        # Check if routes are registered
        routes = [route.path for route in app.routes]
        print(f"✓ Found {len(routes)} routes")
        
        # Check for key endpoints
        key_endpoints = ['/health', '/docs', '/api/v1/indexer', '/api/v1/searcher']
        for endpoint in key_endpoints:
            if any(endpoint in route for route in routes):
                print(f"✓ Found endpoint: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

if __name__ == "__main__":
    print("Desktop Search API Test")
    print("=" * 30)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test app creation
        app_ok = test_app_creation()
        
        if app_ok:
            print("\n🎉 API setup is working correctly!")
            print("\nTo start the server, run:")
            print("  python start_api.py")
            print("\nOr:")
            print("  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
        else:
            print("\n❌ App creation failed")
    else:
        print("\n❌ Import test failed") 