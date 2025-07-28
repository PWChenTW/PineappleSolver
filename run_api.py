#!/usr/bin/env python3
"""
Script to run the OFC Solver API server.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the API server."""
    # Server configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    workers = int(os.getenv("API_WORKERS", "1"))
    
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║        OFC Solver API Server              ║
    ╚═══════════════════════════════════════════╝
    
    Starting API server...
    - Host: {host}
    - Port: {port}
    - Reload: {reload}
    - Workers: {workers}
    
    Documentation will be available at:
    - Swagger UI: http://localhost:{port}/docs
    - ReDoc: http://localhost:{port}/redoc
    - OpenAPI JSON: http://localhost:{port}/openapi.json
    
    Health check: http://localhost:{port}/api/v1/health
    """)
    
    # Run server
    if reload:
        # Development mode with auto-reload
        uvicorn.run(
            "src.api.app:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    else:
        # Production mode
        uvicorn.run(
            "src.api.app:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info"
        )

if __name__ == "__main__":
    main()