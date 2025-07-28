"""
Performance benchmark tests for OFC Solver.

Tests the performance of critical components to ensure they meet
speed requirements.
"""

import pytest
import time
import random
import memory_profiler
import cProfile
import pstats
import io
from contextlib import contextmanager
from typing import List, Callable, Tuple

from src.core.domain import Card, GameState, CardSet
from src.core.domain.hand import Hand
from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSConfig
from src.core.algorithms.evaluator import StateEvaluator
from src.ofc_solver import OFCSolver


@contextmanager
def time_limit(seconds: float):
    """Context manager to ensure code runs within time limit."""
    start_time = time.time()
    yield
    elapsed = time.time() - start_time
    assert elapsed < seconds, f"Exceeded time limit: {elapsed:.3f}s > {seconds}s"


@contextmanager
def profile_code():
    """Context manager for profiling code execution."""
    pr = cProfile.Profile()
    pr.enable()
    yield pr
    pr.disable()


class TestCardPerformance:
    """Performance tests for Card operations."""
    
    def test_card_creation_speed(self):
        """Test speed of creating many cards."""
        with time_limit(0.1):  # 100ms for 10,000 cards
            cards = []
            for i in range(10000):
                cards.append(Card(i % 52))
        
        assert len(cards) == 10000
    
    def test_card_string_parsing_speed(self):
        """Test speed of parsing card strings."""
        card_strings = []
        ranks = "23456789TJQKA"
        suits = "shdc"
        
        # Generate all possible card strings
        for rank in ranks:
            for suit in suits:
                card_strings.append(f"{rank}{suit}")
        
        with time_limit(0.05):  # 50ms to parse all cards 100 times
            for _ in range(100):
                cards = [Card.from_string(s) for s in card_strings]
        
        assert len(cards) == 52
    
    def test_card_comparison_speed(self):
        """Test speed of card comparisons."""
        cards = Card.deck()
        
        with time_limit(0.1):  # 100ms for sorting 1000 decks
            for _ in range(1000):
                sorted_cards = sorted(cards)
        
        assert len(sorted_cards) == 52


class TestCardSetPerformance:
    """Performance tests for CardSet operations."""
    
    def test_cardset_operations_speed(self):
        """Test speed of set operations."""
        # Create random card sets
        all_cards = Card.deck()
        sets = []
        for _ in range(100):
            random.shuffle(all_cards)
            sets.append(CardSet.from_cards(all_cards[:26]))
        
        with time_limit(0.1):  # 100ms for 1000 operations
            for _ in range(10):
                for i in range(len(sets)-1):
                    union = sets[i] | sets[i+1]
                    intersection = sets[i] & sets[i+1]
                    difference = sets[i] - sets[i+1]
        
        assert len(union) >= len(intersection)
    
    def test_cardset_membership_speed(self):
        """Test speed of membership testing."""
        full_deck = CardSet.full_deck()
        cards = Card.deck()
        
        with time_limit(0.05):  # 50ms for 100,000 membership tests
            for _ in range(100000):
                card = random.choice(cards)
                _ = card in full_deck
    
    def test_cardset_iteration_speed(self):
        """Test speed of iterating over card sets."""
        full_deck = CardSet.full_deck()
        
        with time_limit(0.1):  # 100ms to iterate 1000 times
            count = 0
            for _ in range(1000):
                for card in full_deck:
                    count += 1
        
        assert count == 52000  # 52 cards * 1000 iterations


