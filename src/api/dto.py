"""
Data Transfer Objects for OFC Solver API.

This module defines the DTOs used for API communication,
providing a clear boundary between external API and internal domain.
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class CardDTO:
    """Card representation for API."""
    
    def __init__(self, card_str: str):
        """
        Initialize from string representation.
        
        Args:
            card_str: Card string like "As", "Kh", "2c"
        """
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        self.rank = card_str[0]
        self.suit = card_str[1]
        self.card_str = card_str
    
    def __str__(self):
        return self.card_str
    
    @classmethod
    def from_domain(cls, domain_card) -> 'CardDTO':
        """Create from domain Card object."""
        rank_str = domain_card.rank.value
        suit_str = domain_card.suit.value
        return cls(f"{rank_str}{suit_str}")


@dataclass
class GameStateDTO:
    """Game state for API communication."""
    current_cards: List[str]  # Current hand as strings
    front_hand: List[str] = field(default_factory=list)
    middle_hand: List[str] = field(default_factory=list)
    back_hand: List[str] = field(default_factory=list)
    remaining_cards: int = 0
    current_street: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'current_cards': self.current_cards,
            'front_hand': self.front_hand,
            'middle_hand': self.middle_hand,
            'back_hand': self.back_hand,
            'remaining_cards': self.remaining_cards,
            'current_street': self.current_street
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameStateDTO':
        """Create from dictionary."""
        return cls(
            current_cards=data.get('current_cards', []),
            front_hand=data.get('front_hand', []),
            middle_hand=data.get('middle_hand', []),
            back_hand=data.get('back_hand', []),
            remaining_cards=data.get('remaining_cards', 0),
            current_street=data.get('current_street')
        )


@dataclass
class SolveRequestDTO:
    """Request for solving OFC position."""
    game_state: GameStateDTO
    time_limit: Optional[float] = None
    simulations_limit: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SolveRequestDTO':
        """Create from dictionary."""
        return cls(
            game_state=GameStateDTO.from_dict(data['game_state']),
            time_limit=data.get('time_limit'),
            simulations_limit=data.get('simulations_limit')
        )


@dataclass
class PlacementDTO:
    """Card placement information."""
    card: str
    position: str  # 'front', 'middle', 'back'
    index: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {
            'card': self.card,
            'position': self.position
        }
        if self.index is not None:
            result['index'] = self.index
        return result


@dataclass
class ActionStatDTO:
    """Statistics for a single action."""
    placement: PlacementDTO
    visits: int
    average_reward: float
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'placement': self.placement.to_dict(),
            'visits': self.visits,
            'average_reward': self.average_reward,
            'confidence': self.confidence
        }


@dataclass
class SolveResultDTO:
    """Result from OFC solver."""
    best_placements: List[PlacementDTO]
    discard: Optional[str] = None
    expected_score: float = 0.0
    confidence: float = 0.0
    simulations_count: int = 0
    time_taken: float = 0.0
    top_actions: List[ActionStatDTO] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON response."""
        result = {
            'best_placements': [p.to_dict() for p in self.best_placements],
            'expected_score': self.expected_score,
            'confidence': self.confidence,
            'simulations_count': self.simulations_count,
            'time_taken': self.time_taken,
            'top_actions': [a.to_dict() for a in self.top_actions]
        }
        if self.discard:
            result['discard'] = self.discard
        return result


@dataclass
class InitialPlacementRequestDTO:
    """Request for initial 5-card placement."""
    cards: List[str]  # Exactly 5 cards
    time_limit: Optional[float] = None
    
    def validate(self):
        """Validate the request."""
        if len(self.cards) != 5:
            raise ValueError(f"Initial placement requires exactly 5 cards, got {len(self.cards)}")
        
        # Validate card format
        for card in self.cards:
            if len(card) != 2:
                raise ValueError(f"Invalid card format: {card}")
            if card[0] not in '23456789TJQKA':
                raise ValueError(f"Invalid rank: {card[0]}")
            if card[1] not in 'shdc':
                raise ValueError(f"Invalid suit: {card[1]}")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InitialPlacementRequestDTO':
        """Create from dictionary."""
        return cls(
            cards=data['cards'],
            time_limit=data.get('time_limit')
        )