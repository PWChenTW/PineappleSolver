"""
Pydantic models for OFC Solver API.

This module defines all request/response models for the RESTful API,
ensuring type safety and automatic validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, conint, confloat, constr


# Enums
class Rank(str, Enum):
    """Card rank enumeration."""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class Suit(str, Enum):
    """Card suit enumeration."""
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"


class HandType(str, Enum):
    """Hand placement enumeration."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceStatus(str, Enum):
    """Service health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class Priority(str, Enum):
    """Priority level enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


# Base Models
class Card(BaseModel):
    """Card representation."""
    rank: Rank
    suit: Suit
    
    class Config:
        schema_extra = {
            "example": {"rank": "A", "suit": "s"}
        }


class HandCards(BaseModel):
    """Hand cards representation."""
    cards: List[Card]
    max_size: conint(ge=3, le=5) = Field(..., description="Maximum hand size (3 for top, 5 for middle/bottom)")
    
    @validator('cards')
    def validate_hand_size(cls, v, values):
        if 'max_size' in values and len(v) > values['max_size']:
            raise ValueError(f"Hand contains {len(v)} cards, but max_size is {values['max_size']}")
        return v


class PlayerState(BaseModel):
    """Player state representation."""
    player_id: str
    top_hand: HandCards
    middle_hand: HandCards
    bottom_hand: HandCards
    in_fantasy_land: bool = False
    next_fantasy_land: bool = False
    is_folded: bool = False


class GameState(BaseModel):
    """Complete game state representation."""
    current_round: conint(ge=1, le=17) = Field(..., description="Current round number (1-17)")
    players: List[PlayerState] = Field(..., min_items=2, max_items=4)
    current_player_index: conint(ge=0) = Field(..., description="Index of current player")
    remaining_deck: List[Card] = Field(..., description="Cards remaining in deck")
    dealer_position: Optional[conint(ge=0)] = Field(None, description="Dealer position index")
    
    @validator('current_player_index')
    def validate_player_index(cls, v, values):
        if 'players' in values and v >= len(values['players']):
            raise ValueError(f"current_player_index {v} is out of bounds for {len(values['players'])} players")
        return v
    
    @validator('remaining_deck')
    def validate_deck_size(cls, v, values):
        # Standard deck has 52 cards
        if 'players' in values and 'current_round' in values:
            used_cards = 0
            for player in values['players']:
                used_cards += len(player.top_hand.cards)
                used_cards += len(player.middle_hand.cards)
                used_cards += len(player.bottom_hand.cards)
            
            total_cards = used_cards + len(v)
            if total_cards > 52:
                raise ValueError(f"Total cards ({total_cards}) exceeds deck size (52)")
        return v


# Options Models
class SolveOptions(BaseModel):
    """Options for solve endpoint."""
    time_limit: confloat(ge=0.1, le=300) = Field(30, description="Time limit in seconds")
    max_iterations: Optional[conint(ge=100, le=1000000)] = Field(None, description="Maximum MCTS iterations")
    threads: conint(ge=1, le=32) = Field(4, description="Number of parallel threads")
    exploration_constant: confloat(ge=0.1, le=10.0) = Field(1.4, description="MCTS exploration constant")
    use_neural_network: bool = Field(False, description="Whether to use neural network evaluation")


class AnalyzeOptions(BaseModel):
    """Options for analyze endpoint."""
    depth: conint(ge=1, le=5) = Field(3, description="Analysis depth")
    include_alternatives: bool = Field(True, description="Include alternative moves")


class BatchOptions(BaseModel):
    """Options for batch processing."""
    priority: Priority = Field(Priority.NORMAL)
    notification_webhook: Optional[str] = Field(None, description="Webhook URL for completion notification")
    
    @validator('notification_webhook')
    def validate_webhook_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Webhook URL must start with http:// or https://')
        return v


# Request Models
class SolveRequest(BaseModel):
    """Request model for solve endpoint."""
    request_id: Optional[UUID] = Field(None, description="Client-provided request ID for tracking")
    game_state: GameState
    options: Optional[SolveOptions] = Field(default_factory=SolveOptions)
    async_mode: bool = Field(False, alias="async", description="Whether to process asynchronously")


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""
    request_id: Optional[UUID] = Field(None, description="Client-provided request ID for tracking")
    game_state: GameState
    options: Optional[AnalyzeOptions] = Field(default_factory=AnalyzeOptions)


class BatchPosition(BaseModel):
    """Single position in batch request."""
    id: str = Field(..., description="Position identifier within batch")
    game_state: GameState
    options: Optional[SolveOptions] = Field(default_factory=SolveOptions)