class TestHandEvaluationPerformance:
    """Performance tests for hand evaluation."""
    
    def test_hand_evaluation_speed(self):
        """Test speed of evaluating poker hands."""
        # Generate random 5-card hands
        deck = Card.deck()
        hands = []
        for _ in range(1000):
            random.shuffle(deck)
            hands.append(Hand(deck[:5]))
        
        with time_limit(0.5):  # 500ms to evaluate 1000 hands
            for hand in hands:
                _ = hand.hand_type
    
    def test_three_card_evaluation_speed(self):
        """Test speed of evaluating 3-card hands."""
        deck = Card.deck()
        hands = []
        for _ in range(1000):
            random.shuffle(deck)
            hands.append(Hand(deck[:3]))
        
        with time_limit(0.3):  # 300ms to evaluate 1000 3-card hands
            for hand in hands:
                _ = hand.hand_type
    
    def test_hand_comparison_speed(self):
        """Test speed of comparing hands."""
        deck = Card.deck()
        hands = []
        for _ in range(100):
            random.shuffle(deck)
            hands.append(Hand(deck[:5]))
        
        with time_limit(0.1):  # 100ms for all comparisons
            for i in range(len(hands)):
                for j in range(i+1, len(hands)):
                    _ = hands[i] < hands[j]


class TestGameStatePerformance:
    """Performance tests for game state operations."""
    
    def test_game_state_copy_speed(self):
        """Test speed of copying game states."""
        gs = GameState(seed=42)
        
        # Setup some state
        gs.deal_street()
        cards = gs.current_hand
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        gs.place_cards(placements)
        
        with time_limit(0.5):  # 500ms for 1000 copies
            copies = []
            for _ in range(1000):
                copies.append(gs.copy())
        
        assert len(copies) == 1000
        assert all(c.player_arrangement.cards_placed == 5 for c in copies)
    
    def test_game_simulation_speed(self):
        """Test speed of simulating complete games."""
        def simulate_random_game():
            gs = GameState(seed=random.randint(0, 10000))
            
            while not gs.is_complete:
                gs.deal_street()
                cards = gs.current_hand
                
                if gs.current_street == Street.INITIAL:
                    # Place all 5 cards
                    placements = []
                    for i, (pos, idx) in enumerate([
                        ('front', 0), ('front', 1), ('middle', 0),
                        ('back', 0), ('back', 1)
                    ]):
                        placements.append((cards[i], pos, idx))
                    gs.place_cards(placements)
                else:
                    # Place 2, discard 1
                    placements = [
                        (cards[0], 'middle', gs.player_arrangement.cards_placed % 5),
                        (cards[1], 'back', gs.player_arrangement.cards_placed % 5)
                    ]
                    gs.place_cards(placements, discard=cards[2])
        
        with time_limit(1.0):  # 1 second for 100 games
            for _ in range(100):
                simulate_random_game()


class TestMCTSPerformance:
    """Performance tests for MCTS algorithm."""
    
    def test_mcts_simulation_rate(self):
        """Test MCTS simulation rate."""
        engine = MCTSEngine(MCTSConfig(time_limit=1.0))  # 1 second
        gs = GameState(seed=42)
        gs.deal_street()
        
        start_time = time.time()
        result = engine.search(gs)
        elapsed = time.time() - start_time
        
        simulations_per_second = engine.simulations_run / elapsed
        
        # Should achieve at least 100 simulations per second
        assert simulations_per_second > 100, f"Too slow: {simulations_per_second:.1f} sims/sec"
        
        print(f"\nMCTS Performance: {simulations_per_second:.1f} simulations/second")
    
    def test_mcts_parallel_speedup(self):
        """Test that parallel MCTS is faster."""
        gs = GameState(seed=42)
        gs.deal_street()
        
        # Single-threaded
        engine1 = MCTSEngine(MCTSConfig(num_simulations=100, num_threads=1))
        start = time.time()
        result1 = engine1.search(gs.copy())
        time1 = time.time() - start
        
        # Multi-threaded
        engine2 = MCTSEngine(MCTSConfig(num_simulations=100, num_threads=2))
        start = time.time()
        result2 = engine2.search(gs.copy())
        time2 = time.time() - start
        
        # Parallel should be faster (allowing some overhead)
        speedup = time1 / time2
        print(f"\nParallel speedup: {speedup:.2f}x")
        
        # Should have some speedup (at least 1.2x)
        assert speedup > 1.2, f"Insufficient speedup: {speedup:.2f}x"
    
    def test_mcts_memory_usage(self):
        """Test MCTS memory usage stays reasonable."""
        engine = MCTSEngine(MCTSConfig(num_simulations=1000))
        gs = GameState(seed=42)
        gs.deal_street()
        
        # Measure memory before
        import tracemalloc
        tracemalloc.start()
        
        # Run search
        result = engine.search(gs)
        
        # Measure memory after
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Convert to MB
        peak_mb = peak / 1024 / 1024
        
        print(f"\nMCTS peak memory usage: {peak_mb:.1f} MB")
        
        # Should use less than 100 MB for 1000 simulations
        assert peak_mb < 100, f"Excessive memory usage: {peak_mb:.1f} MB"


