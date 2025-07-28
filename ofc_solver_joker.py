#!/usr/bin/env python3
"""
OFC Pineapple MCTS 求解器 - 支持鬼牌版本
支持2張鬼牌，鬼牌可以代替任何牌以形成最佳手牌組合
"""

import random
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time
import itertools

# Card representation
RANKS = '23456789TJQKA'
SUITS = 'cdhs'
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}
# Add joker representation
RANK_VALUES['X'] = 15  # Joker rank value (higher than Ace for sorting)

@dataclass
class Card:
    """Represents a playing card (including jokers)."""
    rank: str
    suit: str
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __lt__(self, other):
        # Jokers are sorted last
        if self.is_joker() and not other.is_joker():
            return False
        if not self.is_joker() and other.is_joker():
            return True
        if self.is_joker() and other.is_joker():
            return False
        return RANK_VALUES[self.rank] < RANK_VALUES[other.rank]
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    def is_joker(self) -> bool:
        """Check if this card is a joker."""
        return self.rank == 'X'
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create a Card from string like 'As', 'Td', or 'Xj' (joker)."""
        return cls(rank=card_str[0], suit=card_str[1])
    
    @classmethod
    def joker(cls) -> 'Card':
        """Create a joker card."""
        return cls(rank='X', suit='j')


def create_full_deck(include_jokers: bool = True) -> List[Card]:
    """Create a deck with optional jokers."""
    deck = [Card(rank=r, suit=s) for r in RANKS for s in SUITS]
    if include_jokers:
        # Add 2 jokers
        deck.extend([Card.joker(), Card.joker()])
    return deck


class JokerHandEvaluator:
    """Evaluates hands containing jokers by finding optimal joker assignments."""
    
    @staticmethod
    def evaluate_with_jokers(cards: List[Card]) -> Tuple[int, List[int], List[Card]]:
        """
        Evaluate hand with jokers, returning best possible hand.
        Returns: (rank, kickers, best_assignment)
        """
        jokers = [c for c in cards if c.is_joker()]
        regular_cards = [c for c in cards if not c.is_joker()]
        
        if not jokers:
            # No jokers, evaluate normally
            hand = Hand()
            hand.cards = cards
            rank, kickers = hand.evaluate()
            return rank, kickers, cards
        
        # Find all possible joker replacements
        best_rank = -1
        best_kickers = []
        best_assignment = cards
        
        # Generate all possible card assignments for jokers
        possible_replacements = []
        for rank in RANKS:
            for suit in SUITS:
                possible_replacements.append(Card(rank, suit))
        
        # Try all combinations of joker replacements
        num_jokers = len(jokers)
        for replacement_combo in itertools.combinations_with_replacement(possible_replacements, num_jokers):
            # Create a test hand with jokers replaced
            test_cards = regular_cards.copy()
            test_cards.extend(replacement_combo)
            
            # Evaluate this combination
            temp_hand = Hand()
            temp_hand.cards = test_cards
            rank, kickers = temp_hand.evaluate()
            
            # Check if this is better
            if rank > best_rank or (rank == best_rank and kickers > best_kickers):
                best_rank = rank
                best_kickers = kickers
                best_assignment = test_cards
        
        return best_rank, best_kickers, best_assignment


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
        """Evaluate hand strength, handling jokers optimally."""
        if not self.cards:
            return (0, [])
        
        # Check for jokers
        if any(c.is_joker() for c in self.cards):
            rank, kickers, _ = JokerHandEvaluator.evaluate_with_jokers(self.cards)
            return (rank, kickers)
        
        # Original evaluation logic for non-joker hands
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
    
    def get_fantasy_land_status(self) -> bool:
        """Check if this hand qualifies for Fantasy Land (for front hand)."""
        if self.max_size != 3:  # Only front hand can trigger Fantasy Land
            return False
        
        if len(self.cards) != 3:
            return False
        
        # Evaluate hand with joker optimization
        rank, kickers, best_cards = JokerHandEvaluator.evaluate_with_jokers(self.cards)
        
        # QQ+ qualifies for Fantasy Land
        if rank >= 1:  # At least a pair
            # Check if it's a pair of Q, K, or A
            pair_rank = None
            rank_counts = defaultdict(int)
            for card in best_cards:
                rank_counts[card.rank] += 1
            
            for r, count in rank_counts.items():
                if count >= 2 and r in 'QKA':
                    return True
        
        return False


class PineappleStateJoker:
    """Game state for Pineapple OFC with joker support."""
    
    def __init__(self):
        self.front_hand = Hand(max_size=3)
        self.middle_hand = Hand(max_size=5)
        self.back_hand = Hand(max_size=5)
        self.discarded: List[Card] = []
        self.street = 0  # 0=initial, 1-4=draw streets
    
    def copy(self) -> 'PineappleStateJoker':
        new_state = PineappleStateJoker()
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
    
    def has_fantasy_land(self) -> bool:
        """Check if the current state qualifies for Fantasy Land."""
        return self.front_hand.get_fantasy_land_status()


class PineappleMCTSNodeJoker:
    """MCTS node for Pineapple OFC with joker support."""
    
    def __init__(self, state: PineappleStateJoker, parent=None, action=None, 
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
        cards = self.remaining_deck[:5]
        
        # Generate some reasonable initial placements
        sample_actions = []
        
        # Special handling for jokers - they should be placed strategically
        jokers = [c for c in cards if c.is_joker()]
        regular_cards = [c for c in cards if not c.is_joker()]
        
        # Sort regular cards by strength
        sorted_regular = sorted(regular_cards, key=lambda c: RANK_VALUES[c.rank], reverse=True)
        
        # Strategy 1: Use jokers to strengthen front hand for Fantasy Land
        if len(jokers) >= 1:
            placement1 = []
            # Put a joker in front for potential Fantasy Land
            placement1.append((jokers[0], 'front'))
            
            # Place remaining cards
            remaining = sorted_regular + jokers[1:]
            if len(remaining) >= 2:
                placement1.append((remaining[0], 'back'))
                placement1.append((remaining[1], 'back'))
            if len(remaining) >= 4:
                placement1.append((remaining[2], 'middle'))
                placement1.append((remaining[3], 'middle'))
            
            sample_actions.append(('initial', placement1))
        
        # Strategy 2: Traditional placement with jokers in strong positions
        sorted_all = sorted(cards, key=lambda c: RANK_VALUES[c.rank] if not c.is_joker() else 100, reverse=True)
        placement2 = [
            (sorted_all[0], 'back'),
            (sorted_all[1], 'back'),
            (sorted_all[2], 'middle'),
            (sorted_all[3], 'middle'),
            (sorted_all[4], 'front')
        ]
        sample_actions.append(('initial', placement2))
        
        # Strategy 3: Balanced placement
        placement3 = [
            (sorted_all[0], 'back'),
            (sorted_all[1], 'middle'),
            (sorted_all[2], 'back'),
            (sorted_all[3], 'middle'),
            (sorted_all[4], 'front')
        ]
        sample_actions.append(('initial', placement3))
        
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


class PineappleOFCSolverJoker:
    """Pineapple OFC solver with joker support."""
    
    def __init__(self, num_simulations=10000):
        self.num_simulations = num_simulations
    
    def solve_initial_five(self, initial_cards: List[Card]) -> PineappleStateJoker:
        """Solve initial 5-card placement with full game simulation."""
        print(f"\nSolving Pineapple OFC with Jokers - Initial Placement")
        print(f"Initial cards: {' '.join(str(c) for c in initial_cards)}")
        
        # Count jokers
        num_jokers = sum(1 for c in initial_cards if c.is_joker())
        if num_jokers > 0:
            print(f"Number of jokers: {num_jokers}")
        
        # Create full deck and remove initial cards
        full_deck = create_full_deck(include_jokers=True)
        remaining_deck = [c for c in full_deck if c not in initial_cards]
        random.shuffle(remaining_deck)
        
        # Add initial cards to front of deck (they will be "drawn" first)
        deck = initial_cards + remaining_deck
        
        # Create root node
        root = PineappleMCTSNodeJoker(PineappleStateJoker(), remaining_deck=deck)
        
        print(f"\nRunning {self.num_simulations} simulations with full game rollouts...")
        
        # Run MCTS
        for i in range(self.num_simulations):
            self._run_simulation(root)
            
            if (i + 1) % 1000 == 0:
                print(f"Progress: {i+1}/{self.num_simulations} simulations")
        
        # Extract best initial placement
        best_state = self._extract_best_initial_placement(root)
        
        return best_state
    
    def _run_simulation(self, node: PineappleMCTSNodeJoker) -> float:
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
    
    def _simulate_full_game(self, node: PineappleMCTSNodeJoker) -> float:
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
                        # Smart placement for jokers during simulation
                        if card.is_joker() and 'front' in positions:
                            # Prefer front for jokers (Fantasy Land potential)
                            pos = 'front'
                        else:
                            pos = random.choice(positions)
                        state.place_card(card, pos)
            state.advance_street()
        
        # Simulate remaining streets
        while not state.is_complete() and deck_idx + 3 <= len(deck):
            # Draw 3 cards
            drawn = deck[deck_idx:deck_idx+3]
            deck_idx += 3
            
            # Smart discard strategy for jokers
            joker_indices = [i for i, c in enumerate(drawn) if c.is_joker()]
            regular_indices = [i for i, c in enumerate(drawn) if not c.is_joker()]
            
            # Never discard jokers if possible
            if len(regular_indices) > 0:
                # Discard the weakest regular card
                weakest_idx = min(regular_indices, 
                                key=lambda i: RANK_VALUES[drawn[i].rank])
                discard_idx = weakest_idx
            else:
                # All jokers, must discard one
                discard_idx = random.randint(0, 2)
            
            cards_to_place = [drawn[i] for i in range(3) if i != discard_idx]
            state.discarded.append(drawn[discard_idx])
            
            # Place the 2 cards
            for card in cards_to_place:
                positions = state.get_available_positions()
                if positions:
                    # Smart placement for jokers
                    if card.is_joker():
                        if 'front' in positions and len(state.front_hand.cards) < 2:
                            pos = 'front'
                        elif 'back' in positions:
                            pos = 'back'
                        else:
                            pos = random.choice(positions)
                    else:
                        pos = random.choice(positions)
                    state.place_card(card, pos)
            
            state.advance_street()
        
        # Evaluate final position
        return self._evaluate_final_state(state)
    
    def _evaluate_final_state(self, state: PineappleStateJoker) -> float:
        """Evaluate the final game state."""
        if not state.is_valid():
            return 0.0  # Fouled
        
        # Evaluate each hand
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        # Fantasy land bonus
        fantasy_bonus = 0.0
        if state.has_fantasy_land():
            fantasy_bonus = 0.5  # Increased bonus for Fantasy Land
        
        # Calculate score with proper weights
        score = (front_rank * 0.15 +      # Front hand less important
                middle_rank * 0.35 +      # Middle hand medium importance  
                back_rank * 0.5 +         # Back hand most important
                fantasy_bonus)
        
        # Normalize
        return min(score / 10.0, 1.0)
    
    def _is_initial_placement_complete(self, state: PineappleStateJoker) -> bool:
        """Check if initial 5 cards are placed."""
        return self._count_placed_cards(state) == 5
    
    def _count_placed_cards(self, state: PineappleStateJoker) -> int:
        """Count total placed cards."""
        return (len(state.front_hand.cards) + 
                len(state.middle_hand.cards) + 
                len(state.back_hand.cards))
    
    def _select_child(self, node: PineappleMCTSNodeJoker) -> PineappleMCTSNodeJoker:
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
    
    def _add_child(self, node: PineappleMCTSNodeJoker, action) -> PineappleMCTSNodeJoker:
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
        
        child = PineappleMCTSNodeJoker(new_state, parent=node, action=action,
                                      remaining_deck=new_deck)
        node.children.append(child)
        return child
    
    def _extract_best_initial_placement(self, root: PineappleMCTSNodeJoker) -> PineappleStateJoker:
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
            if best_child.state.has_fantasy_land():
                print("✨ Fantasy Land achieved!")
            return best_child.state
        else:
            print("\nNo complete initial placement found, using heuristic")
            # Fallback to heuristic
            state = PineappleStateJoker()
            cards = root.remaining_deck[:5]
            
            # Smart heuristic for jokers
            jokers = [c for c in cards if c.is_joker()]
            regular = [c for c in cards if not c.is_joker()]
            sorted_regular = sorted(regular, key=lambda c: RANK_VALUES[c.rank], reverse=True)
            
            if jokers:
                # Place joker in front for Fantasy Land potential
                state.place_card(jokers[0], 'front')
                remaining = sorted_regular + jokers[1:]
            else:
                remaining = sorted_regular
            
            # Place remaining cards
            if len(remaining) >= 4:
                state.place_card(remaining[0], 'back')
                state.place_card(remaining[1], 'back')
                state.place_card(remaining[2], 'middle')
                state.place_card(remaining[3], 'middle')
            if len(remaining) >= 5:
                state.place_card(remaining[4], 'front')
            
            return state


def main():
    """Test the Pineapple solver with jokers."""
    solver = PineappleOFCSolverJoker(num_simulations=5000)
    
    # Test case 1: Regular cards
    print("=== Test 1: Regular cards ===")
    cards1 = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    result1 = solver.solve_initial_five(cards1)
    print_result(result1)
    
    # Test case 2: Cards with one joker
    print("\n=== Test 2: Cards with one joker ===")
    cards2 = [
        Card.from_string("As"),
        Card.from_string("Kh"),
        Card.from_string("Qd"),
        Card.from_string("Jc"),
        Card.joker()
    ]
    
    result2 = solver.solve_initial_five(cards2)
    print_result(result2)
    
    # Test case 3: Cards with two jokers
    print("\n=== Test 3: Cards with two jokers ===")
    cards3 = [
        Card.from_string("As"),
        Card.from_string("Ks"),
        Card.from_string("5h"),
        Card.joker(),
        Card.joker()
    ]
    
    result3 = solver.solve_initial_five(cards3)
    print_result(result3)


def print_result(result: PineappleStateJoker):
    """Print the result of a solve."""
    print("\n最佳初始擺放:")
    print(f"前墩: {' '.join(str(c) for c in result.front_hand.cards)}")
    
    # Show optimal joker assignment for front hand
    if any(c.is_joker() for c in result.front_hand.cards):
        _, _, best_front = JokerHandEvaluator.evaluate_with_jokers(result.front_hand.cards)
        print(f"  (最佳配置: {' '.join(str(c) for c in best_front)})")
    
    print(f"中墩: {' '.join(str(c) for c in result.middle_hand.cards)}")
    if any(c.is_joker() for c in result.middle_hand.cards):
        _, _, best_middle = JokerHandEvaluator.evaluate_with_jokers(result.middle_hand.cards)
        print(f"  (最佳配置: {' '.join(str(c) for c in best_middle)})")
    
    print(f"後墩: {' '.join(str(c) for c in result.back_hand.cards)}")
    if any(c.is_joker() for c in result.back_hand.cards):
        _, _, best_back = JokerHandEvaluator.evaluate_with_jokers(result.back_hand.cards)
        print(f"  (最佳配置: {' '.join(str(c) for c in best_back)})")
    
    if result.is_valid():
        print("\n✓ 有效擺放")
        if result.has_fantasy_land():
            print("✨ 進入 Fantasy Land!")
    else:
        print("\n✗ 無效擺放")


if __name__ == "__main__":
    main()