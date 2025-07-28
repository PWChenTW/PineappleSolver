"""
Game state management for OFC Solver with enhanced error handling.

This module manages the complete game state including deck, streets,
and player arrangements with comprehensive validation and error recovery.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass
from enum import IntEnum
import random

from src.core.domain.card import Card
from src.core.domain.card_set import CardSet
from src.core.domain.player_arrangement import PlayerArrangement
from src.exceptions import (
    InvalidInputError, GameRuleViolationError, StateError,
    invalid_card_error, duplicate_card_error, invalid_placement_error
)


class Street(IntEnum):
    """Game streets in Pineapple OFC."""
    INITIAL = 0  # 5 cards, place all
    FIRST = 1    # 3 cards, place 2, discard 1
    SECOND = 2   # 3 cards, place 2, discard 1
    THIRD = 3    # 3 cards, place 2, discard 1
    FOURTH = 4   # 3 cards, place 2, discard 1
    COMPLETE = 5 # Game complete


@dataclass
class StreetAction:
    """Action taken in a street."""
    street: Street
    cards_dealt: List[Card]
    cards_placed: List[Tuple[Card, str, int]]  # (card, position, index)
    card_discarded: Optional[Card] = None


class GameState:
    """
    Complete game state for OFC with error handling.
    
    Tracks the deck, current street, player arrangement,
    and all actions taken with comprehensive validation.
    """
    
    def __init__(self, 
                 num_players: int = 2,
                 player_index: int = 0,
                 num_jokers: int = 0,
                 seed: Optional[int] = None):
        """
        Initialize game state with validation.
        
        Args:
            num_players: Number of players in the game
            player_index: Index of the player we're solving for
            num_jokers: Number of jokers in the deck
            seed: Random seed for reproducibility
            
        Raises:
            InvalidInputError: If parameters are invalid
        """
        # Validate inputs
        if num_players < 2 or num_players > 4:
            raise InvalidInputError(
                "Number of players must be between 2 and 4",
                input_value=num_players,
                valid_range="2-4"
            )
        
        if player_index < 0 or player_index >= num_players:
            raise InvalidInputError(
                "Player index out of range",
                input_value=player_index,
                valid_range=f"0-{num_players-1}"
            )
        
        if num_jokers < 0 or num_jokers > 2:
            raise InvalidInputError(
                "Number of jokers must be between 0 and 2",
                input_value=num_jokers,
                valid_range="0-2"
            )
        
        self.num_players = num_players
        self.player_index = player_index
        self.num_jokers = num_jokers
        
        # Initialize deck
        try:
            self._deck = Card.deck(num_jokers)
            self._remaining_deck = CardSet.from_cards(self._deck)
        except Exception as e:
            raise InvalidInputError(
                f"Failed to create deck: {e}",
                num_jokers=num_jokers
            )
        
        # Initialize RNG
        self._rng = random.Random(seed)
        if seed is not None:
            self._rng.shuffle(self._deck)
        
        # Game state
        self._current_street = Street.INITIAL
        self._player_arrangement = PlayerArrangement()
        self._opponent_used_cards = CardSet.empty()
        self._actions: List[StreetAction] = []
        
        # Cards currently in hand (dealt but not yet placed)
        self._current_hand: List[Card] = []
    
    @property
    def current_street(self) -> Street:
        """Get current street."""
        return self._current_street
    
    @property
    def player_arrangement(self) -> PlayerArrangement:
        """Get player's arrangement."""
        return self._player_arrangement
    
    @property
    def opponent_used_cards(self) -> CardSet:
        """Get cards used by opponents."""
        return self._opponent_used_cards.copy()
    
    @property
    def remaining_cards(self) -> CardSet:
        """Get cards remaining in deck."""
        used = self._player_arrangement.used_cards | self._opponent_used_cards
        return self._remaining_deck - used
    
    @property
    def current_hand(self) -> List[Card]:
        """Get cards currently in hand."""
        return self._current_hand.copy()
    
    @property
    def is_complete(self) -> bool:
        """Check if game is complete."""
        return self._current_street == Street.COMPLETE
    
    def deal_street(self) -> List[Card]:
        """
        Deal cards for the current street with validation.
        
        Returns:
            List of cards dealt
            
        Raises:
            StateError: If game state doesn't allow dealing
            GameRuleViolationError: If not enough cards available
        """
        if self._current_street == Street.COMPLETE:
            raise StateError(
                "Cannot deal cards in completed game",
                current_state="COMPLETE",
                expected_state="IN_PROGRESS"
            )
        
        if self._current_hand:
            raise StateError(
                "Cannot deal new cards with unresolved hand",
                current_state="HAND_PENDING",
                expected_state="HAND_EMPTY",
                cards_in_hand=len(self._current_hand)
            )
        
        # Determine number of cards to deal
        if self._current_street == Street.INITIAL:
            num_cards = 5
        else:
            num_cards = 3
        
        # Get available cards
        available = self.remaining_cards.to_list()
        required_cards = num_cards * self.num_players
        
        if len(available) < required_cards:
            raise GameRuleViolationError(
                f"Not enough cards remaining to deal street {self._current_street.name}",
                rule_violated="insufficient_cards",
                cards_available=len(available),
                cards_required=required_cards
            )
        
        try:
            # Shuffle and deal
            self._rng.shuffle(available)
            
            # Deal to all players
            all_dealt = []
            for i in range(self.num_players):
                player_cards = available[i*num_cards:(i+1)*num_cards]
                all_dealt.extend(player_cards)
                
                if i == self.player_index:
                    self._current_hand = player_cards
                else:
                    # Mark opponent cards as used
                    for card in player_cards:
                        self._opponent_used_cards.add(card)
            
            return self._current_hand.copy()
            
        except Exception as e:
            raise GameRuleViolationError(
                f"Failed to deal cards: {e}",
                rule_violated="deal_error",
                street=self._current_street.name
            )
    
    def place_cards(self,
                    placements: List[Tuple[Card, str, int]],
                    discard: Optional[Card] = None) -> None:
        """
        Place cards and advance to next street with comprehensive validation.
        
        Args:
            placements: List of (card, position, index) tuples
            discard: Card to discard (required after initial street)
            
        Raises:
            StateError: If game state doesn't allow placement
            InvalidInputError: If inputs are invalid
            GameRuleViolationError: If placement violates game rules
        """
        # State validation
        if self.is_complete:
            raise StateError(
                "Cannot place cards in completed game",
                current_state="COMPLETE",
                expected_state="IN_PROGRESS"
            )
        
        if not self._current_hand:
            raise StateError(
                "No cards in hand to place",
                current_state="NO_HAND",
                expected_state="HAS_HAND"
            )
        
        # Validate placement count
        if self._current_street == Street.INITIAL:
            expected_placements = 5
            expected_discard = False
        else:
            expected_placements = 2
            expected_discard = True
        
        if len(placements) != expected_placements:
            raise InvalidInputError(
                f"Expected {expected_placements} placements for street {self._current_street.name}",
                input_value=len(placements),
                expected=expected_placements
            )
        
        if expected_discard and discard is None:
            raise InvalidInputError(
                f"Discard required for street {self._current_street.name}",
                street=self._current_street.name
            )
        
        if not expected_discard and discard is not None:
            raise InvalidInputError(
                f"No discard allowed for street {self._current_street.name}",
                street=self._current_street.name,
                discard=str(discard)
            )
        
        # Validate all cards are from hand
        placed_cards = [p[0] for p in placements]
        if discard:
            placed_cards.append(discard)
        
        for card in placed_cards:
            validated_card = validate_card(card)
            if validated_card not in self._current_hand:
                raise GameRuleViolationError(
                    f"Card {validated_card} is not in current hand",
                    rule_violated="card_not_in_hand",
                    card=str(validated_card),
                    hand=[str(c) for c in self._current_hand]
                )
        
        # Check for duplicates in placement
        all_cards = placed_cards[:]
        if len(set(str(c) for c in all_cards)) != len(all_cards):
            raise GameRuleViolationError(
                "Duplicate cards in placement",
                rule_violated="duplicate_placement",
                cards=[str(c) for c in all_cards]
            )
        
        # Check all hand cards are used
        if len(placed_cards) != len(self._current_hand):
            raise GameRuleViolationError(
                "Not all hand cards are used",
                rule_violated="unused_cards",
                hand_size=len(self._current_hand),
                used_size=len(placed_cards)
            )
        
        # Validate each placement
        for card, position, index in placements:
            validate_placement(position, index, self._player_arrangement)
        
        # Apply placements
        try:
            for card, position, index in placements:
                self._player_arrangement.place_card(card, position, index)
            
            # Validate arrangement after placement
            is_valid, error_msg = self._player_arrangement.is_valid_progressive()
            if not is_valid:
                # Rollback placements
                for card, position, index in reversed(placements):
                    row = getattr(self._player_arrangement, position)
                    row[index] = None
                    self._player_arrangement._cards_placed -= 1
                
                raise GameRuleViolationError(
                    f"Invalid arrangement after placement: {error_msg}",
                    rule_violated="invalid_arrangement",
                    error=error_msg
                )
            
            # Record action
            action = StreetAction(
                street=self._current_street,
                cards_dealt=self._current_hand.copy(),
                cards_placed=placements,
                card_discarded=discard
            )
            self._actions.append(action)
            
            # Clear hand and advance street
            self._current_hand = []
            if self._current_street != Street.FOURTH:
                self._current_street = Street(self._current_street + 1)
            else:
                self._current_street = Street.COMPLETE
                
        except GameRuleViolationError:
            raise
        except Exception as e:
            raise GameRuleViolationError(
                f"Failed to apply placements: {e}",
                rule_violated="placement_error",
                error=str(e)
            )
    
    def copy(self) -> 'GameState':
        """
        Create a deep copy of the game state.
        
        Returns:
            New GameState instance
        """
        try:
            # Create new instance
            new_state = GameState.__new__(GameState)
            
            # Copy basic attributes
            new_state.num_players = self.num_players
            new_state.player_index = self.player_index
            new_state.num_jokers = self.num_jokers
            
            # Copy deck and RNG state
            new_state._deck = self._deck.copy()
            new_state._remaining_deck = self._remaining_deck.copy()
            new_state._rng = random.Random()
            new_state._rng.setstate(self._rng.getstate())
            
            # Copy game state
            new_state._current_street = self._current_street
            new_state._player_arrangement = self._player_arrangement.copy()
            new_state._opponent_used_cards = self._opponent_used_cards.copy()
            new_state._actions = [action for action in self._actions]
            new_state._current_hand = self._current_hand.copy()
            
            return new_state
            
        except Exception as e:
            raise StateError(
                f"Failed to copy game state: {e}",
                current_state="copy_operation",
                error=str(e)
            )
    
    def __repr__(self) -> str:
        """String representation of game state."""
        return (f"GameState(street={self._current_street.name}, "
                f"cards_placed={self._player_arrangement.cards_placed}/13, "
                f"hand_size={len(self._current_hand)})")
    
    def to_dict(self) -> Dict:
        """
        Convert game state to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        try:
            return {
                'num_players': self.num_players,
                'player_index': self.player_index,
                'num_jokers': self.num_jokers,
                'current_street': self._current_street.name,
                'player_arrangement': self._player_arrangement.to_dict(),
                'current_hand': [str(c) for c in self._current_hand],
                'cards_placed': self._player_arrangement.cards_placed,
                'is_complete': self.is_complete
            }
        except Exception as e:
            raise StateError(
                f"Failed to serialize game state: {e}",
                current_state="serialization",
                error=str(e)
            )
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        """
        Create GameState from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            New GameState instance
            
        Raises:
            InvalidInputError: If data is invalid
        """
        try:
            # Create new instance
            state = cls(
                num_players=data['num_players'],
                player_index=data['player_index'],
                num_jokers=data.get('num_jokers', 0)
            )
            
            # Restore state
            state._current_street = Street[data['current_street']]
            
            # Restore arrangement if provided
            if 'player_arrangement' in data:
                # This would need PlayerArrangement.from_dict method
                pass
            
            # Restore current hand
            if 'current_hand' in data:
                state._current_hand = validate_card_list(data['current_hand'])
            
            return state
            
        except Exception as e:
            raise InvalidInputError(
                f"Failed to create GameState from dict: {e}",
                error=str(e)
            )