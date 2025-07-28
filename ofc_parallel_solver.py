#!/usr/bin/env python3
"""
Parallel OFC MCTS Solver
Simplified version with correct attribute names.
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from ofc_solver_fixed import Card, Hand, PlayerArrangement, RANKS, SUITS, RANK_VALUES


def run_mcts_worker(args):
    """Worker function for parallel MCTS."""
    worker_id, num_simulations, initial_cards, seed = args
    
    # Set random seed for reproducibility
    random.seed(seed + worker_id)
    
    # Generate remaining deck
    full_deck = [Card(rank=r, suit=s) for r in RANKS for s in SUITS]
    remaining_deck = [c for c in full_deck 
                     if not any(c.rank == card.rank and c.suit == card.suit 
                               for card in initial_cards)]
    
    # Track best arrangements found
    best_arrangements = []
    
    # Run simulations
    for _ in range(num_simulations):
        arrangement = simulate_random_placement(initial_cards, remaining_deck)
        if arrangement and arrangement['valid']:
            best_arrangements.append(arrangement)
    
    # Sort by score and return top arrangements
    best_arrangements.sort(key=lambda x: x['score'], reverse=True)
    return best_arrangements[:10]  # Return top 10


def simulate_random_placement(initial_cards: List[Card], remaining_deck: List[Card]) -> Optional[Dict]:
    """Simulate a random placement and evaluate it."""
    arrangement = PlayerArrangement()
    all_cards = initial_cards + random.sample(remaining_deck, 8)  # Total 13 cards
    
    # Place initial 5 cards using heuristics
    placed_initial = place_initial_cards_heuristic(arrangement, initial_cards)
    if not placed_initial:
        return None
    
    # Place remaining 8 cards randomly but validly
    remaining_8 = all_cards[5:]
    for card in remaining_8:
        positions = arrangement.get_available_positions()
        if not positions:
            break
        
        # Try to place card in a valid position
        random.shuffle(positions)
        placed = False
        
        for pos in positions:
            test_arrangement = arrangement.copy()
            test_arrangement.add_card_to_hand(card, pos)
            
            # Check if still potentially valid
            if is_potentially_valid(test_arrangement):
                arrangement.add_card_to_hand(card, pos)
                placed = True
                break
        
        if not placed:
            # Force placement in first available position
            arrangement.add_card_to_hand(card, positions[0])
    
    # Evaluate final arrangement
    if not arrangement.all_hands_full():
        return None
    
    is_valid = arrangement.is_valid()
    score = evaluate_arrangement(arrangement) if is_valid else 0
    
    return {
        'arrangement': arrangement,
        'valid': is_valid,
        'score': score,
        'initial_placement': get_initial_placement(arrangement, initial_cards)
    }


def place_initial_cards_heuristic(arrangement: PlayerArrangement, cards: List[Card]) -> bool:
    """Place initial 5 cards using smart heuristics."""
    # Analyze cards
    rank_counts = defaultdict(int)
    suit_counts = defaultdict(int)
    
    for card in cards:
        rank_counts[card.rank] += 1
        suit_counts[card.suit] += 1
    
    # Sort cards by value
    sorted_cards = sorted(cards, key=lambda c: RANK_VALUES[c.rank], reverse=True)
    placed_cards = set()
    
    # Priority 1: Place trips
    for rank, count in rank_counts.items():
        if count >= 3:
            cards_of_rank = [c for c in cards if c.rank == rank]
            # Place 3 in back
            for c in cards_of_rank[:3]:
                arrangement.back_hand.add_card(c)
                placed_cards.add(id(c))
    
    # Priority 2: Place pairs
    pairs = [(rank, count) for rank, count in rank_counts.items() if count == 2]
    pairs.sort(key=lambda x: RANK_VALUES[x[0]], reverse=True)
    
    for rank, _ in pairs[:2]:  # Maximum 2 pairs
        cards_of_rank = [c for c in cards if c.rank == rank and id(c) not in placed_cards]
        if len(cards_of_rank) >= 2:
            if len(arrangement.back_hand.cards) <= 3:
                # Place higher pair in back
                for c in cards_of_rank[:2]:
                    arrangement.back_hand.add_card(c)
                    placed_cards.add(id(c))
            elif len(arrangement.middle_hand.cards) <= 3:
                # Place lower pair in middle
                for c in cards_of_rank[:2]:
                    arrangement.middle_hand.add_card(c)
                    placed_cards.add(id(c))
    
    # Priority 3: Check for flush/straight potential
    flush_potential = max(suit_counts.values()) >= 3
    
    # Place remaining cards
    remaining = [c for c in sorted_cards if id(c) not in placed_cards]
    
    for card in remaining:
        if len(arrangement.back_hand.cards) < 2:
            arrangement.back_hand.add_card(card)
        elif len(arrangement.middle_hand.cards) < 2:
            arrangement.middle_hand.add_card(card)
        else:
            arrangement.front_hand.add_card(card)
    
    return True


def is_potentially_valid(arrangement: PlayerArrangement) -> bool:
    """Check if arrangement could potentially be valid when complete."""
    # Get current hand evaluations
    hands_info = []
    
    for hand_name, hand in [('front', arrangement.front_hand),
                            ('middle', arrangement.middle_hand),
                            ('back', arrangement.back_hand)]:
        if hand.cards:
            rank, _ = hand.evaluate()
            hands_info.append((hand_name, rank, len(hand.cards), hand.max_size))
    
    # Check basic validity rules
    # If we have evaluations for multiple hands, check ordering
    if len(hands_info) >= 2:
        for i in range(len(hands_info) - 1):
            curr_hand = hands_info[i]
            next_hand = hands_info[i + 1]
            
            # If both hands are complete, check ranking
            if curr_hand[2] == curr_hand[3] and next_hand[2] == next_hand[3]:
                if curr_hand[0] == 'back' and next_hand[0] == 'middle':
                    if curr_hand[1] < next_hand[1]:
                        return False
                elif curr_hand[0] == 'middle' and next_hand[0] == 'front':
                    if curr_hand[1] < next_hand[1]:
                        return False
    
    return True


def evaluate_arrangement(arrangement: PlayerArrangement) -> float:
    """Evaluate the quality of a complete arrangement."""
    if not arrangement.is_valid():
        return 0.0
    
    score = 0.0
    
    # Evaluate each hand
    front_rank, _ = arrangement.front_hand.evaluate()
    middle_rank, _ = arrangement.middle_hand.evaluate()
    back_rank, _ = arrangement.back_hand.evaluate()
    
    # Base scores for hand strength
    score += front_rank * 10     # Front hand multiplier
    score += middle_rank * 20    # Middle hand multiplier
    score += back_rank * 30      # Back hand multiplier
    
    # Bonus for special hands
    if front_rank >= 1:  # Pair or better in front
        score += 50
    if middle_rank >= 4:  # Straight or better in middle
        score += 100
    if back_rank >= 4:  # Straight or better in back
        score += 150
    
    # Penalty for barely valid arrangements
    if back_rank == middle_rank and middle_rank == front_rank:
        score *= 0.8
    
    return score


def get_initial_placement(arrangement: PlayerArrangement, initial_cards: List[Card]) -> PlayerArrangement:
    """Extract just the initial card placements."""
    initial_arrangement = PlayerArrangement()
    
    # Check each card in each hand
    for card in arrangement.front_hand.cards:
        if any(c.rank == card.rank and c.suit == card.suit for c in initial_cards):
            initial_arrangement.front_hand.add_card(card)
    
    for card in arrangement.middle_hand.cards:
        if any(c.rank == card.rank and c.suit == card.suit for c in initial_cards):
            initial_arrangement.middle_hand.add_card(card)
    
    for card in arrangement.back_hand.cards:
        if any(c.rank == card.rank and c.suit == card.suit for c in initial_cards):
            initial_arrangement.back_hand.add_card(card)
    
    return initial_arrangement


class ParallelOFCSolver:
    """Parallel solver for OFC initial placement."""
    
    def __init__(self, num_workers=None, simulations_per_worker=100):
        self.num_workers = num_workers or mp.cpu_count()
        self.simulations_per_worker = simulations_per_worker
    
    def solve_initial_five(self, cards: List[Card]) -> PlayerArrangement:
        """Find optimal placement for initial 5 cards using parallel search."""
        print(f"\nParallel OFC Solver")
        print(f"Cards: {' '.join(str(c) for c in cards)}")
        print(f"Workers: {self.num_workers}")
        print(f"Simulations per worker: {self.simulations_per_worker}")
        
        start_time = time.time()
        
        # Prepare worker arguments
        base_seed = random.randint(0, 1000000)
        worker_args = [
            (i, self.simulations_per_worker, cards, base_seed)
            for i in range(self.num_workers)
        ]
        
        # Run parallel simulations
        all_results = []
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(run_mcts_worker, args) for args in worker_args]
            
            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        # Find best arrangement
        if not all_results:
            print("No valid arrangements found! Using fallback heuristic.")
            return self._fallback_placement(cards)
        
        # Sort all results by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        best = all_results[0]
        
        elapsed = time.time() - start_time
        
        print(f"\nFound {len(all_results)} valid arrangements")
        print(f"Best score: {best['score']:.1f}")
        print(f"Time: {elapsed:.2f}s")
        
        return best['initial_placement']
    
    def _fallback_placement(self, cards: List[Card]) -> PlayerArrangement:
        """Simple fallback placement."""
        arrangement = PlayerArrangement()
        place_initial_cards_heuristic(arrangement, cards)
        return arrangement


def main():
    """Demo the parallel solver."""
    print("=== Parallel OFC Solver Demo ===")
    
    # Test cases
    test_hands = [
        # Royal flush potential
        ["As", "Ks", "Qs", "Js", "Ts"],
        # Two pair
        ["As", "Ah", "Kd", "Kc", "Qs"],
        # Trips
        ["As", "Ah", "Ad", "Kc", "Qs"],
        # Mixed high cards
        ["As", "Kd", "Qh", "Jc", "9s"],
    ]
    
    solver = ParallelOFCSolver(num_workers=4, simulations_per_worker=250)
    
    for i, card_strings in enumerate(test_hands):
        print(f"\n{'='*50}")
        print(f"Test {i+1}: {' '.join(card_strings)}")
        print('='*50)
        
        cards = [Card.from_string(cs) for cs in card_strings]
        
        arrangement = solver.solve_initial_five(cards)
        
        print("\nBest Initial Placement:")
        print(arrangement)
        
        # Verify all cards placed
        total = (len(arrangement.front_hand.cards) + 
                len(arrangement.middle_hand.cards) + 
                len(arrangement.back_hand.cards))
        print(f"\nCards placed: {total}/5")


if __name__ == "__main__":
    main()