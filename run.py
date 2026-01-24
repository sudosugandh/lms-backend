#!/usr/bin/env python3
"""
Simple script to run the FastAPI application using uvicorn.
Usage: 
    python3 run.py
    python3 run.py --host 127.0.0.1 --port 8000
    python3 run.py --no-reload  # Disable auto-reload
"""

import uvicorn
import sys
import os
import argparse

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI LMS backend server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on code changes")
    parser.add_argument("--log-level", type=str, default="info", choices=["critical", "error", "warning", "info", "debug", "trace"], help="Log level (default: info)")
    
    args = parser.parse_args()
    
    # Run the FastAPI app using uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,  # Enable auto-reload unless --no-reload is specified
        log_level=args.log_level
    )

