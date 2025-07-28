"""
Enhanced middleware with Prometheus metrics integration.
"""

import time
import sys
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import psutil

from .middleware import (
    RequestTrackingMiddleware,
    RequestValidationMiddleware,
    APIConfig
)
from .prometheus_metrics import (
    record_api_metrics,
    track_active_requests,
    system_cpu_usage_percent,
    system_memory_usage_bytes,
    system_thread_count,
    error_count_total,
    rate_limit_exceeded_total,
    async_queue_size
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for API requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        # Extract endpoint and method
        method = request.method
        path = request.url.path
        
        # Normalize endpoint for metrics (remove path parameters)
        endpoint = self._normalize_endpoint(path)
        
        # Track active requests
        with track_active_requests(method, endpoint):
            # Record start time
            start_time = time.time()
            
            # Get request size
            request_size = int(request.headers.get("content-length", 0))
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Get response size (approximate)
                response_size = int(response.headers.get("content-length", 0))
                
                # Record metrics
                record_api_metrics(
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration=duration,
                    request_size=request_size,
                    response_size=response_size
                )
                
                # Add Prometheus headers
                response.headers["X-Response-Time"] = f"{duration:.3f}"
                
                return response
                
            except HTTPException as e:
                # Handle HTTP exceptions
                duration = time.time() - start_time
                
                # Record metrics for error
                record_api_metrics(
                    method=method,
                    endpoint=endpoint,
                    status_code=e.status_code,
                    duration=duration,
                    request_size=request_size
                )
                
                # Record specific error types
                if e.status_code == 429:
                    # Extract API key owner if available
                    api_key_owner = getattr(request.state, 'api_key_owner', 'unknown')
                    rate_limit_exceeded_total.labels(api_key_owner=api_key_owner).inc()
                
                # Record general error
                error_count_total.labels(
                    error_type=f"http_{e.status_code}",
                    component="api"
                ).inc()
                
                raise
                
            except Exception as e:
                # Handle other exceptions
                duration = time.time() - start_time
                
                # Record metrics for 500 error
                record_api_metrics(
                    method=method,
                    endpoint=endpoint,
                    status_code=500,
                    duration=duration,
                    request_size=request_size
                )
                
                # Record error
                error_count_total.labels(
                    error_type=type(e).__name__,
                    component="api"
                ).inc()
                
                raise
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Remove trailing slash
        path = path.rstrip('/')
        
        # Replace path parameters with placeholders
        parts = path.split('/')
        normalized_parts = []
        
        for part in parts:
            # Check if part looks like a UUID or ID
            if len(part) == 36 and part.count('-') == 4:  # UUID
                normalized_parts.append('{id}')
            elif part.isdigit():  # Numeric ID
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        
        return '/'.join(normalized_parts) or '/'


class SystemMetricsCollector:
    """Collects system metrics for Prometheus."""
    
    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        self.process = psutil.Process()
        self.last_update = 0
    
    def collect_metrics(self):
        """Collect system metrics if update interval has passed."""
        current_time = time.time()
        
        if current_time - self.last_update < self.update_interval:
            return
        
        self.last_update = current_time
        
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent(interval=None)
            system_cpu_usage_percent.set(cpu_percent)
            
            # Memory usage
            memory_info = self.process.memory_info()
            system_memory_usage_bytes.labels(type='rss').set(memory_info.rss)
            system_memory_usage_bytes.labels(type='vms').set(memory_info.vms)
            
            # Available memory
            virtual_memory = psutil.virtual_memory()
            system_memory_usage_bytes.labels(type='available').set(virtual_memory.available)
            
            # Thread count
            num_threads = self.process.num_threads()
            system_thread_count.set(num_threads)
            
        except Exception as e:
            # Don't let metrics collection crash the application
            error_count_total.labels(
                error_type=type(e).__name__,
                component="metrics_collector"
            ).inc()


# Enhanced RequestTrackingMiddleware with Prometheus
class EnhancedRequestTrackingMiddleware(RequestTrackingMiddleware):
    """Request tracking middleware with Prometheus metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.system_metrics = SystemMetricsCollector()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with enhanced tracking."""
        # Collect system metrics periodically
        self.system_metrics.collect_metrics()
        
        # Call parent implementation
        return await super().dispatch(request, call_next)


# Enhanced AsyncTaskManager with metrics
class MetricsAsyncTaskManager:
    """Async task manager with Prometheus metrics."""
    
    def __init__(self, base_manager):
        self.base_manager = base_manager
    
    async def create_task(self, task_type: str, task_data: Dict[str, Any], 
                         priority: str = "normal") -> str:
        """Create task and update metrics."""
        # Update queue size before adding
        queue_size = self.base_manager.redis.llen(self.base_manager.task_queue)
        async_queue_size.set(queue_size)
        
        # Create task
        task_id = await self.base_manager.create_task(task_type, task_data, priority)
        
        # Update queue size after adding
        async_queue_size.set(queue_size + 1)
        
        return task_id
    
    async def update_task_status(self, task_id: str, status: str, 
                               result: Optional[Dict[str, Any]] = None,
                               error: Optional[Dict[str, Any]] = None,
                               progress: Optional[int] = None):
        """Update task status with metrics."""
        # Get task info for metrics
        task = await self.base_manager.get_task_status(task_id)
        
        if task and status in ["completed", "failed"]:
            # Calculate duration
            from datetime import datetime
            created_at = datetime.fromisoformat(task['created_at'])
            completed_at = datetime.utcnow()
            duration = (completed_at - created_at).total_seconds()
            
            # Record task duration
            from .prometheus_metrics import async_task_duration_seconds
            async_task_duration_seconds.labels(task_type=task['type']).observe(duration)
            
            # Update queue size
            queue_size = self.base_manager.redis.llen(self.base_manager.task_queue)
            async_queue_size.set(queue_size)
        
        # Update task status
        await self.base_manager.update_task_status(
            task_id, status, result, error, progress
        )