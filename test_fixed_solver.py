#!/usr/bin/env python3
"""Test the fixed OFC solver."""

import sys
import os
from ofc_solver_fixed import Card, PlayerArrangement, OFCMCTSSolver

def test_player_arrangement_attributes():
    """Test that PlayerArrangement has correct attributes."""
    print("Testing PlayerArrangement attributes...")
    
    arrangement = PlayerArrangement()
    
    # Test attribute existence
    assert hasattr(arrangement, 'front_hand'), "Missing front_hand attribute"
    assert hasattr(arrangement, 'middle_hand'), "Missing middle_hand attribute"
    assert hasattr(arrangement, 'back_hand'), "Missing back_hand attribute"
    
    # Test that old attributes don't exist
    assert not hasattr(arrangement, 'front'), "Should not have 'front' attribute"
    assert not hasattr(arrangement, 'middle'), "Should not have 'middle' attribute"
    assert not hasattr(arrangement, 'back'), "Should not have 'back' attribute"
    
    print("✓ All attributes are correct")


def test_basic_functionality():
    """Test basic card placement functionality."""
    print("\nTesting basic functionality...")
    
    arrangement = PlayerArrangement()
    
    # Test adding cards
    card1 = Card.from_string("As")
    card2 = Card.from_string("Kd")
    card3 = Card.from_string("Qh")
    
    assert arrangement.add_card_to_hand(card1, 'front'), "Failed to add card to front"
    assert arrangement.add_card_to_hand(card2, 'middle'), "Failed to add card to middle"
    assert arrangement.add_card_to_hand(card3, 'back'), "Failed to add card to back"
    
    print("✓ Card placement works correctly")


def test_mcts_solver():
    """Test MCTS solver with sample cards."""
    print("\nTesting MCTS solver...")
    
    # Create test cards
    test_cards = [
        Card.from_string("As"),
        Card.from_string("Ks"),
        Card.from_string("Qs"),
        Card.from_string("Js"),
        Card.from_string("Ts")  # Royal flush cards
    ]
    
    solver = OFCMCTSSolver(num_simulations=500)  # More simulations for better exploration
    
    try:
        arrangement = solver.solve_initial_five(test_cards)
        print("✓ MCTS solver completed successfully")
        
        # Check that all 5 cards were placed
        total_cards = (len(arrangement.front_hand.cards) + 
                      len(arrangement.middle_hand.cards) + 
                      len(arrangement.back_hand.cards))
        
        assert total_cards == 5, f"Expected 5 cards placed, got {total_cards}"
        print("✓ All 5 cards were placed")
        
        # Check validity
        assert arrangement.is_valid(), "Arrangement is invalid"
        print("✓ Arrangement is valid")
        
        return True
        
    except Exception as e:
        print(f"✗ MCTS solver failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_various_hands():
    """Test solver with various hand types."""
    print("\nTesting various hand combinations...")
    
    test_cases = [
        # Pair of aces
        ["As", "Ah", "Kd", "Qc", "Js"],
        # Two pair
        ["As", "Ah", "Kd", "Kc", "Qs"],
        # Three of a kind
        ["As", "Ah", "Ad", "Kc", "Qs"],
        # Mixed high cards
        ["As", "Kd", "Qh", "Jc", "Ts"],
        # Low cards
        ["2s", "3h", "4d", "5c", "7s"]
    ]
    
    solver = OFCMCTSSolver(num_simulations=200)  # More simulations for various hands
    
    for i, card_strings in enumerate(test_cases):
        cards = [Card.from_string(cs) for cs in card_strings]
        print(f"\nTest {i+1}: {' '.join(card_strings)}")
        
        try:
            arrangement = solver.solve_initial_five(cards)
            if arrangement.is_valid():
                print("✓ Valid arrangement found")
            else:
                print("✗ Invalid arrangement")
        except Exception as e:
            print(f"✗ Error: {e}")


def main():
    """Run all tests."""
    print("=== Testing Fixed OFC Solver ===\n")
    
    # Run tests
    test_player_arrangement_attributes()
    test_basic_functionality()
    
    if test_mcts_solver():
        test_various_hands()
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")


if __name__ == "__main__":
    main()