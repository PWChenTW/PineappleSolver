"""
Card domain model for OFC Solver.

This module implements the Card value object using optimized integer representation
for high-performance operations.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from enum import IntEnum


class Rank(IntEnum):
    """Card ranks with optimized integer values."""
    TWO = 0
    THREE = 1
    FOUR = 2
    FIVE = 3
    SIX = 4
    SEVEN = 5
    EIGHT = 6
    NINE = 7
    TEN = 8
    JACK = 9
    QUEEN = 10
    KING = 11
    ACE = 12
    
    @property
    def display(self) -> str:
        """Get display character for rank."""
        return "23456789TJQKA"[self.value]
    
    @classmethod
    def from_char(cls, char: str) -> "Rank":
        """Create rank from character."""
        char = char.upper()
        if char == 'T':
            return cls.TEN
        elif char == 'J':
            return cls.JACK
        elif char == 'Q':
            return cls.QUEEN
        elif char == 'K':
            return cls.KING
        elif char == 'A':
            return cls.ACE
        else:
            try:
                return cls(int(char) - 2)
            except ValueError:
                raise ValueError(f"Invalid rank character: {char}")


class Suit(IntEnum):
    """Card suits with optimized integer values."""
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    
    @property
    def display(self) -> str:
        """Get display character for suit."""
        return "♣♦♥♠"[self.value]
    
    @property
    def char(self) -> str:
        """Get single character representation."""
        return "cdhs"[self.value]
    
    @classmethod
    def from_char(cls, char: str) -> "Suit":
        """Create suit from character."""
        char = char.lower()
        if char in ('c', '♣'):
            return cls.CLUBS
        elif char in ('d', '♦'):
            return cls.DIAMONDS
        elif char in ('h', '♥'):
            return cls.HEARTS
        elif char in ('s', '♠'):
            return cls.SPADES
        else:
            raise ValueError(f"Invalid suit character: {char}")


class Card:
    """
    Immutable card representation using optimized integer encoding.
    
    The card is internally represented as a single integer (0-51) for standard cards,
    with special values for jokers. This allows for extremely fast operations
    and minimal memory usage.
    """
    
    __slots__ = ('_value',)
    
    # Special card values
    JOKER_VALUE = 52
    
    def __init__(self, value: int):
        """Initialize card with integer value."""
        if not (0 <= value <= 52):
            raise ValueError(f"Invalid card value: {value}")
        self._value = value
    
    @classmethod
    def from_rank_suit(cls, rank: Rank, suit: Suit) -> "Card":
        """Create card from rank and suit."""
        return cls(rank.value * 4 + suit.value)
    
    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """
        Create card from string representation.
        
        Examples: "As", "2h", "Tc", "Joker"
        """
        card_str = card_str.strip()
        
        if card_str.lower() == "joker":
            return cls(cls.JOKER_VALUE)
        
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank = Rank.from_char(card_str[0])
        suit = Suit.from_char(card_str[1])
        return cls.from_rank_suit(rank, suit)
    
    @classmethod
    def joker(cls) -> "Card":
        """Create a joker card."""
        return cls(cls.JOKER_VALUE)
    
    @property
    def value(self) -> int:
        """Get the integer value of the card."""
        return self._value
    
    @property
    def is_joker(self) -> bool:
        """Check if this is a joker."""
        return self._value == self.JOKER_VALUE
    
    @property
    def rank(self) -> Optional[Rank]:
        """Get the rank of the card (None for joker)."""
        if self.is_joker:
            return None
        return Rank(self._value // 4)
    
    @property
    def suit(self) -> Optional[Suit]:
        """Get the suit of the card (None for joker)."""
        if self.is_joker:
            return None
        return Suit(self._value % 4)
    
    @property
    def rank_value(self) -> int:
        """Get rank as integer (0-12, or 13 for joker)."""
        if self.is_joker:
            return 13
        return self._value // 4
    
    @property
    def suit_value(self) -> int:
        """Get suit as integer (0-3, or -1 for joker)."""
        if self.is_joker:
            return -1
        return self._value % 4
    
    def __str__(self) -> str:
        """String representation of card."""
        if self.is_joker:
            return "Joker"
        return f"{self.rank.display}{self.suit.char}"
    
    def __repr__(self) -> str:
        """Developer representation of card."""
        return f"Card({self._value})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another card."""
        if not isinstance(other, Card):
            return NotImplemented
        return self._value == other._value
    
    def __lt__(self, other: "Card") -> bool:
        """Compare cards by rank (suit is ignored)."""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank_value < other.rank_value
    
    def __hash__(self) -> int:
        """Hash value for use in sets and dicts."""
        return self._value
    
    @classmethod
    def all_cards(cls, include_jokers: bool = False) -> List["Card"]:
        """Generate all standard cards."""
        cards = [cls(i) for i in range(52)]
        if include_jokers:
            cards.append(cls.joker())
        return cards
    
    @classmethod
    def deck(cls, num_jokers: int = 0) -> List["Card"]:
        """Create a standard deck of cards."""
        deck = cls.all_cards(include_jokers=False)
        deck.extend([cls.joker() for _ in range(num_jokers)])
        return deck
    
    def to_bit(self) -> int:
        """Convert to bit position for bitset operations."""
        return 1 << self._value