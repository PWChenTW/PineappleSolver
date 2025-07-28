#!/usr/bin/env python3
"""
完整的 OFC Pineapple MCTS 求解器（包含後續街道模擬）
"""

import random
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time

# Card representation
RANKS = '23456789TJQKA'
SUITS = 'cdhs'
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}


@dataclass
class Card:
    """Represents a playing card."""
    rank: str
    suit: str
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __lt__(self, other):
        return RANK_VALUES[self.rank] < RANK_VALUES[other.rank]
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create a Card from string like 'As' or 'Td'."""
        return cls(rank=card_str[0], suit=card_str[1])


def create_full_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    return [Card(rank=r, suit=s) for r in RANKS for s in SUITS]


@dataclass
class Hand:
    """Represents a poker hand (front, middle, or back)."""
    cards: List[Card] = field(default_factory=list)
    max_size: int = 5
    
    def is_full(self) -> bool:
        return len(self.cards) >= self.max_size
    
    def add_card(self, card: Card) -> bool:
        if self.is_full():
            return False
        self.cards.append(card)
        return True
    
    def copy(self) -> 'Hand':
        new_hand = Hand(max_size=self.max_size)
        new_hand.cards = self.cards.copy()
        return new_hand
    
    def evaluate(self) -> Tuple[int, List[int]]:
        """Evaluate hand strength. Returns (rank, kickers)."""
        if not self.cards:
            return (0, [])
        
        # Count ranks
        rank_counts = defaultdict(int)
        suits = defaultdict(list)
        
        for card in self.cards:
            rank_counts[card.rank] += 1
            suits[card.suit].append(card)
        
        # Sort by count then rank
        sorted_ranks = sorted(rank_counts.items(), 
                            key=lambda x: (x[1], RANK_VALUES[x[0]]), 
                            reverse=True)
        
        # Check for flush
        is_flush = any(len(cards) >= 5 for cards in suits.values()) if len(self.cards) >= 5 else False
        
        # Check for straight
        if len(self.cards) >= 5:
            sorted_cards = sorted(self.cards, key=lambda c: RANK_VALUES[c.rank])
            is_straight = self._check_straight(sorted_cards)
        else:
            is_straight = False
        
        # Determine hand rank
        counts = [count for rank, count in sorted_ranks]
        
        if is_straight and is_flush:
            return (8, [RANK_VALUES[self.cards[0].rank]])  # Straight flush
        elif counts[0] == 4:
            return (7, [RANK_VALUES[sorted_ranks[0][0]]])  # Four of a kind
        elif counts[0] == 3 and len(counts) > 1 and counts[1] == 2:
            return (6, [RANK_VALUES[sorted_ranks[0][0]], RANK_VALUES[sorted_ranks[1][0]]])  # Full house
        elif is_flush:
            return (5, [RANK_VALUES[c.rank] for c in sorted(self.cards, reverse=True)])  # Flush
        elif is_straight:
            return (4, [max(RANK_VALUES[c.rank] for c in self.cards)])  # Straight
        elif counts[0] == 3:
            return (3, [RANK_VALUES[sorted_ranks[0][0]]])  # Three of a kind
        elif counts[0] == 2 and len(counts) > 1 and counts[1] == 2:
            return (2, [RANK_VALUES[sorted_ranks[0][0]], RANK_VALUES[sorted_ranks[1][0]]])  # Two pair
        elif counts[0] == 2:
            return (1, [RANK_VALUES[sorted_ranks[0][0]]])  # One pair
        else:
            return (0, [RANK_VALUES[c.rank] for c in sorted(self.cards, reverse=True)])  # High card
    
    def _check_straight(self, sorted_cards: List[Card]) -> bool:
        """Check if cards form a straight."""
        if len(sorted_cards) < 5:
            return False
        
        # Check regular straight
        values = [RANK_VALUES[c.rank] for c in sorted_cards]
        for i in range(len(values) - 4):
            if values[i+4] - values[i] == 4:
                # Check all 5 cards are consecutive
                is_straight = True
                for j in range(4):
                    if values[i+j+1] - values[i+j] != 1:
                        is_straight = False
                        break
                if is_straight:
                    return True
        
        # Check wheel (A-2-3-4-5)
        ranks = [c.rank for c in sorted_cards]
        if 'A' in ranks and '2' in ranks and '3' in ranks and '4' in ranks and '5' in ranks:
            return True
        
        return False


class PineappleState:
    """Complete game state for Pineapple OFC."""
    
    def __init__(self):
        self.front_hand = Hand(max_size=3)
        self.middle_hand = Hand(max_size=5)
        self.back_hand = Hand(max_size=5)
        self.discarded: List[Card] = []
        self.street = 0  # 0=initial, 1-4=draw streets
    
    def copy(self) -> 'PineappleState':
        new_state = PineappleState()
        new_state.front_hand = self.front_hand.copy()
        new_state.middle_hand = self.middle_hand.copy()
        new_state.back_hand = self.back_hand.copy()
        new_state.discarded = self.discarded.copy()
        new_state.street = self.street
        return new_state
    
    def get_all_cards(self) -> Set[Card]:
        """Get all cards in the current state."""
        all_cards = set()
        all_cards.update(self.front_hand.cards)
        all_cards.update(self.middle_hand.cards)
        all_cards.update(self.back_hand.cards)
        all_cards.update(self.discarded)
        return all_cards
    
    def get_available_positions(self) -> List[str]:
        """Get positions that can accept cards."""
        positions = []
        if not self.front_hand.is_full():
            positions.append('front')
        if not self.middle_hand.is_full():
            positions.append('middle')
        if not self.back_hand.is_full():
            positions.append('back')
        return positions
    
    def place_card(self, card: Card, position: str) -> bool:
        """Place a card in the specified position."""
        if position == 'front':
            return self.front_hand.add_card(card)
        elif position == 'middle':
            return self.middle_hand.add_card(card)
        elif position == 'back':
            return self.back_hand.add_card(card)
        return False
    
    def is_complete(self) -> bool:
        """Check if all hands are full."""
        return (self.front_hand.is_full() and 
                self.middle_hand.is_full() and 
                self.back_hand.is_full())
    
    def is_valid(self) -> bool:
        """Check if arrangement is valid (no fouls)."""
        if not self.is_complete():
            return True  # Can't foul until complete
        
        front_rank, _ = self.front_hand.evaluate()
        middle_rank, _ = self.middle_hand.evaluate()
        back_rank, _ = self.back_hand.evaluate()
        
        # Back must beat middle, middle must beat front
        return back_rank >= middle_rank >= front_rank
    
    def advance_street(self):
        """Move to next street."""
        self.street += 1


class PineappleMCTSNode:
    """MCTS node for Pineapple OFC."""
    
    def __init__(self, state: PineappleState, parent=None, action=None, 
                 remaining_deck=None):
        self.state = state
        self.parent = parent
        self.action = action  # (cards_placed, card_discarded) or initial placement
        self.remaining_deck = remaining_deck or []
        
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions = None
        self._setup_untried_actions()
    
    def _setup_untried_actions(self):
        """Initialize untried actions based on current street."""
        if self.state.is_complete():
            self.untried_actions = []
            return
        
        self.untried_actions = []
        
        if self.state.street == 0:
            # Initial placement: try all combinations of 5 cards
            self._setup_initial_placement_actions()
        else:
            # Draw streets: place 2 of 3 cards, discard 1
            self._setup_draw_street_actions()
    
    def _setup_initial_placement_actions(self):
        """Setup actions for initial 5-card placement."""
        if len(self.remaining_deck) < 5:
            return
        
        # For initial placement, we need to explore different arrangements
        # This is simplified - in reality we'd want more sophisticated action generation
        cards = self.remaining_deck[:5]
        positions = ['front', 'middle', 'back']
        
        # Generate some reasonable initial placements
        # (In practice, you'd want a smarter heuristic here)
        sample_actions = []
        
        # Try putting strongest cards in back
        sorted_cards = sorted(cards, key=lambda c: RANK_VALUES[c.rank], reverse=True)
        placement1 = [
            (sorted_cards[0], 'back'),
            (sorted_cards[1], 'back'),
            (sorted_cards[2], 'middle'),
            (sorted_cards[3], 'middle'),
            (sorted_cards[4], 'front')
        ]
        sample_actions.append(('initial', placement1))
        
        # Try other arrangements
        placement2 = [
            (sorted_cards[0], 'back'),
            (sorted_cards[1], 'middle'),
            (sorted_cards[2], 'back'),
            (sorted_cards[3], 'middle'),
            (sorted_cards[4], 'front')
        ]
        sample_actions.append(('initial', placement2))
        
        self.untried_actions = sample_actions
    
    def _setup_draw_street_actions(self):
        """Setup actions for draw streets (place 2, discard 1)."""
        if len(self.remaining_deck) < 3:
            return
        
        # Draw 3 cards
        drawn_cards = self.remaining_deck[:3]
        positions = self.state.get_available_positions()
        
        # Generate all combinations of placing 2 cards and discarding 1
        for discard_idx in range(3):
            cards_to_place = [drawn_cards[i] for i in range(3) if i != discard_idx]
            card_to_discard = drawn_cards[discard_idx]
            
            # Try different position combinations for the 2 cards
            for pos1 in positions:
                for pos2 in positions:
                    action = ('draw', [
                        (cards_to_place[0], pos1),
                        (cards_to_place[1], pos2)
                    ], card_to_discard)
                    self.untried_actions.append(action)


class PineappleOFCSolver:
    """Full Pineapple OFC solver with complete game simulation."""
    
    def __init__(self, num_simulations=10000):
        self.num_simulations = num_simulations
    
    def solve_initial_five(self, initial_cards: List[Card]) -> PineappleState:
        """Solve initial 5-card placement with full game simulation."""
        print(f"\nSolving Pineapple OFC initial placement with full game simulation")
        print(f"Initial cards: {' '.join(str(c) for c in initial_cards)}")
        
        # Create full deck and remove initial cards
        full_deck = create_full_deck()
        remaining_deck = [c for c in full_deck if c not in initial_cards]
        random.shuffle(remaining_deck)
        
        # Add initial cards to front of deck (they will be "drawn" first)
        deck = initial_cards + remaining_deck
        
        # Create root node
        root = PineappleMCTSNode(PineappleState(), remaining_deck=deck)
        
        print(f"\nRunning {self.num_simulations} simulations with full game rollouts...")
        
        # Run MCTS
        for i in range(self.num_simulations):
            self._run_simulation(root)
            
            if (i + 1) % 1000 == 0:
                print(f"Progress: {i+1}/{self.num_simulations} simulations")
        
        # Extract best initial placement
        best_state = self._extract_best_initial_placement(root)
        
        return best_state
    
    def _run_simulation(self, node: PineappleMCTSNode) -> float:
        """Run one MCTS simulation with full game rollout."""
        # Selection
        path = [node]
        
        while node.untried_actions == [] and node.children:
            node = self._select_child(node)
            path.append(node)
        
        # Expansion
        if node.untried_actions:
            action = random.choice(node.untried_actions)
            node.untried_actions.remove(action)
            node = self._add_child(node, action)
            path.append(node)
        
        # Simulation - play out the full game
        result = self._simulate_full_game(node)
        
        # Backpropagation
        for n in path:
            n.visits += 1
            n.wins += result
        
        return result
    
    def _simulate_full_game(self, node: PineappleMCTSNode) -> float:
        """Simulate a complete game from current position."""
        state = node.state.copy()
        deck = node.remaining_deck.copy()
        deck_idx = 0
        
        # Complete initial placement if needed
        if state.street == 0 and not self._is_initial_placement_complete(state):
            # Random initial placement completion
            cards_to_place = 5 - self._count_placed_cards(state)
            for _ in range(cards_to_place):
                if deck_idx < len(deck):
                    card = deck[deck_idx]
                    deck_idx += 1
                    positions = state.get_available_positions()
                    if positions:
                        pos = random.choice(positions)
                        state.place_card(card, pos)
            state.advance_street()
        
        # Simulate remaining streets
        while not state.is_complete() and deck_idx + 3 <= len(deck):
            # Draw 3 cards
            drawn = deck[deck_idx:deck_idx+3]
            deck_idx += 3
            
            # Randomly place 2, discard 1
            discard_idx = random.randint(0, 2)
            cards_to_place = [drawn[i] for i in range(3) if i != discard_idx]
            state.discarded.append(drawn[discard_idx])
            
            # Place the 2 cards
            for card in cards_to_place:
                positions = state.get_available_positions()
                if positions:
                    pos = random.choice(positions)
                    state.place_card(card, pos)
            
            state.advance_street()
        
        # Evaluate final position
        return self._evaluate_final_state(state)
    
    def _evaluate_final_state(self, state: PineappleState) -> float:
        """Evaluate the final game state."""
        if not state.is_valid():
            return 0.0  # Fouled
        
        # Evaluate each hand
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        # Fantasy land bonus
        fantasy_bonus = 0.0
        if len(state.front_hand.cards) == 3:
            # QQ+ in front = fantasy land
            if front_rank >= 1:  # At least a pair
                cards = state.front_hand.cards
                if any(c.rank in 'QKA' for c in cards):
                    if sum(1 for c in cards if c.rank == cards[0].rank) >= 2:
                        fantasy_bonus = 0.3
        
        # Calculate score with proper weights
        score = (front_rank * 0.15 +      # Front hand less important
                middle_rank * 0.35 +      # Middle hand medium importance  
                back_rank * 0.5 +         # Back hand most important
                fantasy_bonus)
        
        # Normalize
        return min(score / 10.0, 1.0)
    
    def _is_initial_placement_complete(self, state: PineappleState) -> bool:
        """Check if initial 5 cards are placed."""
        return self._count_placed_cards(state) == 5
    
    def _count_placed_cards(self, state: PineappleState) -> int:
        """Count total placed cards."""
        return (len(state.front_hand.cards) + 
                len(state.middle_hand.cards) + 
                len(state.back_hand.cards))
    
    def _select_child(self, node: PineappleMCTSNode) -> PineappleMCTSNode:
        """Select child using UCB1."""
        if node.visits == 0:
            return random.choice(node.children)
        
        c = 1.4  # Exploration constant
        best_score = -1
        best_child = None
        
        for child in node.children:
            if child.visits == 0:
                score = float('inf')
            else:
                score = (child.wins / child.visits + 
                        c * math.sqrt(math.log(node.visits) / child.visits))
            
            if score > best_score:
                best_score = score
                best_child = child
        
        return best_child
    
    def _add_child(self, node: PineappleMCTSNode, action) -> PineappleMCTSNode:
        """Add a child node for the given action."""
        new_state = node.state.copy()
        new_deck = node.remaining_deck.copy()
        
        if action[0] == 'initial':
            # Initial placement
            placements = action[1]
            for card, position in placements:
                new_state.place_card(card, position)
            new_deck = new_deck[5:]  # Remove placed cards
            new_state.advance_street()
        else:
            # Draw street action
            _, placements, discard = action
            for card, position in placements:
                new_state.place_card(card, position)
            new_state.discarded.append(discard)
            new_deck = new_deck[3:]  # Remove drawn cards
            new_state.advance_street()
        
        child = PineappleMCTSNode(new_state, parent=node, action=action,
                                remaining_deck=new_deck)
        node.children.append(child)
        return child
    
    def _extract_best_initial_placement(self, root: PineappleMCTSNode) -> PineappleState:
        """Extract the best initial placement from MCTS tree."""
        # Find the child with best win rate that represents a complete initial placement
        best_child = None
        best_score = -1
        
        for child in root.children:
            if child.visits > 0 and self._is_initial_placement_complete(child.state):
                score = child.wins / child.visits
                if score > best_score:
                    best_score = score
                    best_child = child
        
        if best_child:
            print(f"\nBest initial placement found with win rate: {best_score:.3f}")
            return best_child.state
        else:
            print("\nNo complete initial placement found, using heuristic")
            # Fallback to heuristic
            state = PineappleState()
            cards = sorted(root.remaining_deck[:5], 
                         key=lambda c: RANK_VALUES[c.rank], reverse=True)
            state.place_card(cards[0], 'back')
            state.place_card(cards[1], 'back')
            state.place_card(cards[2], 'middle')
            state.place_card(cards[3], 'middle')
            state.place_card(cards[4], 'front')
            return state


def main():
    """Test the full Pineapple solver."""
    solver = PineappleOFCSolver(num_simulations=5000)
    
    # Test cards
    cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    result = solver.solve_initial_five(cards)
    
    print("\n最佳初始擺放:")
    print(f"前墩: {' '.join(str(c) for c in result.front_hand.cards)}")
    print(f"中墩: {' '.join(str(c) for c in result.middle_hand.cards)}")
    print(f"後墩: {' '.join(str(c) for c in result.back_hand.cards)}")
    
    if result.is_valid():
        print("\n✓ 有效擺放")
    else:
        print("\n✗ 無效擺放")


if __name__ == "__main__":
    main()