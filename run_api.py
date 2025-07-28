#!/usr/bin/env python3
"""
Quick script to run the OFC Solver API server.
"""

import uvicorn
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Run the API server."""
    print("Starting OFC Solver API server...")
    print("=" * 60)
    print("API will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Alternative docs: http://localhost:8000/redoc")
    print("=" * 60)
    
    # Run server
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()