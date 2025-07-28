"""
API middleware components for authentication, rate limiting, and request tracking.
"""

import time
import hashlib
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps
from uuid import UUID, uuid4

from fastapi import Request, HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pydantic import BaseModel

from .models import RequestContext, RateLimitInfo, ErrorResponse, ErrorDetail


logger = logging.getLogger(__name__)


# Configuration
class APIConfig(BaseModel):
    """API configuration settings."""
    api_keys: Dict[str, Dict[str, Any]]  # API key -> {name, rate_limit, permissions}
    default_rate_limit: int = 100  # requests per hour
    rate_limit_window: int = 3600  # seconds
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 300  # 5 minutes
    enable_async_processing: bool = True
    max_async_queue_size: int = 1000


# Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticationMiddleware:
    """API key authentication middleware."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self._api_key_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def authenticate(
        self,
        api_key: Optional[str] = Depends(api_key_header)
    ) -> Dict[str, Any]:
        """Authenticate API request."""
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "MISSING_API_KEY",
                        "message": "API key is required"
                    }
                }
            )
        
        # Check cache first
        cached = self._get_cached_key_info(api_key)
        if cached:
            return cached
        
        # Validate API key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_info = self.config.api_keys.get(key_hash)
        
        if not key_info:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_API_KEY",
                        "message": "Invalid API key"
                    }
                }
            )
        
        # Check if key is active
        if not key_info.get("active", True):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INACTIVE_API_KEY",
                        "message": "API key is inactive"
                    }
                }
            )
        
        # Cache the result
        self._cache_key_info(api_key, key_info)
        return key_info
    
    def _get_cached_key_info(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API key info."""
        cached = self._api_key_cache.get(api_key)
        if cached and cached["expires"] > time.time():
            return cached["info"]
        return None
    
    def _cache_key_info(self, api_key: str, key_info: Dict[str, Any]):
        """Cache API key info."""
        self._api_key_cache[api_key] = {
            "info": key_info,
            "expires": time.time() + self._cache_ttl
        }


# Rate Limiting
class RateLimiter:
    """Redis-based rate limiter using sliding window."""
    
    def __init__(self, redis_client, config: APIConfig):
        self.redis = redis_client
        self.config = config
    
    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> RateLimitInfo:
        """Check rate limit for a key."""
        limit = limit or self.config.default_rate_limit
        window = window or self.config.rate_limit_window
        
        now = time.time()
        window_start = now - window
        
        # Redis key for rate limiting
        redis_key = f"rate_limit:{key}"
        
        # Remove old entries and count current ones
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zadd(redis_key, {str(uuid4()): now})
        pipe.zcount(redis_key, window_start, now)
        pipe.expire(redis_key, window)
        
        results = pipe.execute()
        request_count = results[2]
        
        # Calculate rate limit info
        remaining = max(0, limit - request_count)
        reset_time = int(now + window)
        
        # Check if limit exceeded
        if request_count > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded",
                        "details": {
                            "limit": limit,
                            "window": f"{window} seconds",
                            "retry_after": window
                        }
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(window)
                }
            )
        
        return RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset=reset_time
        )


# Request Tracking
class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking and logging."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with tracking."""
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        # Create request context
        context = RequestContext(
            request_id=UUID(request_id),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent"),
            timestamp=datetime.utcnow()
        )
        
        # Store context in request state
        request.state.context = context
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": context.client_ip
            }
        )
        
        # Track timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                },
                exc_info=True
            )
            raise


