"""
GUI-specific routes for OFC Solver API.

This module provides endpoints specifically designed for the web GUI interface.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from .routes import (
    get_auth_info, get_cache_client_dep, get_solver,
    record_metrics
)
from .gui_adapter import convert_gui_request
from .solver_adapter import MCTSSolver

logger = logging.getLogger(__name__)

# Create router for GUI endpoints
gui_router = APIRouter(prefix="/api/v1", tags=["GUI"])


@gui_router.post("/solve")
async def solve_position_gui(
    request_body: Dict[str, Any],
    background_tasks: BackgroundTasks,
    req: Request,
    auth_info: dict = Depends(get_auth_info),
    cache_client = Depends(get_cache_client_dep),
    solver: MCTSSolver = Depends(get_solver)
):
    """
    Solve an OFC game position (GUI version).
    
    This endpoint accepts the GUI's format and converts it to the internal API format.
    """
    start_time = datetime.utcnow()
    
    try:
        # Check if this is a GUI request (has drawn_cards field)
        is_gui_request = 'game_state' in request_body and 'drawn_cards' in request_body.get('game_state', {})
        
        if is_gui_request:
            # Convert GUI request to API format
            logger.info("Processing GUI request format")
            api_request = convert_gui_request(request_body)
        else:
            # Already in API format, parse directly
            from .models import SolveRequest
            api_request = SolveRequest(**request_body)
        
        # Configure solver
        solver.configure(
            time_limit=api_request.options.time_limit,
            max_iterations=api_request.options.max_iterations,
            threads=api_request.options.threads,
            exploration_constant=api_request.options.exploration_constant,
            use_neural_network=api_request.options.use_neural_network
        )
        
        # Solve position
        result = await solver.solve(api_request.game_state)
        
        # Update result with request ID
        result.request_id = api_request.request_id or uuid4()
        
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
        
        # Convert result to dict for JSON response
        return result.dict()
        
    except ValueError as e:
        # Validation error
        logger.warning(f"Validation error in GUI solve: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request format",
                    "details": {"error": str(e)}
                }
            }
        )
    except Exception as e:
        # Log error details
        logger.error(f"GUI solver error: {str(e)}", exc_info=True)
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