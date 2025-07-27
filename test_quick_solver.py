#!/usr/bin/env python3
"""
Quick test for OFC Solver parallel execution bug fix.
"""

import sys
sys.path.append('.')

from src.core.domain import GameState
from src.ofc_solver import create_solver


def test_parallel_search():
    """Test parallel MCTS search."""
    print("=== Testing Parallel Search Fix ===\n")
    
    # Create game state
    game = GameState(num_players=2, player_index=0, seed=456)
    
    # Create solver with parallel threads but short time limit
    solver = create_solver(time_limit=2.0, num_threads=2)
    
    print("Testing multi-threaded MCTS...")
    
    try:
        # Solve complete game with very short time limits
        results = solver.solve_game(game)
        
        print(f"Success! Completed {len(results)} decisions")
        print("Parallel search is working correctly.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_single_thread():
    """Test single thread for comparison."""
    print("\n=== Testing Single Thread ===\n")
    
    game = GameState(num_players=2, player_index=0, seed=456)
    solver = create_solver(time_limit=2.0, num_threads=1)
    
    print("Testing single-threaded MCTS...")
    
    try:
        # Just test initial placement
        game.deal_street()
        result = solver.solve(game)
        
        print(f"Success! Found action in {result.time_taken:.2f}s")
        print(f"Simulations: {result.num_simulations}")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True


def main():
    """Run tests."""
    print("Quick OFC Solver Test\n")
    
    # Test single thread first
    if test_single_thread():
        print("✓ Single thread test passed")
    else:
        print("✗ Single thread test failed")
        return
    
    # Test parallel
    if test_parallel_search():
        print("\n✓ Parallel search test passed")
    else:
        print("\n✗ Parallel search test failed")


if __name__ == "__main__":
    main()