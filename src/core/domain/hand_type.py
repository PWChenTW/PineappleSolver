"""
Hand type definitions and ranking for OFC.

This module defines all possible hand types and their relative rankings.
"""

from enum import IntEnum
from typing import List, Tuple, Optional


class HandCategory(IntEnum):
    """Categories of poker hands from lowest to highest."""
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9
    
    @property
    def display_name(self) -> str:
        """Get human-readable name."""
        names = {
            self.HIGH_CARD: "High Card",
            self.PAIR: "Pair",
            self.TWO_PAIR: "Two Pair",
            self.THREE_OF_A_KIND: "Three of a Kind",
            self.STRAIGHT: "Straight",
            self.FLUSH: "Flush",
            self.FULL_HOUSE: "Full House",
            self.FOUR_OF_A_KIND: "Four of a Kind",
            self.STRAIGHT_FLUSH: "Straight Flush",
            self.ROYAL_FLUSH: "Royal Flush"
        }
        return names[self]
    
    def is_valid_for_front(self) -> bool:
        """Check if this hand type is valid for front hand (3 cards)."""
        return self in (self.HIGH_CARD, self.PAIR, self.THREE_OF_A_KIND)


class HandType:
    """
    Complete hand type representation including category and tiebreakers.
    
    The hand type includes:
    - Category (e.g., FLUSH, FULL_HOUSE)
    - Primary rank (e.g., rank of three cards in full house)
    - Secondary rank (e.g., rank of pair in full house)
    - Kickers (remaining cards for tiebreaking)
    """
    
    __slots__ = ('category', 'primary_rank', 'secondary_rank', 'kickers')
    
    def __init__(self, 
                 category: HandCategory,
                 primary_rank: int,
                 secondary_rank: Optional[int] = None,
                 kickers: Optional[List[int]] = None):
        """
        Initialize hand type.
        
        Args:
            category: The hand category
            primary_rank: Main rank for comparison (0-12 for 2-A)
            secondary_rank: Secondary rank for two pair, full house
            kickers: List of kicker ranks for tiebreaking
        """
        self.category = category
        self.primary_rank = primary_rank
        self.secondary_rank = secondary_rank
        self.kickers = kickers or []
    
    def __lt__(self, other: "HandType") -> bool:
        """Compare hand types for ordering."""
        # First compare by category
        if self.category != other.category:
            return self.category < other.category
        
        # Then by primary rank
        if self.primary_rank != other.primary_rank:
            return self.primary_rank < other.primary_rank
        
        # Then by secondary rank (if applicable)
        if self.secondary_rank is not None and other.secondary_rank is not None:
            if self.secondary_rank != other.secondary_rank:
                return self.secondary_rank < other.secondary_rank
        
        # Finally by kickers
        for k1, k2 in zip(self.kickers, other.kickers):
            if k1 != k2:
                return k1 < k2
        
        return False
    
    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, HandType):
            return NotImplemented
        
        return (self.category == other.category and
                self.primary_rank == other.primary_rank and
                self.secondary_rank == other.secondary_rank and
                self.kickers == other.kickers)
    
    def __str__(self) -> str:
        """String representation."""
        rank_names = "23456789TJQKA"
        
        if self.category == HandCategory.HIGH_CARD:
            kicker_str = "".join(rank_names[k] for k in self.kickers[:5])
            return f"High Card: {kicker_str}"
        
        elif self.category == HandCategory.PAIR:
            pair_rank = rank_names[self.primary_rank]
            kicker_str = "".join(rank_names[k] for k in self.kickers[:3])
            return f"Pair of {pair_rank}s ({kicker_str})"
        
        elif self.category == HandCategory.TWO_PAIR:
            high_pair = rank_names[self.primary_rank]
            low_pair = rank_names[self.secondary_rank]
            kicker = rank_names[self.kickers[0]] if self.kickers else ""
            return f"Two Pair: {high_pair}s and {low_pair}s ({kicker})"
        
        elif self.category == HandCategory.THREE_OF_A_KIND:
            trips_rank = rank_names[self.primary_rank]
            kicker_str = "".join(rank_names[k] for k in self.kickers[:2])
            return f"Three {trips_rank}s ({kicker_str})"
        
        elif self.category == HandCategory.STRAIGHT:
            high_rank = rank_names[self.primary_rank]
            # Special case for A-5 straight
            if self.primary_rank == 3:  # 5-high straight
                return "Straight: A-5"
            return f"Straight: {high_rank}-high"
        
        elif self.category == HandCategory.FLUSH:
            kicker_str = "".join(rank_names[k] for k in [self.primary_rank] + self.kickers[:4])
            return f"Flush: {kicker_str}"
        
        elif self.category == HandCategory.FULL_HOUSE:
            trips = rank_names[self.primary_rank]
            pair = rank_names[self.secondary_rank]
            return f"Full House: {trips}s full of {pair}s"
        
        elif self.category == HandCategory.FOUR_OF_A_KIND:
            quads = rank_names[self.primary_rank]
            kicker = rank_names[self.kickers[0]] if self.kickers else ""
            return f"Four {quads}s ({kicker})"
        
        elif self.category == HandCategory.STRAIGHT_FLUSH:
            high_rank = rank_names[self.primary_rank]
            # Special case for A-5 straight flush
            if self.primary_rank == 3:  # 5-high straight
                return "Straight Flush: A-5"
            return f"Straight Flush: {high_rank}-high"
        
        else:  # ROYAL_FLUSH
            return "Royal Flush"
    
    def strength_value(self) -> int:
        """
        Get a single integer representing hand strength.
        
        Used for fast comparison and caching.
        Higher values are better hands.
        """
        # Category is most significant (multiply by large factor)
        value = self.category.value * 1000000
        
        # Primary rank
        value += self.primary_rank * 10000
        
        # Secondary rank (if applicable)
        if self.secondary_rank is not None:
            value += self.secondary_rank * 100
        
        # Kickers (limited precision)
        for i, kicker in enumerate(self.kickers[:2]):
            value += kicker * (10 // (i + 1))
        
        return value