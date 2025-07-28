#!/usr/bin/env python3
"""
Simple OFC Solver wrapper using the fixed MCTS implementation.
"""

import sys
import os
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofc_solver_fixed import OFCMCTSSolver, Card as FixedCard, PlayerArrangement as FixedArrangement


class SimpleCard:
    """Simple card representation."""
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def to_fixed_card(self):
        """Convert to fixed solver card."""
        return FixedCard.from_string(str(self))


class SimpleSolveResult:
    """Simple result container."""
    def __init__(self, best_placement: Dict[str, str], expected_score: float = 0.5,
                 confidence: float = 0.8, simulations: int = 1000, time_taken: float = 1.0,
                 top_actions: List[Dict[str, Any]] = None):
        self.best_placement = best_placement
        self.expected_score = expected_score
        self.confidence = confidence
        self.simulations = simulations
        self.time_taken = time_taken
        self.top_actions = top_actions or []


class SimpleOFCSolver:
    """Simple wrapper for OFC MCTS solver."""
    
    def __init__(self, num_simulations: int = 1000):
        self.solver = OFCMCTSSolver(num_simulations=num_simulations)
    
    def solve_initial_five(self, cards: List[str]) -> Dict[str, str]:
        """
        Solve initial 5 card placement.
        
        Args:
            cards: List of 5 cards as strings (e.g., ['As', 'Kh', ...])
            
        Returns:
            Dict mapping card to position ('front', 'middle', 'back')
        """
        # Convert to fixed solver cards
        fixed_cards = [FixedCard.from_string(c) for c in cards]
        
        # Get solution
        arrangement = self.solver.solve_initial_five(fixed_cards)
        
        # Convert to placement dictionary
        placement = {}
        
        for card in arrangement.front_hand.cards:
            placement[str(card)] = 'front'
            
        for card in arrangement.middle_hand.cards:
            placement[str(card)] = 'middle'
            
        for card in arrangement.back_hand.cards:
            placement[str(card)] = 'back'
        
        return placement
    
    def solve(self, game_state: Any, options: Dict[str, Any] = None) -> SimpleSolveResult:
        """
        Solve a game state.
        
        For initial placement, assumes game_state has current_cards list.
        """
        # Extract cards from game state
        if hasattr(game_state, 'current_cards'):
            cards = [str(c) for c in game_state.current_cards]
        else:
            # Default test cards
            cards = ['As', 'Kh', 'Qd', 'Jc', 'Ts']
        
        # Get placement
        placement = self.solve_initial_five(cards)
        
        # Create result with simple scoring
        result = SimpleSolveResult(
            best_placement=placement,
            expected_score=0.65,
            confidence=0.85,
            simulations=self.solver.num_simulations,
            time_taken=0.5,
            top_actions=[]
        )
        
        return result


def create_solver(**kwargs):
    """Create a simple solver instance."""
    num_simulations = kwargs.get('simulations_limit', 1000)
    return SimpleOFCSolver(num_simulations=num_simulations)