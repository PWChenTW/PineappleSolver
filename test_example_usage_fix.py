#!/usr/bin/env python3
"""
Test to verify example_usage.py works correctly after the Street enum import fix.
This test simulates a minimal version of the examples to ensure no AttributeError occurs.
"""

import sys
sys.path.append('.')

from src.core.domain import GameState, Card, Street
from src.ofc_solver import create_solver


def test_minimal_example():
    """Test a minimal version of the example to ensure imports work."""
    print("Testing minimal example after fix...")
    
    try:
        # Test 1: Create game state and use Street enum
        game = GameState(num_players=2, player_index=0, seed=42)
        print(f"✓ Created GameState, current street: {game.current_street}")
        
        # Test 2: Set street using the enum
        game._current_street = Street.SECOND
        print(f"✓ Changed street to: {game.current_street}")
        
        # Test 3: Create cards
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        game._current_hand = cards
        print(f"✓ Set current hand: {[str(c) for c in cards]}")
        
        # Test 4: Use Street in comparison
        if game.current_street == Street.SECOND:
            print("✓ Street comparison works correctly")
        
        # Test 5: Check Street values in different contexts
        streets = [Street.INITIAL, Street.SECOND, Street.THIRD, Street.FOURTH, Street.COMPLETE]
        for street in streets:
            game._current_street = street
            assert game.current_street == street
        print("✓ All Street enum values work correctly")
        
        return True
        
    except AttributeError as e:
        print(f"✗ AttributeError (the original bug): {e}")
        return False
    except Exception as e:
        print(f"✗ Other error: {type(e).__name__}: {e}")
        return False


def test_example_functions_import():
    """Test that we can import and call example functions without errors."""
    print("\nTesting example function imports...")
    
    try:
        # Import should not raise AttributeError anymore
        import example_usage
        
        # Check that functions exist
        assert hasattr(example_usage, 'example_solve_initial_hand')
        assert hasattr(example_usage, 'example_solve_difficult_position')
        assert hasattr(example_usage, 'example_complete_game')
        assert hasattr(example_usage, 'example_custom_analysis')
        
        print("✓ All example functions imported successfully")
        return True
        
    except AttributeError as e:
        print(f"✗ AttributeError during import: {e}")
        return False
    except Exception as e:
        print(f"✗ Import error: {type(e).__name__}: {e}")
        return False


def test_street_usage_patterns():
    """Test common Street enum usage patterns from example_usage.py."""
    print("\nTesting Street enum usage patterns...")
    
    try:
        game = GameState(num_players=2, player_index=0)
        
        # Pattern 1: Direct assignment (line 74 in example_usage.py)
        game._current_street = Street.SECOND
        assert game._current_street == Street.SECOND
        print("✓ Direct Street assignment works")
        
        # Pattern 2: Using Street.INITIAL (line 168 in example_usage.py)
        game._current_street = Street.INITIAL
        assert game._current_street == Street.INITIAL
        print("✓ Street.INITIAL assignment works")
        
        # Pattern 3: Street in game logic
        if game.current_street == Street.INITIAL:
            print("✓ Street comparison in conditionals works")
        
        return True
        
    except AttributeError as e:
        print(f"✗ AttributeError with Street enum: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing example_usage.py fix for AttributeError")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(test_minimal_example())
    results.append(test_example_functions_import())
    results.append(test_street_usage_patterns())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\nThe fix for the AttributeError in example_usage.py is working correctly!")
        print("The Street enum can now be imported from src.core.domain without issues.")
        return 0
    else:
        print(f"❌ TESTS FAILED ({total - passed}/{total} failed)")
        print("\nPlease check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())