"""
Card representation for OFC Solver with enhanced error handling.

Provides an efficient, immutable card implementation with comprehensive validation.
"""

from __future__ import annotations
from enum import IntEnum
from typing import List, Optional

from src.exceptions import InvalidInputError


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
        """
        Create rank from character with validation.
        
        Args:
            char: Character representing rank ('2'-'9', 'T', 'J', 'Q', 'K', 'A')
            
        Returns:
            Rank instance
            
        Raises:
            InvalidInputError: If character is invalid
        """
        if not isinstance(char, str) or len(char) != 1:
            raise InvalidInputError(
                "Rank must be a single character",
                input_value=char,
                expected_format="Single character: 2-9, T, J, Q, K, A"
            )
        
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
        elif char in '23456789':
            try:
                return cls(int(char) - 2)
            except ValueError:
                pass
        
        raise InvalidInputError(
            f"Invalid rank character: '{char}'",
            input_value=char,
            valid_chars="2-9, T, J, Q, K, A"
        )


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
        """
        Create suit from character with validation.
        
        Args:
            char: Character representing suit ('c', 'd', 'h', 's' or symbols)
            
        Returns:
            Suit instance
            
        Raises:
            InvalidInputError: If character is invalid
        """
        if not isinstance(char, str) or len(char) != 1:
            raise InvalidInputError(
                "Suit must be a single character",
                input_value=char,
                expected_format="c, d, h, s (or ♣, ♦, ♥, ♠)"
            )
        
        char_lower = char.lower()
        if char_lower == 'c' or char == '♣':
            return cls.CLUBS
        elif char_lower == 'd' or char == '♦':
            return cls.DIAMONDS
        elif char_lower == 'h' or char == '♥':
            return cls.HEARTS
        elif char_lower == 's' or char == '♠':
            return cls.SPADES
        else:
            raise InvalidInputError(
                f"Invalid suit character: '{char}'",
                input_value=char,
                valid_chars="c, d, h, s (or ♣, ♦, ♥, ♠)"
            )


