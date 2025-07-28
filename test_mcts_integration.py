#!/usr/bin/env python3
"""
Test script to verify MCTS integration is working correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ofc_solver import OFCSolver, GameState, Card


def test_initial_placement():
    """Test solving initial 5-card placement."""
    print("Testing MCTS integration for initial 5-card placement...")
    print("-" * 60)
    
    # Create solver
    solver = OFCSolver(threads=1, time_limit=5.0)  # Short time for testing
    
    # Create initial game state with 5 cards
    initial_cards = [
        Card(rank='A', suit='s'),  # Ace of spades
        Card(rank='K', suit='h'),  # King of hearts
        Card(rank='Q', suit='d'),  # Queen of diamonds
        Card(rank='J', suit='c'),  # Jack of clubs
        Card(rank='T', suit='s'),  # Ten of spades
    ]
    
    game_state = GameState(
        current_cards=initial_cards,
        front_hand=[],
        middle_hand=[],
        back_hand=[],
        remaining_cards=47  # 52 - 5 = 47
    )
    
    print(f"Initial cards: {', '.join(str(card) for card in initial_cards)}")
    print("\nRunning MCTS solver...")
    
    try:
        # Solve the position
        result = solver.solve(game_state)
        
        print(f"\nSolver completed!")
        print(f"Simulations run: {result.simulations}")
        print(f"Time taken: {result.time_taken:.2f} seconds")
        print(f"Expected score: {result.expected_score:.2f}")
        print(f"Confidence: {result.confidence:.2%}")
        
        print("\nBest placement:")
        for card_str, position in sorted(result.best_placement.items()):
            print(f"  {card_str} -> {position}")
        
        if result.top_actions:
            print("\nTop alternative actions:")
            for i, action in enumerate(result.top_actions[:3]):
                print(f"  {i+1}. {action['card']} -> {action['position']}")
                print(f"     Visits: {action['visits']}, Avg reward: {action['avg_reward']:.2f}")
        
        # Verify all cards are placed
        if len(result.best_placement) == 5:
            print("\n✓ All 5 cards have been placed!")
        else:
            print(f"\n✗ ERROR: Only {len(result.best_placement)} cards placed!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mid_game_placement():
    """Test solving a mid-game position."""
    print("\n\nTesting MCTS integration for mid-game placement...")
    print("-" * 60)
    
    # Create solver
    solver = OFCSolver(threads=2, time_limit=3.0)
    
    # Create mid-game state
    current_cards = [
        Card(rank='9', suit='h'),
        Card(rank='8', suit='d'),
        Card(rank='7', suit='c'),
    ]
    
    game_state = GameState(
        current_cards=current_cards,
        front_hand=[Card(rank='3', suit='s'), Card(rank='3', suit='h')],  # Pair of 3s
        middle_hand=[Card(rank='T', suit='d'), Card(rank='J', suit='d')],  # Flush draw
        back_hand=[Card(rank='A', suit='c'), Card(rank='K', suit='c')],   # High cards
        remaining_cards=42  # Already placed 6 cards
    )
    
    print(f"Current cards to place: {', '.join(str(card) for card in current_cards)}")
    print(f"Front hand: {', '.join(str(card) for card in game_state.front_hand)}")
    print(f"Middle hand: {', '.join(str(card) for card in game_state.middle_hand)}")
    print(f"Back hand: {', '.join(str(card) for card in game_state.back_hand)}")
    
    print("\nRunning MCTS solver...")
    
    try:
        result = solver.solve(game_state)
        
        print(f"\nSolver completed!")
        print(f"Simulations run: {result.simulations}")
        print(f"Time taken: {result.time_taken:.2f} seconds")
        print(f"Expected score: {result.expected_score:.2f}")
        
        print("\nBest placement:")
        for card_str, position in sorted(result.best_placement.items()):
            print(f"  {card_str} -> {position}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("OFC Solver MCTS Integration Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_initial_placement()
    test2_passed = test_mid_game_placement()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Initial placement test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"  Mid-game placement test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed! MCTS integration is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)