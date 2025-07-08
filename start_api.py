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

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 