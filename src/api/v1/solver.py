"""
Solver endpoints for OFC API v1.

Simple interface for initial 5-card placement solving.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging

from src.application import OFCSolverService, SolveRequestDTO


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/solver", tags=["solver"])

# Initialize service
solver_service = OFCSolverService()


class SolveInitialRequest(BaseModel):
    """Request model for solving initial 5 cards."""
    cards: List[str] = Field(..., description="List of 5 cards in string format (e.g., 'As', 'Kh')", min_items=5, max_items=5)
    time_limit: float = Field(30.0, description="Time limit in seconds", ge=1.0, le=300.0)
    num_threads: int = Field(4, description="Number of threads for parallel search", ge=1, le=32)
    
    class Config:
        schema_extra = {
            "example": {
                "cards": ["As", "Kh", "Qc", "Jd", "Ts"],
                "time_limit": 30.0,
                "num_threads": 4
            }
        }


class PlacementResponse(BaseModel):
    """Single card placement."""
    card: str = Field(..., description="Card string (e.g., 'As')")
    position: str = Field(..., description="Position: 'front', 'middle', or 'back'")
    index: int = Field(..., description="Index within the position (0-based)")


class SolveInitialResponse(BaseModel):
    """Response for initial solve request."""
    placements: List[PlacementResponse] = Field(..., description="Optimal card placements")
    evaluation: float = Field(..., description="Position evaluation score")
    confidence: float = Field(..., description="Confidence in the solution (0-1)")
    visit_count: int = Field(..., description="Number of visits to best action")
    computation_time: float = Field(..., description="Computation time in seconds")
    statistics: Dict[str, Any] = Field(..., description="Search statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "placements": [
                    {"card": "As", "position": "back", "index": 0},
                    {"card": "Kh", "position": "back", "index": 1},
                    {"card": "Qc", "position": "middle", "index": 0},
                    {"card": "Jd", "position": "middle", "index": 1},
                    {"card": "Ts", "position": "front", "index": 0}
                ],
                "evaluation": 0.65,
                "confidence": 0.85,
                "visit_count": 15234,
                "computation_time": 29.8,
                "statistics": {
                    "total_simulations": 50000,
                    "nodes_evaluated": 125000,
                    "config": {
                        "time_limit": 30.0,
                        "num_threads": 4,
                        "c_puct": 1.4
                    }
                }
            }
        }


@router.post("/initial", response_model=SolveInitialResponse)
async def solve_initial_placement(request: SolveInitialRequest):
    """
    Solve optimal placement for initial 5 cards.
    
    This endpoint uses Monte Carlo Tree Search (MCTS) to find the optimal
    placement for the initial 5 cards in Pineapple OFC.
    """
    try:
        # Convert to DTO
        solve_request = SolveRequestDTO(
            cards=request.cards,
            time_limit=request.time_limit,
            num_threads=request.num_threads
        )
        
        # Solve
        result = solver_service.solve_initial_placement(solve_request)
        
        # Convert to response
        return SolveInitialResponse(
            placements=[
                PlacementResponse(
                    card=p.card,
                    position=p.position,
                    index=p.index
                )
                for p in result.placements
            ],
            evaluation=result.evaluation,
            confidence=result.confidence,
            visit_count=result.visit_count,
            computation_time=result.computation_time,
            statistics=result.statistics
        )
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error solving initial placement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Check solver service health."""
    return {
        "status": "healthy",
        "service": "ofc-solver",
        "version": "1.0.0"
    }