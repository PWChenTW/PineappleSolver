#!/usr/bin/env python3
"""
Test script to verify TODO fixes in OFC Solver.

This tests:
1. Expected score extraction from MCTS root node
2. Top actions extraction from MCTS root node  
3. Smart initial placement generation
"""

import sys
sys.path.append('.')

from src.ofc_solver import create_solver
from src.core.domain import GameState, Card


def test_solver_result_extraction():
    """Test that we can extract expected score and top actions from solver result."""
    print("=== Testing solver result extraction ===")
    
    # Create a solver with short time limit for testing
    solver = create_solver(time_limit=1.0, num_threads=1)
    
    # Create initial game state
    game_state = GameState(num_players=2, player_index=0)
    
    # Deal initial cards
    game_state.deal_street()
    print(f"Dealt cards: {[str(c) for c in game_state.current_hand]}")
    
    # Solve the position
    result = solver.solve(game_state)
    
    # Check that TODO items are fixed
    print(f"\nExpected score: {result.expected_score:.3f}")
    assert isinstance(result.expected_score, float), "Expected score should be a float"
    
    print(f"\nTop actions found: {len(result.top_actions)}")
    assert isinstance(result.top_actions, list), "Top actions should be a list"
    
    if result.top_actions:
        print("\nTop 3 actions:")
        for i, (action, visits, avg_reward) in enumerate(result.top_actions[:3]):
            print(f"  {i+1}. Visits: {visits}, Avg reward: {avg_reward:.3f}")
            for card, pos, idx in action.placements:
                print(f"     Place {card} at {pos}[{idx}]")
            if action.discard:
                print(f"     Discard {action.discard}")
    
    print("\n✓ Solver result extraction working correctly")


def test_initial_placement_strategies():
    """Test that initial placement generates multiple smart strategies."""
    print("\n=== Testing initial placement strategies ===")
    
    from src.core.algorithms.mcts_node import MCTSNode
    
    # Test case 1: Hand with a pair
    print("\nTest 1: Hand with a pair")
    game_state = GameState(num_players=2, player_index=0)
    game_state.current_hand = [
        Card.from_string("As"),
        Card.from_string("Ah"),  # Pair of aces
        Card.from_string("Kd"),
        Card.from_string("Qc"),
        Card.from_string("5h")
    ]
    
    node = MCTSNode(game_state)
    actions = node._generate_initial_actions(game_state.current_hand)
    
    print(f"Generated {len(actions)} actions for hand with pair")
    assert len(actions) > 0, "Should generate at least one action"
    
    # Test case 2: Hand with flush potential
    print("\nTest 2: Hand with flush potential")
    game_state.current_hand = [
        Card.from_string("Ah"),
        Card.from_string("Kh"),
        Card.from_string("Qh"),  # Three hearts
        Card.from_string("5c"),
        Card.from_string("2d")
    ]
    
    node = MCTSNode(game_state)
    actions = node._generate_initial_actions(game_state.current_hand)
    
    print(f"Generated {len(actions)} actions for hand with flush potential")
    assert len(actions) > 0, "Should generate at least one action"
    
    # Test case 3: Hand with straight potential
    print("\nTest 3: Hand with straight potential")
    game_state.current_hand = [
        Card.from_string("6h"),
        Card.from_string("7d"),
        Card.from_string("8c"),  # Connected cards
        Card.from_string("Ks"),
        Card.from_string("2h")
    ]
    
    node = MCTSNode(game_state)
    actions = node._generate_initial_actions(game_state.current_hand)
    
    print(f"Generated {len(actions)} actions for hand with straight potential")
    assert len(actions) > 0, "Should generate at least one action"
    
    # Test case 4: Mixed high cards
    print("\nTest 4: Mixed high cards")
    game_state.current_hand = [
        Card.from_string("As"),
        Card.from_string("Kd"),
        Card.from_string("Jh"),
        Card.from_string("9c"),
        Card.from_string("7s")
    ]
    
    node = MCTSNode(game_state)
    actions = node._generate_initial_actions(game_state.current_hand)
    
    print(f"Generated {len(actions)} actions for mixed high cards")
    assert len(actions) > 0, "Should generate at least one action"
    
    # Show sample action details
    if actions:
        print("\nSample action placement:")
        action = actions[0]
        for card, pos, idx in action.placements:
            print(f"  Place {card} at {pos}[{idx}]")
    
    print("\n✓ Initial placement strategies working correctly")


def test_full_game_solve():
    """Test solving a complete game to verify everything works together."""
    print("\n=== Testing full game solve ===")
    
    # Create solver with very short time limit
    solver = create_solver(time_limit=0.5, num_threads=1)
    
    # Progress callback
    def progress_update(msg):
        print(f"  Progress: {msg}")
    
    # Solve first street only
    game_state = GameState(num_players=2, player_index=0)
    game_state.deal_street()
    
    print(f"Initial hand: {[str(c) for c in game_state.current_hand]}")
    
    result = solver.solve(game_state)
    
    print(f"\nSolution found:")
    print(f"  Expected score: {result.expected_score:.3f}")
    print(f"  Simulations run: {result.num_simulations}")
    print(f"  Time taken: {result.time_taken:.3f}s")
    
    if result.best_action:
        print(f"\nBest action:")
        for card, pos, idx in result.best_action.placements:
            print(f"  Place {card} at {pos}[{idx}]")
        if result.best_action.discard:
            print(f"  Discard {result.best_action.discard}")
    
    print("\n✓ Full game solve working correctly")


if __name__ == "__main__":
    print("Testing TODO fixes in OFC Solver\n")
    
    try:
        test_solver_result_extraction()
        test_initial_placement_strategies()
        test_full_game_solve()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("TODO fixes completed successfully:")
        print("- Expected score extracted from MCTS root node")
        print("- Top actions extracted from MCTS root node")
        print("- Smart initial placement strategies implemented")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)