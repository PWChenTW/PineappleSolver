#!/usr/bin/env python3
"""
Test script for OFC Solver.

Demonstrates solving OFC positions using MCTS.
"""

import sys
sys.path.append('.')

import time
from src.core.domain import GameState, Card, Street
from src.ofc_solver import create_solver, SolverConfig


def test_initial_placement():
    """Test solving initial 5-card placement."""
    print("=== Testing Initial Placement ===\n")
    
    # Create game state
    game = GameState(num_players=2, player_index=0, seed=42)
    
    # Deal initial cards
    initial_cards = game.deal_street()
    print(f"Initial cards: {' '.join(str(c) for c in initial_cards)}")
    
    # Create solver with short time limit for testing
    solver = create_solver(time_limit=10.0, num_threads=1)
    
    # Progress callback
    def progress(sims, elapsed, status):
        if sims % 100 == 0:
            print(f"\r{status} - {elapsed:.1f}s", end='', flush=True)
    
    # Solve position
    print("\nSolving position...")
    result = solver.solve(game, progress)
    print(f"\n\nSolution found in {result.time_taken:.2f}s with {result.num_simulations} simulations")
    
    # Display best action
    if result.best_action:
        print("\nBest action:")
        for card, pos, idx in result.best_action.placements:
            print(f"  Place {card} at {pos}[{idx}]")
    
    # Apply action and show result
    game.place_cards(result.best_action.placements)
    print(f"\nAfter placement:")
    print(game.player_arrangement)
    
    # Analyze position
    analysis = solver.analyze_position(game)
    print(f"\nPosition analysis:")
    print(f"  Expected score: {analysis['expected_score']:.2f}")
    print(f"  Foul risk: {analysis['foul_risk']:.2%}")


def test_regular_street():
    """Test solving a regular street (3 cards, place 2, discard 1)."""
    print("\n\n=== Testing Regular Street ===\n")
    
    # Create game with some cards already placed
    game = GameState(num_players=2, player_index=0, seed=123)
    
    # Simulate initial placement
    initial_cards = game.deal_street()
    print(f"Initial setup: {' '.join(str(c) for c in initial_cards)}")
    
    # Place initial cards in a reasonable way
    placements = [
        (initial_cards[0], 'front', 0),
        (initial_cards[1], 'front', 1),
        (initial_cards[2], 'middle', 0),
        (initial_cards[3], 'back', 0),
        (initial_cards[4], 'back', 1),
    ]
    game.place_cards(placements)
    print("Initial placement complete")
    print(game.player_arrangement)
    
    # Deal street 1
    street1_cards = game.deal_street()
    print(f"\n\nStreet 1 cards: {' '.join(str(c) for c in street1_cards)}")
    
    # Create solver
    solver = create_solver(time_limit=10.0, num_threads=1)
    
    # Solve
    print("\nSolving position...")
    result = solver.solve(game)
    print(f"Solution found in {result.time_taken:.2f}s")
    
    # Display best action
    if result.best_action:
        print("\nBest action:")
        for card, pos, idx in result.best_action.placements:
            print(f"  Place {card} at {pos}[{idx}]")
        print(f"  Discard {result.best_action.discard}")
    
    # Apply and show
    game.place_cards(result.best_action.placements, result.best_action.discard)
    print(f"\nAfter street 1:")
    print(game.player_arrangement)


def test_complete_game():
    """Test solving a complete game."""
    print("\n\n=== Testing Complete Game ===\n")
    
    # Create solver with reasonable time limit
    solver = create_solver(time_limit=30.0, num_threads=2)
    
    # Progress callback
    def game_progress(status):
        print(f"  {status}")
    
    # Solve complete game
    print("Solving complete game...")
    start_time = time.time()
    
    game_state = GameState(num_players=2, player_index=0, seed=456)
    results = solver.solve_game(game_state, game_progress)
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n\nGame complete in {total_time:.2f}s")
    print(f"Total decisions: {len(results)}")
    print(f"Total simulations: {sum(r.num_simulations for r in results)}")
    
    # Show final arrangement
    print(f"\nFinal arrangement:")
    print(game_state)
    
    # Analyze final position
    analysis = solver.analyze_position(game_state)
    print(f"\nFinal analysis:")
    print(f"  Expected score: {analysis['expected_score']:.2f}")
    if analysis['royalties']:
        print(f"  Royalties: F={analysis['royalties']['front']}, "
              f"M={analysis['royalties']['middle']}, "
              f"B={analysis['royalties']['back']} "
              f"(Total={analysis['royalties']['total']})")


def test_difficult_position():
    """Test a difficult position with high foul risk."""
    print("\n\n=== Testing Difficult Position ===\n")
    
    # Create a position with pair in front
    game = GameState(num_players=2, player_index=0)
    
    # Manually place cards to create difficult position
    game.player_arrangement.place_card(Card.from_string("Kh"), 'front', 0)
    game.player_arrangement.place_card(Card.from_string("Kd"), 'front', 1)
    game.player_arrangement.place_card(Card.from_string("Ac"), 'middle', 0)
    game.player_arrangement.place_card(Card.from_string("2h"), 'middle', 1)
    game.player_arrangement.place_card(Card.from_string("3d"), 'back', 0)
    game.player_arrangement.place_card(Card.from_string("4s"), 'back', 1)
    
    # Mark these cards as used
    for card in [Card.from_string(s) for s in ["Kh", "Kd", "Ac", "2h", "3d", "4s"]]:
        game._player_arrangement._used_cards.add(card)
    
    print("Current position (KK in front):")
    print(game.player_arrangement)
    
    # Manually set current hand for next street
    game._current_street = Street.SECOND
    game._current_hand = [
        Card.from_string("Ah"),
        Card.from_string("As"),
        Card.from_string("5c")
    ]
    
    print(f"\nNext cards: {' '.join(str(c) for c in game._current_hand)}")
    print("Challenge: Need to avoid fouling with KK in front!")
    
    # Solve with more time
    solver = create_solver(time_limit=20.0, num_threads=2)
    
    print("\nSolving difficult position...")
    result = solver.solve(game)
    
    print(f"\nSolution found in {result.time_taken:.2f}s")
    if result.best_action:
        print("Best action:")
        for card, pos, idx in result.best_action.placements:
            print(f"  Place {card} at {pos}[{idx}]")
        print(f"  Discard {result.best_action.discard}")
    
    # Analyze
    analysis = solver.analyze_position(game)
    print(f"\nPosition analysis:")
    print(f"  Foul risk: {analysis['foul_risk']:.2%}")
    print(f"  Expected score: {analysis['expected_score']:.2f}")


def main():
    """Run all tests."""
    print("OFC Solver Test Suite")
    print("=" * 50)
    
    test_initial_placement()
    test_regular_street()
    test_complete_game()
    test_difficult_position()
    
    print("\n\nAll tests completed!")


if __name__ == "__main__":
    main()