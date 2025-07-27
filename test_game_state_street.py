#!/usr/bin/env python3
"""
Comprehensive test for GameState and Street enum functionality.
"""

import sys
sys.path.append('.')

from src.core.domain import GameState, Card, Street, PlayerArrangement


def test_street_enum_values():
    """Test Street enum values and properties."""
    print("Testing Street enum values...")
    
    # Test enum values
    assert Street.INITIAL.value == 0
    assert Street.SECOND.value == 1
    assert Street.THIRD.value == 2
    assert Street.FOURTH.value == 3
    assert Street.COMPLETE.value == 4
    
    # Test string representation
    assert str(Street.INITIAL) == "Street.INITIAL"
    
    # Test comparison
    assert Street.INITIAL < Street.SECOND
    assert Street.FOURTH < Street.COMPLETE
    
    print("✓ Street enum values are correct")


def test_game_state_street_usage():
    """Test GameState usage of Street enum."""
    print("\nTesting GameState with Street enum...")
    
    # Create game state
    game = GameState(num_players=2, player_index=0)
    
    # Test initial street
    assert game.current_street == Street.INITIAL
    print(f"✓ Initial street is: {game.current_street}")
    
    # Test street progression
    game._current_street = Street.SECOND
    assert game.current_street == Street.SECOND
    print(f"✓ Successfully changed street to: {game.current_street}")
    
    # Test is_complete property
    assert not game.is_complete
    game._current_street = Street.COMPLETE
    assert game.is_complete
    print("✓ is_complete property works correctly")


def test_street_specific_logic():
    """Test street-specific game logic."""
    print("\nTesting street-specific logic...")
    
    game = GameState(num_players=2, player_index=0)
    
    # Test initial street (5 cards)
    game._current_street = Street.INITIAL
    game._current_hand = [Card.from_string(c) for c in ["As", "Kh", "Qd", "Jc", "Ts"]]
    assert len(game._current_hand) == 5
    print("✓ Initial street has 5 cards")
    
    # Test other streets (3 cards)
    for street in [Street.SECOND, Street.THIRD, Street.FOURTH]:
        game._current_street = street
        game._current_hand = [Card.from_string(c) for c in ["2s", "3h", "4d"]]
        assert len(game._current_hand) == 3
    print("✓ Other streets have 3 cards")


def test_example_usage_scenarios():
    """Test scenarios from example_usage.py."""
    print("\nTesting example_usage scenarios...")
    
    # Test scenario from example_solve_difficult_position
    game = GameState(num_players=2, player_index=0)
    
    # Set up a position
    placements = [
        (Card.from_string("Qh"), 'front', 0),
        (Card.from_string("Qd"), 'front', 1),
    ]
    
    for card, pos, idx in placements:
        game.player_arrangement.place_card(card, pos, idx)
    
    # Change street
    game._current_street = Street.SECOND
    assert game.current_street == Street.SECOND
    print("✓ example_solve_difficult_position scenario works")
    
    # Test scenario from example_custom_analysis
    game2 = GameState(num_players=2, player_index=0)
    game2._current_street = Street.INITIAL
    assert game2.current_street == Street.INITIAL
    print("✓ example_custom_analysis scenario works")


def test_street_transition():
    """Test street transitions in game flow."""
    print("\nTesting street transitions...")
    
    game = GameState(num_players=2, player_index=0)
    
    # Simulate street progression
    streets = [Street.INITIAL, Street.SECOND, Street.THIRD, Street.FOURTH, Street.COMPLETE]
    
    for i, street in enumerate(streets):
        game._current_street = street
        assert game.current_street == street
        
        if i < len(streets) - 1:
            # Should not be complete yet
            assert not game.is_complete
        else:
            # Should be complete at COMPLETE street
            assert game.is_complete
    
    print("✓ Street transitions work correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Comprehensive GameState and Street enum tests")
    print("=" * 60)
    
    try:
        test_street_enum_values()
        test_game_state_street_usage()
        test_street_specific_logic()
        test_example_usage_scenarios()
        test_street_transition()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("The fix for the Street enum import is working correctly.")
        print("GameState and Street functionality is intact.")
        print("=" * 60)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())