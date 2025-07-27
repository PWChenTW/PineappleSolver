#!/usr/bin/env python3
"""
Example usage of OFC Solver.

This script demonstrates how to use the solver in different scenarios.
"""

import sys
sys.path.append('.')

from src.core.domain import GameState, Card
from src.core.domain.game_state import Street
from src.ofc_solver import create_solver


def example_solve_initial_hand():
    """Example: Solve initial 5-card placement."""
    print("=== Example 1: Initial Hand Placement ===\n")
    
    # Create solver
    solver = create_solver(time_limit=30.0, num_threads=4)
    
    # Create game and deal initial cards
    game = GameState(num_players=2, player_index=0, seed=42)
    cards = game.deal_street()
    
    print(f"Your cards: {' '.join(str(c) for c in cards)}")
    print("\nFinding optimal placement...\n")
    
    # Solve
    result = solver.solve(game)
    
    # Display solution
    print("Optimal placement:")
    for card, position, index in result.best_action.placements:
        print(f"  {card} → {position} position {index}")
    
    print(f"\nExpected score: {result.expected_score:.2f}")
    print(f"Simulations run: {result.num_simulations:,}")
    print(f"Time taken: {result.time_taken:.2f} seconds")


def example_solve_difficult_position():
    """Example: Solve a difficult mid-game position."""
    print("\n\n=== Example 2: Difficult Position ===\n")
    
    # Create a challenging position
    game = GameState(num_players=2, player_index=0)
    
    # Set up a risky position (QQ in front)
    placements = [
        (Card.from_string("Qh"), 'front', 0),
        (Card.from_string("Qd"), 'front', 1),
        (Card.from_string("7c"), 'middle', 0),
        (Card.from_string("8s"), 'middle', 1),
        (Card.from_string("9h"), 'middle', 2),
        (Card.from_string("2d"), 'back', 0),
        (Card.from_string("3c"), 'back', 1),
        (Card.from_string("4s"), 'back', 2),
    ]
    
    for card, pos, idx in placements:
        game.player_arrangement.place_card(card, pos, idx)
    
    # Update game state
    game._player_arrangement._used_cards.add(Card.from_string("Qh"))
    game._player_arrangement._used_cards.add(Card.from_string("Qd"))
    game._player_arrangement._used_cards.add(Card.from_string("7c"))
    game._player_arrangement._used_cards.add(Card.from_string("8s"))
    game._player_arrangement._used_cards.add(Card.from_string("9h"))
    game._player_arrangement._used_cards.add(Card.from_string("2d"))
    game._player_arrangement._used_cards.add(Card.from_string("3c"))
    game._player_arrangement._used_cards.add(Card.from_string("4s"))
    game._current_street = Street.SECOND
    
    print("Current position:")
    print(game.player_arrangement)
    print("\nChallenge: We have QQ in front - need strong hands in middle/back!")
    
    # Simulate next 3 cards
    game._current_hand = [
        Card.from_string("Th"),
        Card.from_string("Jd"),
        Card.from_string("5h")
    ]
    
    print(f"\nNext cards: {' '.join(str(c) for c in game._current_hand)}")
    
    # Create solver and analyze
    solver = create_solver(time_limit=30.0, num_threads=4)
    
    # First analyze the position
    analysis = solver.analyze_position(game)
    print(f"\nPosition analysis:")
    print(f"  Foul risk: {analysis['foul_risk']:.1%}")
    print(f"  Expected score: {analysis['expected_score']:.2f}")
    
    # Now solve
    print("\nFinding best move...")
    result = solver.solve(game)
    
    print("\nBest action:")
    for card, pos, idx in result.best_action.placements:
        print(f"  Place {card} at {pos}[{idx}]")
    print(f"  Discard {result.best_action.discard}")


def example_complete_game():
    """Example: Play a complete game with solver."""
    print("\n\n=== Example 3: Complete Game ===\n")
    
    solver = create_solver(time_limit=20.0, num_threads=4)
    
    def progress_callback(status):
        print(f"  {status}")
    
    print("Playing complete game with solver...\n")
    
    # Play complete game
    game_state = GameState(num_players=2, player_index=0, seed=789)
    results = solver.solve_game(game_state, progress_callback)
    
    print(f"\n\nGame Summary:")
    print(f"  Total decisions: {len(results)}")
    print(f"  Total simulations: {sum(r.num_simulations for r in results):,}")
    print(f"  Average time per decision: {sum(r.time_taken for r in results) / len(results):.2f}s")
    
    # Show final position
    print(f"\nFinal arrangement:")
    print(game_state)
    
    # Final analysis
    if game_state.is_complete:
        is_valid, error = game_state.player_arrangement.is_valid()
        if is_valid:
            royalties = game_state.player_arrangement.calculate_royalties()
            print(f"\nRoyalties earned:")
            print(f"  Front: {royalties.front}")
            print(f"  Middle: {royalties.middle}")
            print(f"  Back: {royalties.back}")
            print(f"  Total: {royalties.total}")
            
            if game_state.player_arrangement.qualifies_for_fantasyland():
                print("\n🎉 Qualified for FANTASYLAND!")
        else:
            print(f"\n❌ FOULED: {error}")


def example_custom_analysis():
    """Example: Custom position analysis."""
    print("\n\n=== Example 4: Custom Analysis ===\n")
    
    # You can input your own position here
    print("Setting up custom position...")
    
    game = GameState(num_players=2, player_index=0)
    
    # Example: Analyzing a specific hand combination
    cards_to_analyze = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    game._current_hand = cards_to_analyze
    game._current_street = Street.INITIAL
    
    print(f"Cards to place: {' '.join(str(c) for c in cards_to_analyze)}")
    print("\nThis is a strong starting hand with two pairs (AA and KK).")
    print("Let's see how the solver handles it...\n")
    
    solver = create_solver(time_limit=60.0, num_threads=4)
    
    # Progress callback for detailed info
    def detailed_progress(sims, elapsed, status):
        if sims % 1000 == 0:
            print(f"\r{status} [{elapsed:.1f}s]", end='', flush=True)
    
    result = solver.solve(game, detailed_progress)
    print("\n\nOptimal placement found:")
    
    for card, pos, idx in result.best_action.placements:
        print(f"  {card} → {pos}[{idx}]")
    
    # Apply the action to see the result
    game.place_cards(result.best_action.placements)
    print(f"\nResulting arrangement:")
    print(game.player_arrangement)
    
    # Show statistics
    print(f"\nSolver statistics:")
    print(f"  Expected score: {result.expected_score:.2f}")
    print(f"  Simulations: {result.num_simulations:,}")
    print(f"  Time: {result.time_taken:.2f}s")
    print(f"  Simulations/second: {result.num_simulations / result.time_taken:,.0f}")


def main():
    """Run all examples."""
    print("OFC Solver Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_solve_initial_hand()
    example_solve_difficult_position()
    example_complete_game()
    example_custom_analysis()
    
    print("\n\nAll examples completed!")
    print("\nYou can modify these examples to analyze your own positions.")
    print("Just change the cards and placements in the code above.")


if __name__ == "__main__":
    main()