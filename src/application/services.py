"""
Application services for OFC Solver.

Coordinates between API layer and core domain.
"""

import time
import logging
from typing import Optional, List

from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSConfig
from .dto import (
    SolveRequestDTO,
    SolveResultDTO,
    PlacementDTO,
    converter
)


logger = logging.getLogger(__name__)


class OFCSolverService:
    """
    Main service for solving OFC positions.
    
    Provides high-level interface for the MCTS solver.
    """
    
    def __init__(self):
        """Initialize solver service."""
        self.default_config = MCTSConfig(
            time_limit=30.0,
            num_threads=4,
            c_puct=1.4,
            use_transposition_table=True,
            progressive_widening=True
        )
    
    def solve_initial_placement(self, request: SolveRequestDTO) -> SolveResultDTO:
        """
        Solve initial 5-card placement.
        
        Args:
            request: Solve request with 5 cards
            
        Returns:
            Solution with optimal placements
            
        Raises:
            ValueError: If request is invalid
        """
        start_time = time.time()
        
        # Validate request
        request.validate()
        
        logger.info(f"Solving initial placement for cards: {request.cards}")
        
        try:
            # Create game state with initial cards
            game_state = converter.create_initial_game_state(request.cards)
            
            # Configure MCTS
            config = MCTSConfig(
                time_limit=request.time_limit,
                num_threads=request.num_threads,
                c_puct=self.default_config.c_puct,
                use_transposition_table=self.default_config.use_transposition_table,
                progressive_widening=self.default_config.progressive_widening
            )
            
            # Create and run MCTS engine
            engine = MCTSEngine(config)
            
            # Progress callback for logging
            def progress_callback(simulations: int, elapsed: float):
                if simulations % 1000 == 0:
                    logger.info(f"Progress: {simulations} simulations in {elapsed:.2f}s")
            
            # Run search
            result = engine.search(game_state, progress_callback)
            
            # Calculate computation time
            computation_time = time.time() - start_time
            
            # Extract best action
            best_action = result.best_action
            root_node = result.root_node
            
            # Convert to DTOs
            placements = converter.action_to_placements(best_action)
            
            # Calculate confidence based on visit distribution
            total_visits = root_node.visit_count
            best_visits = 0
            if root_node.children:
                for child in root_node.children.values():
                    if child.parent_action == best_action:
                        best_visits = child.visit_count
                        break
            
            confidence = best_visits / total_visits if total_visits > 0 else 0.0
            
            # Get evaluation (win rate of best action)
            evaluation = root_node.get_action_win_rate(best_action)
            
            # Extract statistics
            statistics = converter.extract_statistics(engine.get_statistics())
            
            logger.info(f"Solution found in {computation_time:.2f}s with {statistics['total_simulations']} simulations")
            
            return SolveResultDTO(
                placements=placements,
                evaluation=evaluation,
                confidence=confidence,
                visit_count=best_visits,
                computation_time=computation_time,
                statistics=statistics
            )
            
        except Exception as e:
            logger.error(f"Error solving initial placement: {e}", exc_info=True)
            raise
    
    def validate_placement(self, cards: List[str], placements: List[PlacementDTO]) -> bool:
        """
        Validate that a placement is legal.
        
        Args:
            cards: Original cards
            placements: Proposed placements
            
        Returns:
            True if placement is valid
        """
        try:
            # Check all cards are used
            placed_cards = {p.card for p in placements}
            if placed_cards != set(cards):
                return False
            
            # Check positions are valid
            for p in placements:
                if p.position not in ['front', 'middle', 'back']:
                    return False
                
                # Check index bounds
                if p.position == 'front' and p.index not in [0, 1, 2]:
                    return False
                elif p.position in ['middle', 'back'] and p.index not in [0, 1, 2, 3, 4]:
                    return False
            
            # Create game state and apply placements to check validity
            game_state = converter.create_initial_game_state(cards)
            
            placement_tuples = [p.to_tuple() for p in placements]
            game_state.place_cards(placement_tuples)
            
            # If no exception was raised, placement is valid
            return True
            
        except Exception:
            return False