class BatchSolveRequest(BaseModel):
    """Request model for batch solve endpoint."""
    request_id: Optional[UUID] = Field(None, description="Client-provided request ID for tracking")
    positions: List[BatchPosition] = Field(..., min_items=1, max_items=100)
    batch_options: Optional[BatchOptions] = Field(default_factory=BatchOptions)


# Move Models
class CardPlacement(BaseModel):
    """Card placement representation."""
    card: Card
    hand: HandType


class Move(BaseModel):
    """Move representation."""
    card_placements: List[CardPlacement]
    is_fold: bool = False
    
    @validator('card_placements')
    def validate_placements(cls, v, values):
        if values.get('is_fold') and len(v) > 0:
            raise ValueError("Fold move should not have card placements")
        return v


class MoveEvaluation(BaseModel):
    """Move with evaluation data."""
    move: Move
    evaluation: float
    visit_count: int
    win_rate: confloat(ge=0, le=1)


class MoveRecommendation(BaseModel):
    """Move recommendation with reasoning."""
    move: Move
    reasoning: str = Field(..., description="Explanation for the recommendation")
    priority: Priority
    expected_value: Optional[float] = None


# Statistics Models
class SolveStatistics(BaseModel):
    """Solve statistics."""
    total_iterations: int
    nodes_visited: int
    average_depth: float
    max_depth: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None


class HandStrengthImprovement(BaseModel):
    """Potential hand improvement."""
    hand_type: str
    probability: confloat(ge=0, le=1)
    required_cards: List[Card]


class HandStrength(BaseModel):
    """Hand strength analysis."""
    current_rank: str = Field(..., description="Current hand ranking")
    current_strength: confloat(ge=0, le=1)
    potential_improvements: List[HandStrengthImprovement]


# Response Models
class SolveResult(BaseModel):
    """Solve endpoint response."""
    request_id: UUID
    best_move: Move
    evaluation: float = Field(..., description="Position evaluation score")
    confidence: confloat(ge=0, le=1) = Field(..., description="Confidence in the solution")
    alternative_moves: Optional[List[MoveEvaluation]] = None
    statistics: SolveStatistics
    computation_time: float = Field(..., description="Computation time in seconds")


class PositionAnalysis(BaseModel):
    """Analyze endpoint response."""
    request_id: UUID
    evaluation: float = Field(..., description="Overall position evaluation")
    hand_strengths: Dict[str, HandStrength] = Field(..., description="Strength analysis for each hand")
    recommendations: List[MoveRecommendation]
    fantasy_land_probability: confloat(ge=0, le=1)
    foul_probability: confloat(ge=0, le=1)


class AsyncTaskResponse(BaseModel):
    """Async task creation response."""
    task_id: UUID
    status: TaskStatus
    created_at: datetime
    estimated_completion_time: Optional[datetime] = None
    status_url: str


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: UUID
    status: TaskStatus
    progress: Optional[conint(ge=0, le=100)] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[SolveResult] = None
    error: Optional[Dict[str, Any]] = None


class BatchJobResponse(BaseModel):
    """Batch job creation response."""
    job_id: UUID
    status: TaskStatus
    created_at: datetime
    total_positions: int
    status_url: str


class BatchPositionResult(BaseModel):
    """Result for single position in batch."""
    position_id: str
    status: TaskStatus
    result: Optional[SolveResult] = None
    error: Optional[Dict[str, Any]] = None


class BatchJobStatus(BaseModel):
    """Batch job status response."""
    job_id: UUID
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    total_positions: int
    completed_positions: int
    failed_positions: int
    results: List[BatchPositionResult]


# Health Check Models
class ComponentHealth(BaseModel):
    """Component health status."""
    status: ServiceStatus
    latency_ms: float
    details: Optional[Dict[str, Any]] = None


class HealthStatus(BaseModel):
    """Service health status response."""
    status: ServiceStatus
    timestamp: datetime
    version: str
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    components: Dict[str, ComponentHealth]


# Error Models
class FieldError(BaseModel):
    """Field-level error."""
    field: str = Field(..., description="Field path with error")
    message: str = Field(..., description="Error message for the field")
    code: Optional[str] = Field(None, description="Error code")


class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    field_errors: Optional[List[FieldError]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
    request_id: UUID
    timestamp: datetime


# Rate Limit Models
class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int = Field(..., description="Rate limit ceiling")
    remaining: int = Field(..., description="Remaining requests")
    reset: int = Field(..., description="Unix timestamp when limit resets")


# Middleware Models
class RequestContext(BaseModel):
    """Request context for tracking."""
    request_id: UUID
    api_key: Optional[str] = None
    client_ip: str
    user_agent: Optional[str] = None
    timestamp: datetime
    
    class Config:
        # Allow extra fields for extensibility
        extra = "allow"