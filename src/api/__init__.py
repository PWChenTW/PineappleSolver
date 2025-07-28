"""
OFC Solver API package.
"""

from .app import app
from .models import (
    SolveRequest,
    SolveResult,
    AnalyzeRequest,
    PositionAnalysis,
    BatchSolveRequest,
    BatchJobResponse,
    HealthStatus
)

__all__ = [
    'app',
    'SolveRequest',
    'SolveResult',
    'AnalyzeRequest',
    'PositionAnalysis',
    'BatchSolveRequest',
    'BatchJobResponse',
    'HealthStatus'
]

__version__ = '1.0.0'