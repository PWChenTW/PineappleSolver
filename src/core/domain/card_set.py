"""
CardSet implementation using bit manipulation for high performance.

This module provides an efficient way to represent and manipulate sets of cards
using bitwise operations.
"""

from __future__ import annotations
from typing import List, Iterator, Set
from src.core.domain.card import Card


class CardSet:
    """
    Efficient card set representation using bit manipulation.
    
    Uses a 64-bit integer to represent presence/absence of cards,
    allowing for O(1) operations like union, intersection, and membership testing.
    """
    
    __slots__ = ('_bits',)
    
    def __init__(self, bits: int = 0):
        """Initialize with bit representation."""
        self._bits = bits
    
    @classmethod
    def from_cards(cls, cards: List[Card]) -> "CardSet":
        """Create CardSet from list of cards."""
        bits = 0
        for card in cards:
            bits |= (1 << card.value)
        return cls(bits)
    
    @classmethod
    def empty(cls) -> "CardSet":
        """Create empty card set."""
        return cls(0)
    
    @classmethod
    def full_deck(cls, include_jokers: bool = False) -> "CardSet":
        """Create a card set with all cards."""
        if include_jokers:
            # All 52 cards + joker
            return cls((1 << 53) - 1)
        else:
            # All 52 cards
            return cls((1 << 52) - 1)
    
    def add(self, card: Card) -> None:
        """Add a card to the set."""
        self._bits |= (1 << card.value)
    
    def remove(self, card: Card) -> None:
        """Remove a card from the set."""
        self._bits &= ~(1 << card.value)
    
    def discard(self, card: Card) -> None:
        """Remove a card if present (no error if not present)."""
        self.remove(card)
    
    def contains(self, card: Card) -> bool:
        """Check if card is in the set."""
        return bool(self._bits & (1 << card.value))
    
    def __contains__(self, card: Card) -> bool:
        """Support 'in' operator."""
        return self.contains(card)
    
    def union(self, other: "CardSet") -> "CardSet":
        """Return union of two card sets."""
        return CardSet(self._bits | other._bits)
    
    def intersection(self, other: "CardSet") -> "CardSet":
        """Return intersection of two card sets."""
        return CardSet(self._bits & other._bits)
    
    def difference(self, other: "CardSet") -> "CardSet":
        """Return cards in this set but not in other."""
        return CardSet(self._bits & ~other._bits)
    
    def symmetric_difference(self, other: "CardSet") -> "CardSet":
        """Return cards in either set but not in both."""
        return CardSet(self._bits ^ other._bits)
    
    def issubset(self, other: "CardSet") -> bool:
        """Check if this is a subset of other."""
        return (self._bits & other._bits) == self._bits
    
    def issuperset(self, other: "CardSet") -> bool:
        """Check if this is a superset of other."""
        return (self._bits | other._bits) == self._bits
    
    def isdisjoint(self, other: "CardSet") -> bool:
        """Check if sets have no common elements."""
        return (self._bits & other._bits) == 0
    
    def copy(self) -> "CardSet":
        """Create a copy of this card set."""
        return CardSet(self._bits)
    
    def clear(self) -> None:
        """Remove all cards."""
        self._bits = 0
    
    def __len__(self) -> int:
        """Count number of cards in set."""
        # Brian Kernighan's algorithm for counting set bits
        count = 0
        bits = self._bits
        while bits:
            bits &= bits - 1
            count += 1
        return count
    
    def __bool__(self) -> bool:
        """Check if set is non-empty."""
        return self._bits != 0
    
    def __iter__(self) -> Iterator[Card]:
        """Iterate over cards in the set."""
        bits = self._bits
        pos = 0
        while bits:
            if bits & 1:
                yield Card(pos)
            bits >>= 1
            pos += 1
    
    def to_list(self) -> List[Card]:
        """Convert to list of cards."""
        return list(self)
    
    def to_set(self) -> Set[Card]:
        """Convert to Python set."""
        return set(self)
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another CardSet."""
        if not isinstance(other, CardSet):
            return NotImplemented
        return self._bits == other._bits
    
    def __str__(self) -> str:
        """String representation of card set."""
        cards = [str(card) for card in self]
        return f"CardSet({', '.join(cards)})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"CardSet(bits={self._bits:b})"
    
    # Bitwise operations
    def __or__(self, other: "CardSet") -> "CardSet":
        """Union using | operator."""
        return self.union(other)
    
    def __and__(self, other: "CardSet") -> "CardSet":
        """Intersection using & operator."""
        return self.intersection(other)
    
    def __sub__(self, other: "CardSet") -> "CardSet":
        """Difference using - operator."""
        return self.difference(other)
    
    def __xor__(self, other: "CardSet") -> "CardSet":
        """Symmetric difference using ^ operator."""
        return self.symmetric_difference(other)
    
    # In-place operations
    def __ior__(self, other: "CardSet") -> "CardSet":
        """In-place union."""
        self._bits |= other._bits
        return self
    
    def __iand__(self, other: "CardSet") -> "CardSet":
        """In-place intersection."""
        self._bits &= other._bits
        return self
    
    def __isub__(self, other: "CardSet") -> "CardSet":
        """In-place difference."""
        self._bits &= ~other._bits
        return self
    
    def __ixor__(self, other: "CardSet") -> "CardSet":
        """In-place symmetric difference."""
        self._bits ^= other._bits
        return self
    
    @property
    def bits(self) -> int:
        """Get the raw bit representation."""
        return self._bits
    
    def pop(self) -> Card:
        """Remove and return an arbitrary card."""
        if not self._bits:
            raise KeyError("pop from empty CardSet")
        
        # Find the lowest set bit
        lowest_bit = self._bits & -self._bits
        pos = (lowest_bit - 1).bit_length()
        
        # Remove it
        self._bits &= ~lowest_bit
        
        return Card(pos)