"""
OFC Solver with Prometheus metrics integration.
"""

import time
from typing import List, Dict, Any, Optional
import uuid

from .ofc_solver import OFCSolver, GameState, SolveResult
from .logging_config import LogContext
from .api.prometheus_metrics import (
    record_solver_metrics,
    record_error,
    solver_simulation_rate,
    measure_time
)


class PrometheusOFCSolver(OFCSolver):
    """OFC Solver with Prometheus metrics collection."""
    
    def solve(self, game_state: GameState, 
              options: Optional[Dict[str, Any]] = None) -> SolveResult:
        """
        Solve OFC position with metrics collection.
        
        Args:
            game_state: Current game state
            options: Solver options
            
        Returns:
            Solve result
        """
        start_time = time.time()
        status = "success"
        
        try:
            # Call parent solve method
            result = super().solve(game_state, options)
            
            # Record solver metrics
            duration = time.time() - start_time
            record_solver_metrics(
                status=status,
                duration=duration,
                simulations=result.simulations,
                expected_score=result.expected_score,
                confidence=result.confidence
            )
            
            return result
            
        except Exception as e:
            # Record error
            status = "failed"
            duration = time.time() - start_time
            
            record_error(
                error_type=type(e).__name__,
                component="solver"
            )
            
            # Record failed solve metrics
            record_solver_metrics(
                status=status,
                duration=duration,
                simulations=0,
                expected_score=0.0,
                confidence=0.0
            )
            
            raise
    
    def _run_mcts_search(self, game_state: GameState, 
                        options: Optional[Dict[str, Any]],
                        log_ctx: LogContext) -> SolveResult:
        """Run MCTS search with metrics collection."""
        # Start simulation rate tracking
        start_time = time.time()
        last_update_time = start_time
        last_simulation_count = 0
        
        # Override parent method to add metrics
        result = super()._run_mcts_search(game_state, options, log_ctx)
        
        # Final simulation rate
        total_duration = time.time() - start_time
        if total_duration > 0:
            final_rate = result.simulations / total_duration
            solver_simulation_rate.set(final_rate)
        
        return result


# Factory function
def create_prometheus_solver(**kwargs) -> PrometheusOFCSolver:
    """Create OFC solver with Prometheus metrics."""
    return PrometheusOFCSolver(**kwargs)