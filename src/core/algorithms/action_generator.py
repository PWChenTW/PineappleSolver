"""
Optimized action generation for OFC Solver.

This module provides intelligent action generation to reduce the search space
while maintaining solution quality.
"""

from typing import List, Tuple, Dict, Set
from collections import defaultdict
import itertools

from src.core.domain import (
    GameState, Street, Card, Rank, Suit,
    PlayerArrangement, HandCategory
)
from src.core.algorithms.mcts_node import Action
from src.core.algorithms.evaluator import StateEvaluator


class ActionGenerator:
    """
    Generates and prioritizes actions for OFC game states.
    
    Uses domain knowledge to reduce the action space while
    ensuring good moves are not pruned.
    """
    
    def __init__(self):
        """Initialize action generator."""
        self.evaluator = StateEvaluator()
    
    def generate_actions(self, state: GameState) -> List[Action]:
        """
        Generate all reasonable actions from current state.
        
        Returns actions sorted by heuristic quality.
        """
        if state.is_complete:
            return []
        
        current_hand = state.current_hand
        if not current_hand:
            return []
        
        if state.current_street == Street.INITIAL:
            return self._generate_initial_actions(state, current_hand)
        else:
            return self._generate_regular_actions(state, current_hand)
    
    def _generate_initial_actions(self, 
                                 state: GameState, 
                                 cards: List[Card]) -> List[Action]:
        """
        Generate actions for initial street (5 cards).
        
        Uses templates based on common successful patterns.
        """
        positions = state.get_valid_placements()
        if len(positions) < 5:
            return []
        
        # Categorize positions
        front_pos = [(p, i) for p, i in positions if p == 'front']
        middle_pos = [(p, i) for p, i in positions if p == 'middle']
        back_pos = [(p, i) for p, i in positions if p == 'back']
        
        # Analyze hand strength
        hand_analysis = self._analyze_initial_hand(cards)
        
        actions = []
        
        # Generate actions based on hand strength
        if hand_analysis['has_pair']:
            actions.extend(self._generate_pair_based_initial(
                cards, front_pos, middle_pos, back_pos, hand_analysis
            ))
        
        if hand_analysis['flush_potential']:
            actions.extend(self._generate_flush_based_initial(
                cards, front_pos, middle_pos, back_pos, hand_analysis
            ))
        
        if hand_analysis['straight_potential']:
            actions.extend(self._generate_straight_based_initial(
                cards, front_pos, middle_pos, back_pos, hand_analysis
            ))
        
        # Always include some balanced distributions
        actions.extend(self._generate_balanced_initial(
            cards, front_pos, middle_pos, back_pos
        ))
        
        # Remove duplicates and sort by quality
        unique_actions = list(set(actions))
        scored_actions = [(self._score_initial_action(state, action), action) 
                         for action in unique_actions]
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        
        # Return top actions
        return [action for _, action in scored_actions[:20]]
    
    def _generate_regular_actions(self,
                                 state: GameState,
                                 cards: List[Card]) -> List[Action]:
        """
        Generate actions for regular streets (3 cards, place 2, discard 1).
        
        Prioritizes actions that maintain hand strength progression.
        """
        positions = state.get_valid_placements()
        if len(positions) < 2:
            return []
        
        actions = []
        
        # For each card to discard
        for discard_idx in range(3):
            discard_card = cards[discard_idx]
            place_cards = [cards[i] for i in range(3) if i != discard_idx]
            
            # Analyze placement options
            placement_options = self._analyze_placement_options(
                state, place_cards, positions
            )
            
            # Generate top placement combinations
            for placements in placement_options[:5]:  # Limit to top 5 per discard
                action = Action(placements, discard=discard_card)
                actions.append(action)
        
        # Score and sort actions
        scored_actions = [(self._score_regular_action(state, action), action)
                         for action in actions]
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        
        return [action for _, action in scored_actions[:15]]
    
    def _analyze_initial_hand(self, cards: List[Card]) -> Dict:
        """Analyze initial 5-card hand for patterns."""
        analysis = {
            'pairs': [],
            'has_pair': False,
            'flush_suits': defaultdict(list),
            'flush_potential': False,
            'straight_cards': [],
            'straight_potential': False,
            'high_cards': []
        }
        
        # Count ranks and suits
        rank_counts = defaultdict(list)
        suit_counts = defaultdict(list)
        
        for card in cards:
            if not card.is_joker:
                rank_counts[card.rank_value].append(card)
                suit_counts[card.suit_value].append(card)
        
        # Find pairs
        for rank, rank_cards in rank_counts.items():
            if len(rank_cards) >= 2:
                analysis['pairs'].append((rank, rank_cards))
                analysis['has_pair'] = True
        
        # Check flush potential
        for suit, suit_cards in suit_counts.items():
            if len(suit_cards) >= 3:
                analysis['flush_suits'][suit] = suit_cards
                analysis['flush_potential'] = True
        
        # Check straight potential
        ranks = sorted(set(card.rank_value for card in cards if not card.is_joker))
        if len(ranks) >= 3:
            # Check for connected cards
            for i in range(len(ranks) - 2):
                if ranks[i+2] - ranks[i] <= 4:  # Potential straight
                    analysis['straight_potential'] = True
                    break
        
        # Identify high cards
        analysis['high_cards'] = [card for card in cards 
                                 if card.rank_value >= Rank.JACK.value]
        
        return analysis
    
    def _generate_pair_based_initial(self,
                                    cards: List[Card],
                                    front_pos: List[Tuple[str, int]],
                                    middle_pos: List[Tuple[str, int]],
                                    back_pos: List[Tuple[str, int]],
                                    analysis: Dict) -> List[Action]:
        """Generate actions when starting hand has pairs."""
        actions = []
        
        for rank, pair_cards in analysis['pairs']:
            remaining = [c for c in cards if c not in pair_cards]
            
            # Strategy 1: Pair in front (if high enough for royalty)
            if rank >= Rank.SIX.value and len(front_pos) >= 2:
                # Place pair in front, distribute others
                placements = [
                    (pair_cards[0], front_pos[0][0], front_pos[0][1]),
                    (pair_cards[1], front_pos[1][0], front_pos[1][1])
                ]
                
                # Distribute remaining cards
                remaining_positions = middle_pos + back_pos
                if len(remaining_positions) >= 3:
                    for i in range(3):
                        pos = remaining_positions[i]
                        placements.append((remaining[i], pos[0], pos[1]))
                    
                    actions.append(Action(placements))
            
            # Strategy 2: Pair in middle (safer)
            if len(middle_pos) >= 2:
                placements = [
                    (pair_cards[0], middle_pos[0][0], middle_pos[0][1]),
                    (pair_cards[1], middle_pos[1][0], middle_pos[1][1])
                ]
                
                # Distribute remaining
                remaining_positions = front_pos[:2] + back_pos[:1]
                if len(remaining_positions) >= 3:
                    for i in range(3):
                        if i < len(remaining) and i < len(remaining_positions):
                            pos = remaining_positions[i]
                            placements.append((remaining[i], pos[0], pos[1]))
                    
                    if len(placements) == 5:
                        actions.append(Action(placements))
        
        return actions
    
    def _generate_flush_based_initial(self,
                                     cards: List[Card],
                                     front_pos: List[Tuple[str, int]],
                                     middle_pos: List[Tuple[str, int]],
                                     back_pos: List[Tuple[str, int]],
                                     analysis: Dict) -> List[Action]:
        """Generate actions for flush potential."""
        actions = []
        
        for suit, suited_cards in analysis['flush_suits'].items():
            if len(suited_cards) >= 3:
                other_cards = [c for c in cards if c not in suited_cards]
                
                # Put suited cards in back
                if len(back_pos) >= min(3, len(suited_cards)):
                    placements = []
                    
                    # Place suited cards in back
                    for i in range(min(3, len(suited_cards))):
                        placements.append((suited_cards[i], back_pos[i][0], back_pos[i][1]))
                    
                    # Fill remaining positions
                    remaining_positions = front_pos[:2] + middle_pos[:2]
                    cards_to_place = suited_cards[3:] + other_cards
                    
                    for i, pos in enumerate(remaining_positions):
                        if i < len(cards_to_place) and len(placements) < 5:
                            placements.append((cards_to_place[i], pos[0], pos[1]))
                    
                    if len(placements) == 5:
                        actions.append(Action(placements))
        
        return actions
    
    def _generate_straight_based_initial(self,
                                        cards: List[Card],
                                        front_pos: List[Tuple[str, int]],
                                        middle_pos: List[Tuple[str, int]],
                                        back_pos: List[Tuple[str, int]],
                                        analysis: Dict) -> List[Action]:
        """Generate actions for straight potential."""
        actions = []
        
        # Find connected cards
        sorted_cards = sorted(cards, key=lambda c: c.rank_value)
        connected_groups = []
        current_group = [sorted_cards[0]]
        
        for i in range(1, len(sorted_cards)):
            if sorted_cards[i].rank_value - sorted_cards[i-1].rank_value <= 2:
                current_group.append(sorted_cards[i])
            else:
                if len(current_group) >= 3:
                    connected_groups.append(current_group)
                current_group = [sorted_cards[i]]
        
        if len(current_group) >= 3:
            connected_groups.append(current_group)
        
        # Place connected cards together
        for group in connected_groups:
            other_cards = [c for c in cards if c not in group]
            
            # Try middle or back for straight potential
            if len(middle_pos) >= min(3, len(group)):
                placements = []
                
                for i in range(min(3, len(group))):
                    placements.append((group[i], middle_pos[i][0], middle_pos[i][1]))
                
                # Fill remaining
                remaining_positions = front_pos[:2] + back_pos[:2]
                cards_to_place = group[3:] + other_cards
                
                for i, pos in enumerate(remaining_positions):
                    if i < len(cards_to_place) and len(placements) < 5:
                        placements.append((cards_to_place[i], pos[0], pos[1]))
                
                if len(placements) == 5:
                    actions.append(Action(placements))
        
        return actions
    
    def _generate_balanced_initial(self,
                                  cards: List[Card],
                                  front_pos: List[Tuple[str, int]],
                                  middle_pos: List[Tuple[str, int]],
                                  back_pos: List[Tuple[str, int]]) -> List[Action]:
        """Generate balanced distributions."""
        actions = []
        
        # Sort cards by rank
        sorted_cards = sorted(cards, key=lambda c: c.rank_value)
        
        # Distribution 1: 2-2-1 (2 front, 2 middle, 1 back)
        if len(front_pos) >= 2 and len(middle_pos) >= 2 and len(back_pos) >= 1:
            placements = [
                (sorted_cards[0], front_pos[0][0], front_pos[0][1]),
                (sorted_cards[1], front_pos[1][0], front_pos[1][1]),
                (sorted_cards[2], middle_pos[0][0], middle_pos[0][1]),
                (sorted_cards[3], middle_pos[1][0], middle_pos[1][1]),
                (sorted_cards[4], back_pos[0][0], back_pos[0][1])
            ]
            actions.append(Action(placements))
        
        # Distribution 2: 1-2-2 (1 front, 2 middle, 2 back)
        if len(front_pos) >= 1 and len(middle_pos) >= 2 and len(back_pos) >= 2:
            placements = [
                (sorted_cards[0], front_pos[0][0], front_pos[0][1]),
                (sorted_cards[1], middle_pos[0][0], middle_pos[0][1]),
                (sorted_cards[2], middle_pos[1][0], middle_pos[1][1]),
                (sorted_cards[3], back_pos[0][0], back_pos[0][1]),
                (sorted_cards[4], back_pos[1][0], back_pos[1][1])
            ]
            actions.append(Action(placements))
        
        return actions
    
    def _analyze_placement_options(self,
                                  state: GameState,
                                  cards: List[Card],
                                  positions: List[Tuple[str, int]]) -> List[List[Tuple[Card, str, int]]]:
        """
        Analyze placement options for 2 cards.
        
        Returns list of placement combinations sorted by quality.
        """
        # Group positions by hand
        front_positions = [p for p in positions if p[0] == 'front']
        middle_positions = [p for p in positions if p[0] == 'middle']
        back_positions = [p for p in positions if p[0] == 'back']
        
        placement_options = []
        
        # Generate all valid 2-card placements
        for pos1, pos2 in itertools.combinations(positions, 2):
            for card_perm in itertools.permutations(cards):
                placements = [
                    (card_perm[0], pos1[0], pos1[1]),
                    (card_perm[1], pos2[0], pos2[1])
                ]
                
                # Quick evaluation of placement quality
                score = self._quick_evaluate_placement(state, placements)
                placement_options.append((score, placements))
        
        # Sort by score and return top options
        placement_options.sort(key=lambda x: x[0], reverse=True)
        return [placements for _, placements in placement_options[:10]]
    
    def _quick_evaluate_placement(self,
                                 state: GameState,
                                 placements: List[Tuple[Card, str, int]]) -> float:
        """Quick heuristic evaluation of a placement."""
        score = 0.0
        
        # Check impact on each hand
        temp_arrangement = state.player_arrangement
        
        for card, position, index in placements:
            # Favor high cards in back
            if position == 'back':
                score += card.rank_value * 0.2
            elif position == 'middle':
                score += card.rank_value * 0.1
            
            # Check for pairs
            if position == 'front':
                front_cards = [c for c in temp_arrangement.front_cards if c is not None]
                for existing in front_cards:
                    if existing.rank_value == card.rank_value:
                        score += 3  # Pair in front
            
            # Check for flush potential
            if position in ('middle', 'back'):
                if position == 'middle':
                    hand_cards = [c for c in temp_arrangement.middle_cards if c is not None]
                else:
                    hand_cards = [c for c in temp_arrangement.back_cards if c is not None]
                
                suit_count = sum(1 for c in hand_cards 
                               if c is not None and c.suit_value == card.suit_value)
                if suit_count >= 2:
                    score += 1.5
        
        return score
    
    def _score_initial_action(self, state: GameState, action: Action) -> float:
        """Score an initial placement action."""
        # Create temporary state to test action
        temp_state = state.copy()
        temp_state.place_cards(action.placements, action.discard)
        
        # Evaluate resulting state
        return self.evaluator.evaluate_state(temp_state)
    
    def _score_regular_action(self, state: GameState, action: Action) -> float:
        """Score a regular street action."""
        # Create temporary state to test action
        temp_state = state.copy()
        temp_state.place_cards(action.placements, action.discard)
        
        # Evaluate resulting state
        base_score = self.evaluator.evaluate_state(temp_state)
        
        # Penalty for discarding high cards
        if action.discard:
            discard_penalty = action.discard.rank_value * 0.1
            base_score -= discard_penalty
        
        return base_score