#!/usr/bin/env python3
"""
Startup script for the Desktop Search FastAPI application
"""

import uvicorn
import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize application before starting
try:
    from pkg.utils.initialization import initialize_app
    from pkg.utils.llm_initialization import initialize_llm_system
    
    print("🚀 Starting Desktop Search API...")
    if not initialize_app(project_root):
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

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8443,
        reload=True,
        log_level="info"
    ) 