# Request Validation
class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation."""
    
    def __init__(self, app, config: APIConfig):
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next):
        """Validate request size and content."""
        # Check content length
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.config.max_request_size:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": "Request payload exceeds maximum size",
                        "details": {
                            "max_size": f"{self.config.max_request_size} bytes",
                            "actual_size": f"{content_length} bytes"
                        }
                    }
                }
            )
        
        return await call_next(request)


# Async Task Management
class AsyncTaskManager:
    """Manager for async task processing."""
    
    def __init__(self, redis_client, config: APIConfig):
        self.redis = redis_client
        self.config = config
        self.task_queue = "ofc_solver:tasks"
        self.task_status_prefix = "ofc_solver:task:"
    
    async def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: str = "normal"
    ) -> str:
        """Create a new async task."""
        task_id = str(uuid4())
        
        # Create task record
        task = {
            "id": task_id,
            "type": task_type,
            "data": task_data,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check queue size
        queue_size = self.redis.llen(self.task_queue)
        if queue_size >= self.config.max_async_queue_size:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "QUEUE_FULL",
                        "message": "Task queue is full, please try again later",
                        "details": {
                            "queue_size": queue_size,
                            "max_size": self.config.max_async_queue_size
                        }
                    }
                }
            )
        
        # Store task status
        self.redis.setex(
            f"{self.task_status_prefix}{task_id}",
            86400,  # 24 hours TTL
            json.dumps(task)
        )
        
        # Add to queue based on priority
        if priority == "high":
            self.redis.lpush(self.task_queue, task_id)
        else:
            self.redis.rpush(self.task_queue, task_id)
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        data = self.redis.get(f"{self.task_status_prefix}{task_id}")
        if data:
            return json.loads(data)
        return None
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        progress: Optional[int] = None
    ):
        """Update task status."""
        task = await self.get_task_status(task_id)
        if not task:
            return
        
        # Update task
        task["status"] = status
        task["updated_at"] = datetime.utcnow().isoformat()
        
        if result:
            task["result"] = result
        if error:
            task["error"] = error
        if progress is not None:
            task["progress"] = progress
        
        if status in ["completed", "failed"]:
            task["completed_at"] = datetime.utcnow().isoformat()
        
        # Store updated task
        self.redis.setex(
            f"{self.task_status_prefix}{task_id}",
            86400,  # 24 hours TTL
            json.dumps(task)
        )


# Error Handling
def error_handler(status_code: int, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
    """Create standardized error response."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get request ID from context if available
                request_id = str(uuid4())
                request = kwargs.get("request")
                if request and hasattr(request.state, "context"):
                    request_id = str(request.state.context.request_id)
                
                # Log error
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "function": func.__name__,
                        "error": str(e)
                    },
                    exc_info=True
                )
                
                # Create error response
                error_response = ErrorResponse(
                    error=ErrorDetail(
                        code=error_code,
                        message=message,
                        details=details or {"original_error": str(e)}
                    ),
                    request_id=UUID(request_id),
                    timestamp=datetime.utcnow()
                )
                
                raise HTTPException(
                    status_code=status_code,
                    detail=error_response.dict()
                )
        
        return wrapper
    return decorator


# Dependencies
async def get_request_context(request: Request) -> RequestContext:
    """Get request context from request state."""
    if not hasattr(request.state, "context"):
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "MISSING_CONTEXT",
                    "message": "Request context not found"
                }
            }
        )
    return request.state.context


async def get_rate_limit_key(
    request: Request,
    auth_info: Dict[str, Any] = Depends(AuthenticationMiddleware.authenticate)
) -> str:
    """Get rate limit key for request."""
    # Use API key owner as rate limit key
    return auth_info.get("owner", "unknown")


# Monitoring
class MetricsCollector:
    """Collect API metrics for monitoring."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.metrics_prefix = "ofc_solver:metrics:"
    
    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        api_key_owner: Optional[str] = None
    ):
        """Record request metrics."""
        timestamp = int(time.time())
        hour_bucket = timestamp - (timestamp % 3600)
        
        # Metrics to record
        metrics = [
            (f"requests:total:{hour_bucket}", 1),
            (f"requests:{endpoint}:{method}:{hour_bucket}", 1),
            (f"requests:status:{status_code}:{hour_bucket}", 1),
            (f"duration:{endpoint}:{method}:{hour_bucket}", duration_ms)
        ]
        
        if api_key_owner:
            metrics.append((f"requests:owner:{api_key_owner}:{hour_bucket}", 1))
        
        # Record metrics
        pipe = self.redis.pipeline()
        for key, value in metrics:
            pipe.hincrby(f"{self.metrics_prefix}{key}", "count", 1)
            if "duration" in key:
                pipe.hincrby(f"{self.metrics_prefix}{key}", "sum", int(value))
                pipe.hincrby(f"{self.metrics_prefix}{key}", "max", int(value))
            pipe.expire(f"{self.metrics_prefix}{key}", 86400 * 7)  # 7 days retention
        
        pipe.execute()
    
    async def get_metrics(self, metric_type: str, time_range: int = 3600) -> Dict[str, Any]:
        """Get metrics for a time range."""
        now = int(time.time())
        start_time = now - time_range
        
        # Collect metrics from buckets
        metrics = {}
        bucket_size = 3600  # hourly buckets
        
        for timestamp in range(start_time, now, bucket_size):
            bucket = timestamp - (timestamp % bucket_size)
            key = f"{self.metrics_prefix}{metric_type}:{bucket}"
            
            data = self.redis.hgetall(key)
            if data:
                metrics[bucket] = {
                    k.decode() if isinstance(k, bytes) else k: 
                    int(v.decode() if isinstance(v, bytes) else v) 
                    for k, v in data.items()
                }
        
        return metrics