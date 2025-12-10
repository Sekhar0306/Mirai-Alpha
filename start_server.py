#!/usr/bin/env python3
"""
Start the API server
"""
import uvicorn
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("="*60)
    print("Factsheet Extraction System")
    print("="*60)
    print("Starting server...")
    print("API docs: http://localhost:8000/docs")
    print("Web UI: Open frontend/index.html")
    print("="*60)
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

