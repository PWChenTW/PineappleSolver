"""
FastAPI application for OFC Solver API.

This module sets up the FastAPI application with all middleware,
routes, and configurations.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .middleware import (
    APIConfig,
    RequestTrackingMiddleware,
    RequestValidationMiddleware,
    AuthenticationMiddleware,
    RateLimiter
)
from .routes import router
from .models import ErrorResponse, ErrorDetail
from .cache import get_cache_client, SimpleTaskQueue


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Load configuration
def load_config() -> APIConfig:
    """Load API configuration from environment or config file."""
    # In production, load from secure configuration
    return APIConfig(
        api_keys={
            # Example API keys (hashed)
            "sha256_hash_of_test_key": {
                "owner": "test_user",
                "name": "Test API Key",
                "active": True,
                "rate_limit": 100,
                "permissions": {
                    "async_processing": True,
                    "batch_processing": True,
                    "admin": False
                },
                "limits": {
                    "max_batch_size": 50
                }
            }
        },
        default_rate_limit=100,
        rate_limit_window=3600,
        max_request_size=10 * 1024 * 1024,  # 10MB
        request_timeout=300,  # 5 minutes
        enable_async_processing=True,
        max_async_queue_size=1000
    )


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting OFC Solver API...")
    
    # Initialize cache client (memory-based for development)
    app.state.redis = get_cache_client()
    
    # Test cache connection
    try:
        app.state.redis.ping()
        logger.info("Cache connection established")
    except Exception as e:
        logger.error(f"Failed to connect to cache: {e}")
        raise
    
    # Initialize task queue
    app.state.task_queue = SimpleTaskQueue()
    
    # Load configuration
    app.state.config = load_config()
    
    # Initialize services
    app.state.auth = AuthenticationMiddleware(app.state.config)
    app.state.rate_limiter = RateLimiter(app.state.redis, app.state.config)
    app.state.start_time = datetime.utcnow()
    
    logger.info("OFC Solver API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OFC Solver API...")
    
    # Close cache connection
    app.state.redis.close()
    
    logger.info("OFC Solver API shut down complete")


# Create FastAPI application
app = FastAPI(
    title="OFC Solver API",
    description="RESTful API for Open Face Chinese poker solver",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestTrackingMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    # Get request ID
    request_id = "unknown"
    if hasattr(request.state, "context"):
        request_id = str(request.state.context.request_id)
    
    # Log error
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Return error response
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"request_id": request_id}
        ),
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


# Include routes
app.include_router(router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": "OFC Solver API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


# Custom OpenAPI schema
def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Add custom headers
    if "paths" in openapi_schema:
        for path in openapi_schema["paths"].values():
            for operation in path.values():
                if isinstance(operation, dict):
                    # Add common parameters
                    if "parameters" not in operation:
                        operation["parameters"] = []
                    
                    # Add request ID header
                    operation["parameters"].append({
                        "name": "X-Request-ID",
                        "in": "header",
                        "description": "Optional client-provided request ID",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "format": "uuid"
                        }
                    })
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Development server
if __name__ == "__main__":
    # Development configuration
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )