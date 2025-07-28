"""
Data Transfer Objects for application layer.

Provides clean interfaces between API and core domains.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from src.core.domain import Card, GameState, Street
from src.core.algorithms.mcts_node import Action


@dataclass
class CardDTO:
    """Simple card representation using string format."""
    card_str: str  # e.g., "As", "Kh", "2c"
    
    def to_domain(self) -> Card:
        """Convert to domain Card object."""
        return Card.from_string(self.card_str)
    
    @classmethod
    def from_domain(cls, card: Card) -> 'CardDTO':
        """Create from domain Card object."""
        return cls(card_str=str(card))


@dataclass
class PlacementDTO:
    """Card placement representation."""
    card: str  # e.g., "As"
    position: str  # "front", "middle", "back"
    index: int  # 0-based index
    
    def to_tuple(self) -> Tuple[Card, str, int]:
        """Convert to placement tuple."""
        return (Card.from_string(self.card), self.position, self.index)


@dataclass
class SolveRequestDTO:
    """Request for solving initial 5-card placement."""
    cards: List[str]  # List of 5 card strings
    time_limit: float = 30.0
    num_threads: int = 4
    
    def validate(self) -> None:
        """Validate request data."""
        if len(self.cards) != 5:
            raise ValueError(f"Expected 5 cards, got {len(self.cards)}")
        
        # Validate card format
        for card_str in self.cards:
            try:
                Card.from_string(card_str)
            except ValueError as e:
                raise ValueError(f"Invalid card format '{card_str}': {e}")
        
        # Check for duplicates
        if len(set(self.cards)) != len(self.cards):
            raise ValueError("Duplicate cards detected")
        
        if self.time_limit <= 0:
            raise ValueError("Time limit must be positive")
        
        if self.num_threads < 1 or self.num_threads > 32:
            raise ValueError("Number of threads must be between 1 and 32")


@dataclass
class SolveResultDTO:
    """Result from solving request."""
    placements: List[PlacementDTO]
    evaluation: float
    confidence: float
    visit_count: int
    computation_time: float
    statistics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'placements': [
                {
                    'card': p.card,
                    'position': p.position,
                    'index': p.index
                }
                for p in self.placements
            ],
            'evaluation': self.evaluation,
            'confidence': self.confidence,
            'visit_count': self.visit_count,
            'computation_time': self.computation_time,
            'statistics': self.statistics
        }


class DTOConverter:
    """Converter between DTOs and domain objects."""
    
    def create_initial_game_state(self, cards: List[str]) -> GameState:
        """Create game state with initial 5 cards."""
        # Create new game state
        game_state = GameState(
            num_players=2,
            player_index=0,
            num_jokers=0
        )
        
        # Convert cards to domain objects
        domain_cards = [Card.from_string(card_str) for card_str in cards]
        
        # Set the current hand directly (simulating dealt cards)
        game_state._current_hand = domain_cards
        
        return game_state
    
    def action_to_placements(self, action: Action) -> List[PlacementDTO]:
        """Convert MCTS action to placement DTOs."""
        placements = []
        
        for card, position, index in action.placements:
            placements.append(PlacementDTO(
                card=str(card),
                position=position,
                index=index
            ))
        
        return placements
    
    def extract_statistics(self, engine_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant statistics from MCTS engine."""
        return {
            'total_simulations': engine_stats.get('simulations', 0),
            'nodes_evaluated': engine_stats.get('nodes_evaluated', 0),
            'config': {
                'time_limit': engine_stats.get('config', {}).time_limit,
                'num_threads': engine_stats.get('config', {}).num_threads,
                'c_puct': engine_stats.get('config', {}).c_puct
            }
        }


# Global converter instance
converter = DTOConverter()