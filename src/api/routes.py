"""
API route implementations for OFC Solver.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import (
    SolveRequest, SolveResult, SolveStatistics,
    AnalyzeRequest, PositionAnalysis,
    BatchSolveRequest, BatchJobResponse, BatchJobStatus,
    AsyncTaskResponse, TaskStatusResponse, TaskStatus,
    HealthStatus, ServiceStatus, ComponentHealth,
    Move, MoveEvaluation, HandStrength,
    ErrorResponse, ErrorDetail, RequestContext,
    RateLimitInfo
)
from .middleware import (
    AuthenticationMiddleware, RateLimiter, AsyncTaskManager,
    get_request_context, get_rate_limit_key, error_handler,
    MetricsCollector
)
from .solver_adapter import MCTSSolver, PositionEvaluator
from .cache import get_cache_client, SimpleTaskQueue


# Create router
router = APIRouter(prefix="/api/v1", tags=["OFC Solver"])


# Dependencies
async def get_cache_client_dep(request: Request):
    """Get cache client instance from app state."""
    return request.app.state.redis


async def get_task_queue(request: Request) -> SimpleTaskQueue:
    """Get task queue instance from app state."""
    return request.app.state.task_queue


async def get_solver() -> MCTSSolver:
    """Get solver instance."""
    return MCTSSolver()


async def get_evaluator() -> PositionEvaluator:
    """Get position evaluator instance."""
    return PositionEvaluator()


async def get_auth_info(request: Request) -> dict:
    """Get authentication info (simplified for development)."""
    # In production, this would validate the API key
    # For now, return a mock auth info
    return {
        "owner": "test_user",
        "permissions": {
            "async_processing": True,
            "batch_processing": True,
            "admin": False
        },
        "limits": {
            "max_batch_size": 50
        }
    }


# Solve endpoint
@router.post("/solve", response_model=SolveResult)
async def solve_position(
    request: SolveRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    auth_info: dict = Depends(get_auth_info),
    cache_client = Depends(get_cache_client_dep),
    task_queue: SimpleTaskQueue = Depends(get_task_queue),
    solver: MCTSSolver = Depends(get_solver)
):
    """
    Solve an OFC game position.
    
    Uses MCTS algorithm to find the best move for the current position.
    Can be run synchronously or asynchronously based on the request.
    """
    # Use provided request ID or generate new one
    request_id = request.request_id or uuid4()
    
    # Check if async processing is requested
    if request.async_mode:
        # Check if async processing is enabled
        if not auth_info.get("permissions", {}).get("async_processing", True):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "ASYNC_NOT_ALLOWED",
                        "message": "Async processing not allowed for this API key"
                    }
                }
            )
        
        # Create async task
        task_id = await task_queue.create_task(
            task_type="solve",
            task_data={
                "request_id": str(request_id),
                "game_state": request.game_state.dict(),
                "options": request.options.dict()
            },
            priority=auth_info.get("priority", "normal")
        )
        
        # Return async response
        return AsyncTaskResponse(
            task_id=UUID(task_id),
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            estimated_completion_time=datetime.utcnow() + timedelta(seconds=request.options.time_limit),
            status_url=f"/api/v1/tasks/{task_id}"
        )
    
    # Synchronous processing
    start_time = datetime.utcnow()
    
    try:
        # Configure solver
        solver.configure(
            time_limit=request.options.time_limit,
            max_iterations=request.options.max_iterations,
            threads=request.options.threads,
            exploration_constant=request.options.exploration_constant,
            use_neural_network=request.options.use_neural_network
        )
        
        # Solve position
        result = await solver.solve(request.game_state)
        
        # Update result with request ID
        result.request_id = request_id
        
        # Calculate computation time
        computation_time = (datetime.utcnow() - start_time).total_seconds()
        result.computation_time = computation_time
        
        # Record metrics in background
        if hasattr(req.app.state, 'redis'):
            background_tasks.add_task(
                record_metrics,
                cache_client,
                endpoint="solve",
                method="POST",
                status_code=200,
                duration_ms=computation_time * 1000,
                api_key_owner=auth_info.get("owner")
            )
        
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail={
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Solver timeout after {request.options.time_limit} seconds"
                }
            }
        )
    except Exception as e:
        # Log error details
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Solver error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SOLVER_ERROR",
                    "message": "Failed to solve position",
                    "details": {"error": str(e)}
                }
            }
        )


# Analyze endpoint
@router.post("/analyze", response_model=PositionAnalysis)
async def analyze_position(
    request: AnalyzeRequest,
    auth_info: dict = Depends(get_auth_info),
    evaluator: PositionEvaluator = Depends(get_evaluator)
):
    """
    Analyze a game position without deep search.
    
    Provides quick evaluation and recommendations based on
    heuristics and pattern recognition.
    """
    # Use provided request ID or generate new one
    request_id = request.request_id or uuid4()
    
    # Perform analysis
    analysis = await evaluator.analyze(
        game_state=request.game_state,
        depth=request.options.depth,
        include_alternatives=request.options.include_alternatives
    )
    
    # Update with request ID
    analysis.request_id = request_id
    
    return analysis


# Batch solve endpoint
@router.post("/batch", response_model=BatchJobResponse)
async def batch_solve(
    request: BatchSolveRequest,
    auth_info: dict = Depends(get_auth_info),
    cache_client = Depends(get_cache_client_dep),
    task_queue: SimpleTaskQueue = Depends(get_task_queue)
):
    """
    Submit multiple positions for batch processing.
    
    Creates a batch job that processes positions asynchronously.
    Use the returned job ID to check status and retrieve results.
    """
    # Check batch processing permission
    if not auth_info.get("permissions", {}).get("batch_processing", True):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "BATCH_NOT_ALLOWED",
                    "message": "Batch processing not allowed for this API key"
                }
            }
        )
    
    # Check batch size limit
    max_batch_size = auth_info.get("limits", {}).get("max_batch_size", 100)
    if len(request.positions) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "BATCH_TOO_LARGE",
                    "message": f"Batch size exceeds limit of {max_batch_size}"
                }
            }
        )
    
    # Create batch job
    job_id = uuid4()
    
    # Create tasks for each position
    task_ids = []
    for position in request.positions:
        task_id = await task_queue.create_task(
            task_type="solve",
            task_data={
                "request_id": str(request.request_id or uuid4()),
                "position_id": position.id,
                "game_state": position.game_state.dict(),
                "options": position.options.dict(),
                "batch_job_id": str(job_id)
            },
            priority=request.batch_options.priority.value
        )
        task_ids.append(task_id)
    
    # Store batch job metadata
    batch_job = {
        "job_id": str(job_id),
        "status": "processing",
        "created_at": datetime.utcnow().isoformat(),
        "total_positions": len(request.positions),
        "task_ids": task_ids,
        "options": request.batch_options.dict()
    }
    
    cache_client.setex(
        f"ofc_solver:batch:{job_id}",
        86400,  # 24 hours TTL
        json.dumps(batch_job)
    )
    
    # Return batch job response
    return BatchJobResponse(
        job_id=job_id,
        status=TaskStatus.PROCESSING,
        created_at=datetime.utcnow(),
        total_positions=len(request.positions),
        status_url=f"/api/v1/batch/{job_id}"
    )


# Get batch job status
@router.get("/batch/{job_id}", response_model=BatchJobStatus)
async def get_batch_status(
    job_id: UUID,
    auth_info: dict = Depends(get_auth_info),
    cache_client = Depends(get_cache_client_dep),
    task_queue: SimpleTaskQueue = Depends(get_task_queue)
):
    """Get the status and results of a batch job."""
    # Get batch job metadata
    job_data = cache_client.get(f"ofc_solver:batch:{job_id}")
    if not job_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Batch job {job_id} not found"
                }
            }
        )
    
    job = json.loads(job_data)
    
    # Get status of all tasks
    results = []
    completed = 0
    failed = 0
    
    for task_id in job["task_ids"]:
        task_status = await task_queue.get_task_status(task_id)
        if task_status:
            position_result = {
                "position_id": task_status["data"]["position_id"],
                "status": task_status["status"]
            }
            
            if task_status["status"] == "completed":
                completed += 1
                position_result["result"] = task_status.get("result")
            elif task_status["status"] == "failed":
                failed += 1
                position_result["error"] = task_status.get("error")
            
            results.append(position_result)
    
    # Determine overall status
    if completed + failed == len(job["task_ids"]):
        overall_status = TaskStatus.COMPLETED
    else:
        overall_status = TaskStatus.PROCESSING
    
    # Build response
    return BatchJobStatus(
        job_id=UUID(job["job_id"]),
        status=overall_status,
        created_at=datetime.fromisoformat(job["created_at"]),
        updated_at=datetime.utcnow(),
        completed_at=datetime.utcnow() if overall_status == TaskStatus.COMPLETED else None,
        total_positions=job["total_positions"],
        completed_positions=completed,
        failed_positions=failed,
        results=results
    )


# Get async task status
@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: UUID,
    auth_info: dict = Depends(get_auth_info),
    task_queue: SimpleTaskQueue = Depends(get_task_queue)
):
    """Get the status and result of an async task."""
    task = await task_queue.get_task_status(str(task_id))
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task {task_id} not found"
                }
            }
        )
    
    # Build response
    return TaskStatusResponse(
        task_id=UUID(task["id"]),
        status=TaskStatus(task["status"]),
        progress=task.get("progress"),
        created_at=datetime.fromisoformat(task["created_at"]),
        updated_at=datetime.fromisoformat(task["updated_at"]),
        completed_at=datetime.fromisoformat(task["completed_at"]) if task.get("completed_at") else None,
        result=task.get("result"),
        error=task.get("error")
    )


# Health check endpoint
@router.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check(
    req: Request,
    cache_client = Depends(get_cache_client_dep)
):
    """
    Check service health and component status.
    
    Returns detailed health information about all service components.
    No authentication required.
    """
    # Check component health
    components = {}
    overall_status = ServiceStatus.HEALTHY
    
    # Check Cache
    try:
        start = datetime.utcnow()
        cache_client.ping()
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        components["cache"] = ComponentHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=latency,
            details={"type": "memory", "connected": True}
        )
    except Exception as e:
        components["cache"] = ComponentHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=0,
            details={"error": str(e)}
        )
        overall_status = ServiceStatus.UNHEALTHY
    
    # Check solver engine
    try:
        start = datetime.utcnow()
        solver = await get_solver()
        solver.health_check()
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        components["solver_engine"] = ComponentHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=latency,
            details={"version": solver.version}
        )
    except Exception as e:
        components["solver_engine"] = ComponentHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=0,
            details={"error": str(e)}
        )
        overall_status = ServiceStatus.DEGRADED
    
    # Check task queue
    try:
        queue_size = cache_client.llen("ofc_solver:tasks")
        components["task_queue"] = ComponentHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=0,
            details={"queue_size": queue_size}
        )
    except Exception as e:
        components["task_queue"] = ComponentHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=0,
            details={"error": str(e)}
        )
    
    # Build response
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime=int((datetime.utcnow() - req.app.state.start_time).total_seconds()),
        components=components
    )


# Metrics endpoint (internal use)
@router.get("/metrics", include_in_schema=False)
async def get_metrics(
    metric_type: str = "requests:total",
    time_range: int = 3600,
    auth_info: dict = Depends(get_auth_info),
    cache_client = Depends(get_cache_client_dep)
):
    """Get API metrics (admin only)."""
    # Check admin permission
    if not auth_info.get("permissions", {}).get("admin", False):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Admin access required"
                }
            }
        )
    
    metrics_collector = MetricsCollector(cache_client)
    metrics = await metrics_collector.get_metrics(metric_type, time_range)
    
    return JSONResponse(content={"metrics": metrics})


# Helper function to record metrics
async def record_metrics(cache_client, endpoint: str, method: str, 
                        status_code: int, duration_ms: float, 
                        api_key_owner: Optional[str] = None):
    """Record request metrics."""
    try:
        metrics_collector = MetricsCollector(cache_client)
        await metrics_collector.record_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            api_key_owner=api_key_owner
        )
    except Exception as e:
        # Log but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to record metrics: {e}")