class TestSolverPerformance:
    """Performance tests for the complete solver."""
    
    def test_solver_initial_decision_speed(self):
        """Test speed of making initial placement decision."""
        solver = OFCSolver()
        
        # Create initial hand
        cards = [
            Card.from_string("As"), Card.from_string("Kh"),
            Card.from_string("Qd"), Card.from_string("Jc"),
            Card.from_string("Ts")
        ]
        
        with time_limit(5.0):  # 5 seconds for initial decision
            action = solver.get_action(cards, time_limit=1.0)
        
        assert action is not None
        assert len(action['placements']) == 5
    
    def test_solver_subsequent_decision_speed(self):
        """Test speed of subsequent placement decisions."""
        solver = OFCSolver()
        
        # Setup game state
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        # Make initial placement
        cards = game_state.current_hand
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        game_state.place_cards(placements)
        
        # Deal next street
        game_state.deal_street()
        cards = game_state.current_hand
        
        with time_limit(3.0):  # 3 seconds for subsequent decision
            action = solver.get_action(
                cards,
                game_state=game_state,
                time_limit=1.0
            )
        
        assert action is not None
        assert len(action['placements']) == 2
        assert action['discard'] is not None


class TestProfileAnalysis:
    """Profiling tests to identify bottlenecks."""
    
    def test_profile_hand_evaluation(self):
        """Profile hand evaluation to find bottlenecks."""
        deck = Card.deck()
        hands = []
        for _ in range(1000):
            random.shuffle(deck)
            hands.append(Hand(deck[:5]))
        
        with profile_code() as pr:
            for hand in hands:
                _ = hand.hand_type
        
        # Analyze profile
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        
        profile_output = s.getvalue()
        print("\nHand Evaluation Profile (Top 10):")
        print(profile_output)
    
    def test_profile_mcts_search(self):
        """Profile MCTS search to find bottlenecks."""
        engine = MCTSEngine(MCTSConfig(num_simulations=100))
        gs = GameState(seed=42)
        gs.deal_street()
        
        with profile_code() as pr:
            result = engine.search(gs)
        
        # Analyze profile
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        
        profile_output = s.getvalue()
        print("\nMCTS Search Profile (Top 10):")
        print(profile_output)


# Benchmark summary function
def run_performance_summary():
    """Run and summarize all performance benchmarks."""
    print("\n" + "="*60)
    print("OFC Solver Performance Benchmark Summary")
    print("="*60)
    
    benchmarks = [
        ("Card Operations", TestCardPerformance),
        ("CardSet Operations", TestCardSetPerformance),
        ("Hand Evaluation", TestHandEvaluationPerformance),
        ("Game State", TestGameStatePerformance),
        ("MCTS Algorithm", TestMCTSPerformance),
        ("Complete Solver", TestSolverPerformance),
    ]
    
    for name, test_class in benchmarks:
        print(f"\n{name}:")
        test_instance = test_class()
        
        for method_name in dir(test_instance):
            if method_name.startswith('test_'):
                try:
                    method = getattr(test_instance, method_name)
                    start_time = time.time()
                    method()
                    elapsed = time.time() - start_time
                    print(f"  ✓ {method_name}: {elapsed:.3f}s")
                except AssertionError as e:
                    print(f"  ✗ {method_name}: FAILED - {e}")
                except Exception as e:
                    print(f"  ✗ {method_name}: ERROR - {e}")


if __name__ == "__main__":
    run_performance_summary()