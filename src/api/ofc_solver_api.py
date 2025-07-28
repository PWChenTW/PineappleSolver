"""
Unified OFC Solver API.

This module provides the main API interface for the OFC Solver,
handling all external interactions through a clean, consistent interface.
"""

from typing import List, Dict, Any, Optional
import logging

from src.api.dto import (
    GameStateDTO, SolveRequestDTO, SolveResultDTO,
    InitialPlacementRequestDTO, PlacementDTO
)
from src.application.ofc_solver_service import OFCSolverService
from src.exceptions import InvalidInputError, SolverError
from src.logging_config import get_api_logger

logger = get_api_logger()


class OFCSolverAPI:
    """
    Main API class for OFC Solver.
    
    This class provides a clean, unified interface for all solver operations,
    handling DTO conversions and error handling.
    """
    
    def __init__(self,
                 threads: int = 4,
                 default_time_limit: float = 30.0):
        """
        Initialize the OFC Solver API.
        
        Args:
            threads: Number of threads for parallel MCTS
            default_time_limit: Default time limit for solving
        """
        self.service = OFCSolverService(
            threads=threads,
            default_time_limit=default_time_limit
        )
        
        logger.info(f"OFC Solver API initialized with {threads} threads")
    
    def solve_position(self, game_state: Dict[str, Any],
                      time_limit: Optional[float] = None,
                      simulations_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Solve an OFC position.
        
        Args:
            game_state: Game state dictionary with current position
            time_limit: Optional time limit override
            simulations_limit: Optional simulations limit
            
        Returns:
            Dictionary with solution including best placement and statistics
            
        Raises:
            InvalidInputError: If input is invalid
            SolverError: If solving fails
        """
        try:
            # Create DTO from input
            game_state_dto = GameStateDTO.from_dict(game_state)
            request = SolveRequestDTO(
                game_state=game_state_dto,
                time_limit=time_limit,
                simulations_limit=simulations_limit
            )
            
            # Solve using service
            result = self.service.solve_position(request)
            
            # Convert result to dictionary
            return result.to_dict()
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(f"Failed to solve position: {str(e)}")
            raise SolverError(f"Solver failed: {str(e)}")
    
    def solve_initial_placement(self, cards: List[str],
                               time_limit: Optional[float] = None) -> Dict[str, Any]:
        """
        Solve initial 5-card placement.
        
        Args:
            cards: List of 5 cards in string format (e.g., ["As", "Kh", "Qd", "Jc", "Ts"])
            time_limit: Optional time limit override
            
        Returns:
            Dictionary with optimal placement for all 5 cards
            
        Raises:
            InvalidInputError: If input is invalid
            SolverError: If solving fails
        """
        try:
            # Create request DTO
            request = InitialPlacementRequestDTO(
                cards=cards,
                time_limit=time_limit
            )
            
            # Solve using service
            result = self.service.solve_initial_placement(request)
            
            # Convert to simple placement format for backward compatibility
            placement_dict = {}
            for placement in result.best_placements:
                placement_dict[placement.card] = placement.position
            
            return {
                'placement': placement_dict,
                'expected_score': result.expected_score,
                'confidence': result.confidence,
                'simulations': result.simulations_count,
                'time_taken': result.time_taken,
                'detailed_result': result.to_dict()
            }
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(f"Failed to solve initial placement: {str(e)}")
            raise SolverError(f"Solver failed: {str(e)}")
    
    def evaluate_position(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a static OFC position without solving.
        
        Args:
            game_state: Complete game state to evaluate
            
        Returns:
            Dictionary with position evaluation
        """
        # This would use the evaluator directly without MCTS
        # Implementation depends on requirements
        raise NotImplementedError("Position evaluation not yet implemented")
    
    def get_solver_info(self) -> Dict[str, Any]:
        """
        Get information about the solver configuration.
        
        Returns:
            Dictionary with solver information
        """
        return {
            'version': '2.0.0',
            'algorithm': 'MCTS',
            'threads': self.service.threads,
            'default_time_limit': self.service.default_time_limit,
            'features': [
                'initial_placement',
                'progressive_placement',
                'parallel_search',
                'transposition_table',
                'progressive_widening'
            ]
        }
    
    def update_configuration(self, **kwargs) -> Dict[str, Any]:
        """
        Update solver configuration.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            Dictionary with updated configuration
        """
        self.service.update_config(**kwargs)
        return self.get_solver_info()


# Factory function for creating solver instance
def create_ofc_solver(threads: int = 4,
                     time_limit: float = 30.0) -> OFCSolverAPI:
    """
    Create an OFC Solver instance.
    
    Args:
        threads: Number of threads for parallel MCTS
        time_limit: Default time limit for solving
        
    Returns:
        OFCSolverAPI instance
    """
    return OFCSolverAPI(threads=threads, default_time_limit=time_limit)


# Convenience functions for backward compatibility
def solve_initial_placement(cards: List[str],
                           time_limit: float = 30.0) -> Dict[str, str]:
    """
    Solve initial 5-card placement (backward compatibility).
    
    Args:
        cards: List of 5 cards
        time_limit: Time limit for solving
        
    Returns:
        Dictionary mapping cards to positions
    """
    solver = create_ofc_solver(time_limit=time_limit)
    result = solver.solve_initial_placement(cards, time_limit)
    return result['placement']