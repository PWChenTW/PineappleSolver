"""
OFC Solver v2 - Clean Architecture Implementation.

This module provides a facade for the OFC Solver with clean architecture,
maintaining backward compatibility while using the new structured approach.
"""

from typing import List, Dict, Any, Optional

# Import the new API
from src.api.ofc_solver_api import (
    OFCSolverAPI,
    create_ofc_solver as create_api_solver,
    solve_initial_placement as api_solve_initial
)

# Re-export main components for backward compatibility
from src.api.dto import SolveResultDTO as SolveResult


class OFCSolver:
    """
    OFC Solver main class (facade pattern).
    
    This class provides backward compatibility while delegating
    to the new clean architecture implementation.
    """
    
    def __init__(self, 
                 threads: int = 4,
                 time_limit: float = 30.0,
                 simulations_limit: Optional[int] = None):
        """Initialize OFC Solver."""
        self.api = OFCSolverAPI(threads=threads, default_time_limit=time_limit)
        self.threads = threads
        self.time_limit = time_limit
        self.simulations_limit = simulations_limit
    
    def solve(self, game_state: Any, 
              options: Optional[Dict[str, Any]] = None) -> Any:
        """
        Solve OFC position.
        
        Args:
            game_state: Game state (supports both old and new formats)
            options: Additional options
            
        Returns:
            Solve result
        """
        # Handle old GameState format
        if hasattr(game_state, 'to_dict'):
            game_state_dict = game_state.to_dict()
        elif hasattr(game_state, 'current_cards'):
            # Old simple GameState
            game_state_dict = {
                'current_cards': [str(c) for c in game_state.current_cards],
                'front_hand': [str(c) for c in game_state.front_hand],
                'middle_hand': [str(c) for c in game_state.middle_hand],
                'back_hand': [str(c) for c in game_state.back_hand],
                'remaining_cards': game_state.remaining_cards
            }
        else:
            game_state_dict = game_state
        
        # Extract options
        time_limit = self.time_limit
        simulations_limit = self.simulations_limit
        
        if options:
            time_limit = options.get('time_limit', time_limit)
            simulations_limit = options.get('simulations_limit', simulations_limit)
        
        # Solve using API
        result_dict = self.api.solve_position(
            game_state_dict,
            time_limit=time_limit,
            simulations_limit=simulations_limit
        )
        
        # Convert to SolveResult for backward compatibility
        return self._dict_to_solve_result(result_dict)
    
    def solve_initial_placement(self, cards: List[Any]) -> Dict[str, str]:
        """
        Solve initial 5-card placement.
        
        Args:
            cards: List of 5 cards (can be Card objects or strings)
            
        Returns:
            Dictionary mapping cards to positions
        """
        # Convert cards to strings if needed
        card_strings = []
        for card in cards:
            if isinstance(card, str):
                card_strings.append(card)
            else:
                # Assume it has rank and suit attributes
                card_strings.append(f"{card.rank}{card.suit}")
        
        # Solve using API
        result = self.api.solve_initial_placement(card_strings, self.time_limit)
        return result['placement']
    
    def _dict_to_solve_result(self, result_dict: Dict[str, Any]) -> SolveResult:
        """Convert dictionary result to SolveResult object."""
        # Create placement dictionary from placements list
        best_placement = {}
        for placement in result_dict['best_placements']:
            best_placement[placement['card']] = placement['position']
        
        # Create top actions list
        top_actions = []
        for action in result_dict.get('top_actions', []):
            top_actions.append({
                'card': action['placement']['card'],
                'position': action['placement']['position'],
                'visits': action['visits'],
                 'avg_reward': action['average_reward']
            })
        
        from src.api.dto import SolveResultDTO, PlacementDTO, ActionStatDTO
        
        # Convert back to DTO (this is a bit circular but maintains compatibility)
        placements = [
            PlacementDTO(card=p['card'], position=p['position']) 
            for p in result_dict['best_placements']
        ]
        
        return SolveResultDTO(
            best_placements=placements,
            discard=result_dict.get('discard'),
            expected_score=result_dict['expected_score'],
            confidence=result_dict['confidence'],
            simulations_count=result_dict['simulations_count'],
            time_taken=result_dict['time_taken'],
            top_actions=[]  # Simplified for now
        )


def create_solver(**kwargs) -> OFCSolver:
    """Create OFC Solver instance."""
    return OFCSolver(**kwargs)


# For direct initial placement solving
def solve_initial_placement(cards: List[str], **kwargs) -> Dict[str, str]:
    """
    Direct function to solve initial placement.
    
    Args:
        cards: List of 5 cards as strings
        **kwargs: Additional options
        
    Returns:
        Dictionary mapping cards to positions
    """
    time_limit = kwargs.get('time_limit', 30.0)
    return api_solve_initial(cards, time_limit)


__all__ = [
    'OFCSolver',
    'create_solver',
    'solve_initial_placement',
    'SolveResult'
]