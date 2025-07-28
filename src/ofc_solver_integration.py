"""
OFC Solver integration layer for connecting MCTS algorithm with API.

This module provides the integration between the core MCTS algorithm
and the API layer, handling conversions and proper game state management.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from src.core.domain import (
    GameState, Street, Card, Rank, Suit,
    PlayerArrangement
)
from src.core.algorithms import MCTSEngine, MCTSConfig, Action
from src.logging_config import get_solver_logger, get_performance_logger, LogContext

logger = get_solver_logger()
perf_logger = get_performance_logger("solver")


@dataclass
class SolveResult:
    """Result from OFC solver with MCTS integration."""
    best_placement: Dict[str, str]  # card -> position mapping
    expected_score: float
    confidence: float
    simulations: int
    time_taken: float
    top_actions: List[Dict[str, Any]]


class OFCSolverIntegration:
    """
    OFC Solver with real MCTS integration.
    
    This class bridges the gap between the API layer and the core MCTS
    algorithm implementation.
    """
    
    def __init__(self,
                 threads: int = 4,
                 time_limit: float = 30.0,
                 simulations_limit: Optional[int] = None):
        """
        Initialize the solver with MCTS engine.
        
        Args:
            threads: Number of threads for parallel MCTS
            time_limit: Time limit for search in seconds
            simulations_limit: Optional limit on number of simulations
        """
        self.threads = threads
        self.time_limit = time_limit
        self.simulations_limit = simulations_limit
        
        # Create MCTS configuration
        self.mcts_config = MCTSConfig(
            time_limit=time_limit,
            num_simulations=simulations_limit,
            num_threads=threads,
            c_puct=1.4,
            use_transposition_table=True,
            progressive_widening=True
        )
        
        # Create MCTS engine
        self.mcts_engine = MCTSEngine(self.mcts_config)
        
        logger.info(
            "OFC Solver Integration initialized",
            extra={
                'component': 'solver_integration',
                'context': {
                    'threads': threads,
                    'time_limit': time_limit,
                    'simulations_limit': simulations_limit
                }
            }
        )
    
    def solve(self, game_state: GameState,
              options: Optional[Dict[str, Any]] = None) -> SolveResult:
        """
        Solve OFC position using MCTS algorithm.
        
        Args:
            game_state: Current game state
            options: Additional solver options
            
        Returns:
            SolveResult with best placement and statistics
        """
        start_time = time.time()
        
        with LogContext(logger, operation="mcts_solve") as log_ctx:
            log_ctx.log("info", "Starting MCTS solve",
                       street=game_state.current_street.name,
                       cards_to_place=len(game_state.current_hand))
            
            try:
                # Run MCTS search
                mcts_result = self.mcts_engine.search(game_state)
                
                # Extract best action
                best_action = mcts_result.best_action
                root_node = mcts_result.root_node
                
                # Convert action to placement dictionary
                best_placement = self._convert_action_to_placement(best_action)
                
                # Get statistics from root node
                action_stats = root_node.get_action_statistics()
                
                # Calculate expected score from root node
                expected_score = root_node.total_reward / max(root_node.visit_count, 1)
                
                # Calculate confidence based on visits
                confidence = min(root_node.visit_count / 10000.0, 0.99)
                
                # Convert top actions for API response
                top_actions = self._convert_action_statistics(action_stats[:5])
                
                elapsed_time = time.time() - start_time
                
                log_ctx.log("info", "MCTS solve completed",
                           simulations=self.mcts_engine.simulations_run,
                           nodes_evaluated=self.mcts_engine.nodes_evaluated,
                           expected_score=expected_score,
                           time_taken=elapsed_time)
                
                return SolveResult(
                    best_placement=best_placement,
                    expected_score=expected_score,
                    confidence=confidence,
                    simulations=self.mcts_engine.simulations_run,
                    time_taken=elapsed_time,
                    top_actions=top_actions
                )
                
            except Exception as e:
                log_ctx.log("error", f"MCTS solve failed: {str(e)}",
                           error_type=type(e).__name__)
                raise
    
    def _convert_action_to_placement(self, action: Action) -> Dict[str, str]:
        """Convert MCTS action to placement dictionary."""
        placement = {}
        
        for card, position, index in action.placements:
            card_str = f"{card.rank.value}{card.suit.value}"
            placement[card_str] = position
        
        return placement
    
    def _convert_action_statistics(self, 
                                 action_stats: List[Tuple[Action, int, float]]) -> List[Dict[str, Any]]:
        """Convert action statistics to API format."""
        top_actions = []
        
        for action, visits, avg_reward in action_stats:
            # Get first placement as representative
            if action.placements:
                card, position, _ = action.placements[0]
                card_str = f"{card.rank.value}{card.suit.value}"
                
                top_actions.append({
                    'card': card_str,
                    'position': position,
                    'visits': visits,
                    'avg_reward': avg_reward
                })
        
        return top_actions
    
    def solve_initial_placement(self, cards: List[Card]) -> SolveResult:
        """
        Solve initial 5-card placement.
        
        Args:
            cards: List of 5 cards to place
            
        Returns:
            SolveResult with optimal placement
        """
        if len(cards) != 5:
            raise ValueError(f"Initial placement requires exactly 5 cards, got {len(cards)}")
        
        # Create initial game state
        game_state = GameState(num_players=2, player_index=0)
        game_state.current_hand = cards
        game_state.current_street = Street.INITIAL
        
        # Solve using MCTS
        return self.solve(game_state)
    
    def configure(self, **kwargs):
        """Update solver configuration."""
        if 'time_limit' in kwargs:
            self.mcts_config.time_limit = kwargs['time_limit']
        if 'threads' in kwargs:
            self.mcts_config.num_threads = kwargs['threads']
        if 'simulations_limit' in kwargs:
            self.mcts_config.num_simulations = kwargs['simulations_limit']
        if 'exploration_constant' in kwargs:
            self.mcts_config.c_puct = kwargs['exploration_constant']
        
        # Update engine with new config
        self.mcts_engine.config = self.mcts_config


# Factory function for backward compatibility
def create_solver(**kwargs) -> OFCSolverIntegration:
    """Create a new OFC solver instance with MCTS integration."""
    return OFCSolverIntegration(**kwargs)