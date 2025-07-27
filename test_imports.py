#!/usr/bin/env python3
"""
Test script to verify imports are working correctly after the fix.
"""

import sys
sys.path.append('.')

def test_domain_imports():
    """Test that all domain imports work correctly."""
    try:
        # Test the fixed import
        from src.core.domain import GameState, Card, Street
        print("✓ Successfully imported GameState, Card, Street from src.core.domain")
        
        # Verify Street enum values
        print(f"✓ Street.INITIAL = {Street.INITIAL}")
        print(f"✓ Street.SECOND = {Street.SECOND}")
        print(f"✓ Street.THIRD = {Street.THIRD}")
        print(f"✓ Street.FOURTH = {Street.FOURTH}")
        print(f"✓ Street.COMPLETE = {Street.COMPLETE}")
        
        # Test GameState creation
        game = GameState(num_players=2, player_index=0)
        print(f"✓ Successfully created GameState")
        
        # Test Card creation
        card = Card.from_string("As")
        print(f"✓ Successfully created Card: {card}")
        
        # Test Street usage in GameState
        game._current_street = Street.INITIAL
        print(f"✓ Successfully set game street to: {game._current_street}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {type(e).__name__}: {e}")
        return False


def test_solver_imports():
    """Test that solver imports work correctly."""
    try:
        from src.ofc_solver import create_solver
        print("\n✓ Successfully imported create_solver from src.ofc_solver")
        
        # Test solver creation
        solver = create_solver(time_limit=1.0, num_threads=1)
        print("✓ Successfully created solver instance")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Solver import error: {type(e).__name__}: {e}")
        return False


def test_example_usage_imports():
    """Test that example_usage.py imports work correctly."""
    try:
        # Import the functions from example_usage
        from example_usage import (
            example_solve_initial_hand,
            example_solve_difficult_position,
            example_complete_game,
            example_custom_analysis
        )
        print("\n✓ Successfully imported all example functions from example_usage.py")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Example usage import error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all import tests."""
    print("=" * 60)
    print("Testing PineappleSolver imports after Street enum fix")
    print("=" * 60)
    
    results = []
    
    # Test domain imports
    print("\n1. Testing domain imports...")
    results.append(test_domain_imports())
    
    # Test solver imports
    print("\n2. Testing solver imports...")
    results.append(test_solver_imports())
    
    # Test example usage imports
    print("\n3. Testing example_usage imports...")
    results.append(test_example_usage_imports())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n✅ All tests passed! The Street enum import fix is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed_tests} test(s) failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)