class Card:
    """
    Immutable card representation with error handling.
    
    The card is internally represented as a single integer (0-51) for standard cards,
    with special values for jokers. This allows for extremely fast operations
    and minimal memory usage.
    """
    
    __slots__ = ('_value',)
    
    # Special card values
    JOKER_VALUE = 52
    
    def __init__(self, value: int):
        """
        Initialize card with integer value.
        
        Args:
            value: Integer value (0-52)
            
        Raises:
            InvalidInputError: If value is out of range
        """
        if not isinstance(value, int):
            raise InvalidInputError(
                "Card value must be an integer",
                input_value=type(value).__name__,
                expected_type="int"
            )
        
        if not (0 <= value <= 52):
            raise InvalidInputError(
                f"Card value must be between 0 and 52",
                input_value=value,
                valid_range="0-52"
            )
        
        self._value = value
    
    @classmethod
    def from_rank_suit(cls, rank: Rank, suit: Suit) -> "Card":
        """
        Create card from rank and suit with validation.
        
        Args:
            rank: Card rank
            suit: Card suit
            
        Returns:
            Card instance
            
        Raises:
            InvalidInputError: If inputs are invalid
        """
        if not isinstance(rank, Rank):
            raise InvalidInputError(
                "rank must be a Rank instance",
                input_value=type(rank).__name__,
                expected_type="Rank"
            )
        
        if not isinstance(suit, Suit):
            raise InvalidInputError(
                "suit must be a Suit instance",
                input_value=type(suit).__name__,
                expected_type="Suit"
            )
        
        return cls(rank.value * 4 + suit.value)
    
    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """
        Create card from string representation with validation.
        
        Examples: "As", "2h", "Tc", "JOKER"
        
        Args:
            card_str: String representation of card
            
        Returns:
            Card instance
            
        Raises:
            InvalidInputError: If string format is invalid
        """
        if not isinstance(card_str, str):
            raise InvalidInputError(
                "Card string must be a string",
                input_value=type(card_str).__name__,
                expected_type="str"
            )
        
        card_str = card_str.strip()
        
        if not card_str:
            raise InvalidInputError(
                "Card string cannot be empty",
                input_value=card_str
            )
        
        if card_str.upper() == "JOKER":
            return cls(cls.JOKER_VALUE)
        
        if len(card_str) != 2:
            raise InvalidInputError(
                f"Card string must be 2 characters (e.g., 'AS', '2H')",
                input_value=card_str,
                length=len(card_str),
                expected_format="[Rank][Suit]"
            )
        
        try:
            rank = Rank.from_char(card_str[0])
            suit = Suit.from_char(card_str[1])
            return cls.from_rank_suit(rank, suit)
        except InvalidInputError as e:
            # Re-raise with more context
            e.details['card_string'] = card_str
            raise
    
    @property
    def rank(self) -> Optional[Rank]:
        """Get card rank (None for joker)."""
        if self._value == self.JOKER_VALUE:
            return None
        return Rank(self._value // 4)
    
    @property
    def suit(self) -> Optional[Suit]:
        """Get card suit (None for joker)."""
        if self._value == self.JOKER_VALUE:
            return None
        return Suit(self._value % 4)
    
    @property
    def is_joker(self) -> bool:
        """Check if card is a joker."""
        return self._value == self.JOKER_VALUE
    
    @property
    def value(self) -> int:
        """Get internal integer value."""
        return self._value
    
    @property
    def rank_value(self) -> int:
        """Get rank as integer value (for sorting/comparison)."""
        if self.is_joker:
            return Rank.ACE.value  # Joker treated as Ace for ranking
        return self.rank.value
    
    @property
    def suit_value(self) -> int:
        """Get suit as integer value."""
        if self.is_joker:
            return 0  # Default suit value for joker
        return self.suit.value
    
    def __str__(self) -> str:
        """String representation of card."""
        if self.is_joker:
            return "Joker"
        return f"{self.rank.display}{self.suit.char.upper()}"
    
    def __repr__(self) -> str:
        """Debug representation of card."""
        return f"Card('{self}')"
    
    def __eq__(self, other) -> bool:
        """Check equality with other card."""
        if not isinstance(other, Card):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        """Hash value for use in sets/dicts."""
        return self._value
    
    def __lt__(self, other) -> bool:
        """Compare cards by value (for sorting)."""
        if not isinstance(other, Card):
            raise TypeError(f"Cannot compare Card with {type(other).__name__}")
        return self._value < other._value
    
    @classmethod
    def deck(cls, num_jokers: int = 0) -> List["Card"]:
        """
        Create a standard deck of cards with validation.
        
        Args:
            num_jokers: Number of jokers to include (0-2)
            
        Returns:
            List of Card instances
            
        Raises:
            InvalidInputError: If num_jokers is invalid
        """
        if not isinstance(num_jokers, int):
            raise InvalidInputError(
                "Number of jokers must be an integer",
                input_value=type(num_jokers).__name__,
                expected_type="int"
            )
        
        if num_jokers < 0 or num_jokers > 2:
            raise InvalidInputError(
                "Number of jokers must be between 0 and 2",
                input_value=num_jokers,
                valid_range="0-2"
            )
        
        deck = [cls(i) for i in range(52)]
        deck.extend([cls(cls.JOKER_VALUE) for _ in range(num_jokers)])
        return deck
    
    def to_dict(self) -> dict:
        """
        Convert card to dictionary representation.
        
        Returns:
            Dictionary with card data
        """
        if self.is_joker:
            return {"type": "joker", "value": self._value}
        else:
            return {
                "type": "standard",
                "rank": self.rank.name,
                "suit": self.suit.name,
                "value": self._value,
                "string": str(self)
            }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        """
        Create card from dictionary representation.
        
        Args:
            data: Dictionary with card data
            
        Returns:
            Card instance
            
        Raises:
            InvalidInputError: If data is invalid
        """
        if not isinstance(data, dict):
            raise InvalidInputError(
                "Card data must be a dictionary",
                input_value=type(data).__name__,
                expected_type="dict"
            )
        
        try:
            if data.get("type") == "joker":
                return cls(cls.JOKER_VALUE)
            elif data.get("type") == "standard":
                if "string" in data:
                    return cls.from_string(data["string"])
                elif "rank" in data and "suit" in data:
                    rank = Rank[data["rank"]]
                    suit = Suit[data["suit"]]
                    return cls.from_rank_suit(rank, suit)
                elif "value" in data:
                    return cls(data["value"])
            
            raise InvalidInputError(
                "Invalid card data format",
                data=data,
                expected_keys="type, and (string OR rank+suit OR value)"
            )
            
        except (KeyError, ValueError) as e:
            raise InvalidInputError(
                f"Failed to create card from dict: {e}",
                data=data,
                error=str(e)
            )