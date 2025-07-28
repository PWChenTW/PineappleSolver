"""
FastAPI application with Prometheus monitoring integration.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import redis
from contextlib import asynccontextmanager

from .models import SolveRequest, SolveResponse, HealthResponse
from .endpoints import router
from .middleware import (
    APIConfig,
    AuthenticationMiddleware,
    RateLimiter,
    AsyncTaskManager
)
from .middleware_prometheus import (
    PrometheusMiddleware,
    EnhancedRequestTrackingMiddleware,
    MetricsAsyncTaskManager
)
from ..ofc_solver_prometheus import create_prometheus_solver


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    app.state.redis = redis.Redis(
        host=app.state.config.redis_host,
        port=app.state.config.redis_port,
        decode_responses=True
    )
    
    # Initialize components with metrics
    app.state.auth = AuthenticationMiddleware(app.state.config)
    app.state.rate_limiter = RateLimiter(app.state.redis, app.state.config)
    
    # Wrap AsyncTaskManager with metrics
    base_task_manager = AsyncTaskManager(app.state.redis, app.state.config)
    app.state.task_manager = MetricsAsyncTaskManager(base_task_manager)
    
    # Create solver with Prometheus metrics
    app.state.solver = create_prometheus_solver(
        threads=app.state.config.solver_threads,
        time_limit=app.state.config.solver_time_limit
    )
    
    yield
    
    # Shutdown
    app.state.redis.close()


# Create FastAPI app
def create_app(config: APIConfig) -> FastAPI:
    """Create FastAPI application with Prometheus monitoring."""
    
    app = FastAPI(
        title="OFC Solver API",
        description="Open Face Chinese Poker Solver with Prometheus Monitoring",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Store config
    app.state.config = config
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Prometheus middleware (must be added first to catch all requests)
    app.add_middleware(PrometheusMiddleware)
    
    # Add enhanced request tracking with system metrics
    app.add_middleware(EnhancedRequestTrackingMiddleware)
    
    # Add request validation
    from .middleware import RequestValidationMiddleware
    app.add_middleware(RequestValidationMiddleware, config=config)
    
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Include API routes
    app.include_router(router)
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["monitoring"])
    async def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Check Redis connection
            app.state.redis.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
        
        return HealthResponse(
            status="healthy" if redis_status == "healthy" else "degraded",
            version="1.0.0",
            components={
                "api": "healthy",
                "redis": redis_status,
                "solver": "healthy"
            }
        )
    
    return app


# Example configuration
def get_default_config() -> APIConfig:
    """Get default API configuration."""
    import os
    
    return APIConfig(
        api_keys={
            # SHA256 hash of "demo-api-key"
            "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8": {
                "name": "Demo Key",
                "active": True,
                "rate_limit": 1000,
                "permissions": ["solve", "async_solve"],
                "owner": "demo"
            }
        },
        default_rate_limit=100,
        rate_limit_window=3600,
        max_request_size=10 * 1024 * 1024,
        request_timeout=300,
        enable_async_processing=True,
        max_async_queue_size=1000,
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", 6379)),
        solver_threads=int(os.getenv("SOLVER_THREADS", 4)),
        solver_time_limit=float(os.getenv("SOLVER_TIME_LIMIT", 30.0))
    )


# Create app instance
if __name__ == "__main__":
    import uvicorn
    
    config = get_default_config()
    app = create_app(config)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )