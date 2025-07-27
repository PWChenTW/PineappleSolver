"""
State evaluation for OFC Solver.

This module provides evaluation functions to estimate the expected value
of game states and arrangements.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import defaultdict

from src.core.domain import (
    GameState, PlayerArrangement, Hand, HandCategory,
    Card, Rank, CardSet
)


class StateEvaluator:
    """
    Evaluates OFC game states and arrangements.
    
    Provides heuristic evaluation of partial arrangements and
    estimates expected final scores.
    """
    
    def __init__(self):
        """Initialize evaluator with precomputed tables."""
        # Cache for hand evaluations
        self._hand_eval_cache: Dict[frozenset, float] = {}
        
        # Royalty thresholds
        self.front_royalty_threshold = {
            Rank.SIX: 1, Rank.SEVEN: 2, Rank.EIGHT: 3,
            Rank.NINE: 4, Rank.TEN: 5, Rank.JACK: 6,
            Rank.QUEEN: 7, Rank.KING: 8, Rank.ACE: 9
        }
        
        self.middle_royalty = {
            HandCategory.THREE_OF_A_KIND: 2,
            HandCategory.STRAIGHT: 4,
            HandCategory.FLUSH: 8,
            HandCategory.FULL_HOUSE: 12,
            HandCategory.FOUR_OF_A_KIND: 20,
            HandCategory.STRAIGHT_FLUSH: 30,
            HandCategory.ROYAL_FLUSH: 50
        }
        
        self.back_royalty = {
            HandCategory.STRAIGHT: 2,
            HandCategory.FLUSH: 4,
            HandCategory.FULL_HOUSE: 6,
            HandCategory.FOUR_OF_A_KIND: 10,
            HandCategory.STRAIGHT_FLUSH: 15,
            HandCategory.ROYAL_FLUSH: 25
        }
    
    def evaluate_state(self, state: GameState) -> float:
        """
        Evaluate a game state.
        
        Returns expected final score considering:
        - Current arrangement strength
        - Royalty potential
        - Foul risk
        - Remaining cards
        """
        if state.is_complete:
            return self.evaluate_final_arrangement(state.player_arrangement)
        
        # Evaluate partial arrangement
        arrangement = state.player_arrangement
        
        # Base evaluation components
        strength_score = self._evaluate_partial_strength(arrangement, state)
        royalty_potential = self._evaluate_royalty_potential(arrangement, state)
        foul_risk = self._evaluate_foul_risk(arrangement, state)
        
        # Combine components
        # Foul risk is heavily weighted as fouling is catastrophic
        total_score = strength_score + royalty_potential - (foul_risk * 20)
        
        return total_score
    
    def evaluate_final_arrangement(self, arrangement: PlayerArrangement) -> float:
        """
        Evaluate a completed arrangement.
        
        Returns the expected score against an average opponent.
        """
        # Check for foul
        is_valid, _ = arrangement.is_valid()
        if not is_valid:
            return -20.0  # Heavy penalty for fouling
        
        # Calculate royalties
        royalties = arrangement.calculate_royalties()
        royalty_score = royalties.total
        
        # Estimate hand strengths
        front = arrangement.get_front_hand()
        middle = arrangement.get_middle_hand()
        back = arrangement.get_back_hand()
        
        # Estimate win probabilities against average opponent
        front_win_prob = self._estimate_win_probability(front, 'front')
        middle_win_prob = self._estimate_win_probability(middle, 'middle')
        back_win_prob = self._estimate_win_probability(back, 'back')
        
        # Calculate expected basic points
        expected_basic = (
            (front_win_prob - 0.5) * 2 +  # Convert to expected points
            (middle_win_prob - 0.5) * 2 +
            (back_win_prob - 0.5) * 2
        )
        
        # Scoop probability (winning all three)
        scoop_prob = front_win_prob * middle_win_prob * back_win_prob
        expected_scoop = scoop_prob * 3
        
        # Total expected score
        total_score = expected_basic + expected_scoop + royalty_score
        
        # Bonus for Fantasyland qualification
        if arrangement.qualifies_for_fantasyland():
            total_score += 5  # Fantasyland is valuable
        
        return total_score
    
    def _evaluate_partial_strength(self, 
                                  arrangement: PlayerArrangement,
                                  state: GameState) -> float:
        """Evaluate strength of partial arrangement."""
        score = 0.0
        
        # Evaluate each partially filled hand
        if arrangement.get_front_hand():
            front = arrangement.get_front_hand()
            score += self._evaluate_hand_strength(front, 'front')
        else:
            # Evaluate partial front cards
            front_cards = [c for c in arrangement.front_cards if c is not None]
            if len(front_cards) >= 2:
                score += self._evaluate_partial_hand(front_cards, 'front', state)
        
        if arrangement.get_middle_hand():
            middle = arrangement.get_middle_hand()
            score += self._evaluate_hand_strength(middle, 'middle')
        else:
            middle_cards = [c for c in arrangement.middle_cards if c is not None]
            if len(middle_cards) >= 2:
                score += self._evaluate_partial_hand(middle_cards, 'middle', state)
        
        if arrangement.get_back_hand():
            back = arrangement.get_back_hand()
            score += self._evaluate_hand_strength(back, 'back')
        else:
            back_cards = [c for c in arrangement.back_cards if c is not None]
            if len(back_cards) >= 2:
                score += self._evaluate_partial_hand(back_cards, 'back', state)
        
        return score
    
    def _evaluate_hand_strength(self, hand: Hand, position: str) -> float:
        """
        Evaluate strength of a complete hand.
        
        Returns a score based on hand type and position.
        """
        hand_type = hand.hand_type
        category = hand_type.category
        
        # Base scores for each category
        category_scores = {
            HandCategory.HIGH_CARD: 0,
            HandCategory.PAIR: 2,
            HandCategory.TWO_PAIR: 4,
            HandCategory.THREE_OF_A_KIND: 6,
            HandCategory.STRAIGHT: 8,
            HandCategory.FLUSH: 10,
            HandCategory.FULL_HOUSE: 12,
            HandCategory.FOUR_OF_A_KIND: 15,
            HandCategory.STRAIGHT_FLUSH: 20,
            HandCategory.ROYAL_FLUSH: 25
        }
        
        score = category_scores.get(category, 0)
        
        # Adjust for rank within category
        if category == HandCategory.PAIR:
            # Higher pairs are much more valuable
            score += hand_type.primary_rank * 0.3
        elif category == HandCategory.THREE_OF_A_KIND:
            score += hand_type.primary_rank * 0.2
        
        # Position multipliers
        if position == 'front':
            score *= 0.8  # Front is less valuable
        elif position == 'back':
            score *= 1.2  # Back is most valuable
        
        return score
    
    def _evaluate_partial_hand(self, 
                              cards: List[Card], 
                              position: str,
                              state: GameState) -> float:
        """Evaluate a partial hand based on potential."""
        # Count pairs, flushes, straight draws
        rank_counts = defaultdict(int)
        suit_counts = defaultdict(int)
        
        for card in cards:
            if not card.is_joker:
                rank_counts[card.rank_value] += 1
                suit_counts[card.suit_value] += 1
        
        score = 0.0
        
        # Check for pairs/trips
        for rank, count in rank_counts.items():
            if count >= 2:
                score += 2 + (rank * 0.1)
            if count >= 3:
                score += 4 + (rank * 0.2)
        
        # Check for flush draws
        for suit, count in suit_counts.items():
            if position != 'front' and count >= 3:
                score += 1.5
            if position != 'front' and count >= 4:
                score += 3
        
        # Check for straight draws
        if position != 'front':
            straight_potential = self._check_straight_potential(cards)
            score += straight_potential
        
        return score
    
    def _check_straight_potential(self, cards: List[Card]) -> float:
        """Check potential for making a straight."""
        if len(cards) < 3:
            return 0.0
        
        ranks = sorted(set(c.rank_value for c in cards if not c.is_joker))
        if not ranks:
            return 0.0
        
        # Check for connected cards
        max_connected = 1
        current_connected = 1
        
        for i in range(1, len(ranks)):
            if ranks[i] - ranks[i-1] == 1:
                current_connected += 1
                max_connected = max(max_connected, current_connected)
            elif ranks[i] - ranks[i-1] <= 2:
                # One gap - still potential
                current_connected += 0.5
            else:
                current_connected = 1
        
        # Special case for ace-low potential
        if Rank.ACE.value in ranks and any(r <= 4 for r in ranks):
            max_connected = max(max_connected, 2)
        
        if max_connected >= 4:
            return 2.0
        elif max_connected >= 3:
            return 1.0
        
        return 0.0
    
    def _evaluate_royalty_potential(self,
                                   arrangement: PlayerArrangement,
                                   state: GameState) -> float:
        """Evaluate potential for earning royalties."""
        potential = 0.0
        
        # Front royalties (66+)
        front_cards = [c for c in arrangement.front_cards if c is not None]
        if len(front_cards) < 3:
            # Check for pair potential
            rank_counts = defaultdict(int)
            for card in front_cards:
                if not card.is_joker:
                    rank_counts[card.rank_value] += 1
            
            for rank, count in rank_counts.items():
                if count == 2 and rank >= Rank.SIX.value:
                    # Already have qualifying pair
                    potential += self.front_royalty_threshold.get(Rank(rank), 0)
                elif count == 1 and rank >= Rank.QUEEN.value:
                    # Potential for QQ+ (Fantasyland)
                    potential += 2
        
        # Middle royalties (trips+)
        middle_cards = [c for c in arrangement.middle_cards if c is not None]
        if len(middle_cards) >= 2:
            trips_potential = self._check_trips_potential(middle_cards)
            potential += trips_potential * 2  # Trips = 2 royalty
        
        # Back royalties (straight+)
        back_cards = [c for c in arrangement.back_cards if c is not None]
        if len(back_cards) >= 3:
            straight_pot = self._check_straight_potential(back_cards)
            flush_pot = self._check_flush_potential(back_cards)
            potential += max(straight_pot, flush_pot) * 2
        
        return potential
    
    def _check_trips_potential(self, cards: List[Card]) -> float:
        """Check potential for making trips."""
        rank_counts = defaultdict(int)
        for card in cards:
            if not card.is_joker:
                rank_counts[card.rank_value] += 1
        
        for count in rank_counts.values():
            if count >= 2:
                return 0.3  # Decent chance with more cards
        
        return 0.0
    
    def _check_flush_potential(self, cards: List[Card]) -> float:
        """Check potential for making a flush."""
        suit_counts = defaultdict(int)
        for card in cards:
            if not card.is_joker:
                suit_counts[card.suit_value] += 1
        
        max_suit = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit >= 4:
            return 0.8
        elif max_suit >= 3:
            return 0.3
        
        return 0.0
    
    def _evaluate_foul_risk(self,
                           arrangement: PlayerArrangement,
                           state: GameState) -> float:
        """
        Evaluate risk of fouling.
        
        Returns a risk score from 0 (safe) to 1 (high risk).
        """
        # Get current hand strengths
        front_strength = 0
        middle_strength = 0
        back_strength = 0
        
        # Evaluate front
        front_cards = [c for c in arrangement.front_cards if c is not None]
        if len(front_cards) == 3:
            front = arrangement.get_front_hand()
            if front:
                front_strength = self._hand_category_value(front.hand_type.category)
        elif len(front_cards) >= 2:
            # Estimate based on current cards
            if self._has_pair(front_cards):
                front_strength = 1
        
        # Evaluate middle
        middle_cards = [c for c in arrangement.middle_cards if c is not None]
        if len(middle_cards) == 5:
            middle = arrangement.get_middle_hand()
            if middle:
                middle_strength = self._hand_category_value(middle.hand_type.category)
        elif len(middle_cards) >= 2:
            if self._has_pair(middle_cards):
                middle_strength = 1
        
        # Evaluate back
        back_cards = [c for c in arrangement.back_cards if c is not None]
        if len(back_cards) == 5:
            back = arrangement.get_back_hand()
            if back:
                back_strength = self._hand_category_value(back.hand_type.category)
        elif len(back_cards) >= 2:
            if self._has_pair(back_cards):
                back_strength = 1
        
        # Calculate risk
        risk = 0.0
        
        # Check middle >= front constraint
        if front_strength > middle_strength + 1:
            risk += 0.5
        
        # Check back >= middle constraint
        if middle_strength > back_strength + 1:
            risk += 0.5
        
        # Additional risk for strong front hands early
        if len(front_cards) < 3 and front_strength >= 2:
            risk += 0.3
        
        return min(risk, 1.0)
    
    def _hand_category_value(self, category: HandCategory) -> int:
        """Convert hand category to numeric value for comparison."""
        return category.value
    
    def _has_pair(self, cards: List[Card]) -> bool:
        """Check if cards contain a pair."""
        rank_counts = defaultdict(int)
        for card in cards:
            if not card.is_joker:
                rank_counts[card.rank_value] += 1
        
        return any(count >= 2 for count in rank_counts.values())
    
    def _estimate_win_probability(self, hand: Hand, position: str) -> float:
        """
        Estimate probability of winning with a hand.
        
        Based on typical hand distributions in OFC.
        """
        if not hand:
            return 0.5
        
        category = hand.hand_type.category
        
        # Win probability tables (approximate)
        if position == 'front':
            win_probs = {
                HandCategory.HIGH_CARD: 0.3,
                HandCategory.PAIR: 0.6,
                HandCategory.THREE_OF_A_KIND: 0.95
            }
        elif position == 'middle':
            win_probs = {
                HandCategory.HIGH_CARD: 0.1,
                HandCategory.PAIR: 0.25,
                HandCategory.TWO_PAIR: 0.45,
                HandCategory.THREE_OF_A_KIND: 0.7,
                HandCategory.STRAIGHT: 0.8,
                HandCategory.FLUSH: 0.85,
                HandCategory.FULL_HOUSE: 0.9,
                HandCategory.FOUR_OF_A_KIND: 0.95,
                HandCategory.STRAIGHT_FLUSH: 0.99,
                HandCategory.ROYAL_FLUSH: 1.0
            }
        else:  # back
            win_probs = {
                HandCategory.HIGH_CARD: 0.05,
                HandCategory.PAIR: 0.15,
                HandCategory.TWO_PAIR: 0.35,
                HandCategory.THREE_OF_A_KIND: 0.55,
                HandCategory.STRAIGHT: 0.65,
                HandCategory.FLUSH: 0.75,
                HandCategory.FULL_HOUSE: 0.85,
                HandCategory.FOUR_OF_A_KIND: 0.92,
                HandCategory.STRAIGHT_FLUSH: 0.98,
                HandCategory.ROYAL_FLUSH: 1.0
            }
        
        base_prob = win_probs.get(category, 0.5)
        
        # Adjust for rank within category
        if category == HandCategory.PAIR:
            # Adjust based on pair rank
            rank_adjustment = (hand.hand_type.primary_rank - 6) * 0.02
            base_prob += rank_adjustment
        
        return max(0.0, min(1.0, base_prob))