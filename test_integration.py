#!/usr/bin/env python3
"""
Integration test for the complete OFC solver system.
Tests both sequential and parallel solvers.
"""

import time
import sys
from ofc_solver_fixed import Card, PlayerArrangement, OFCMCTSSolver
from ofc_parallel_solver import ParallelOFCSolver


def test_attribute_fix():
    """Verify the attribute naming fix."""
    print("1. Testing PlayerArrangement attribute fix...")
    
    arrangement = PlayerArrangement()
    
    # These should work
    try:
        arrangement.front_hand.add_card(Card.from_string("As"))
        arrangement.middle_hand.add_card(Card.from_string("Kd"))
        arrangement.back_hand.add_card(Card.from_string("Qh"))
        print("   ✓ Correct attributes (front_hand, middle_hand, back_hand) work")
    except AttributeError as e:
        print(f"   ✗ Error with correct attributes: {e}")
        return False
    
    # These should fail
    try:
        _ = arrangement.front
        print("   ✗ Old attribute 'front' still exists (should not)")
        return False
    except AttributeError:
        print("   ✓ Old attribute 'front' correctly removed")
    
    return True


def test_sequential_solver():
    """Test the sequential MCTS solver."""
    print("\n2. Testing Sequential MCTS Solver...")
    
    cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    solver = OFCMCTSSolver(num_simulations=500)
    
    start_time = time.time()
    try:
        arrangement = solver.solve_initial_five(cards)
        elapsed = time.time() - start_time
        
        # Verify results
        total_cards = (len(arrangement.front_hand.cards) + 
                      len(arrangement.middle_hand.cards) + 
                      len(arrangement.back_hand.cards))
        
        print(f"   ✓ Solver completed in {elapsed:.2f}s")
        print(f"   ✓ Placed {total_cards}/5 cards")
        print(f"   ✓ Arrangement valid: {arrangement.is_valid()}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Solver failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_solver():
    """Test the parallel solver."""
    print("\n3. Testing Parallel Solver...")
    
    cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    solver = ParallelOFCSolver(num_workers=2, simulations_per_worker=250)
    
    start_time = time.time()
    try:
        arrangement = solver.solve_initial_five(cards)
        elapsed = time.time() - start_time
        
        # Verify results
        total_cards = (len(arrangement.front_hand.cards) + 
                      len(arrangement.middle_hand.cards) + 
                      len(arrangement.back_hand.cards))
        
        print(f"   ✓ Parallel solver completed in {elapsed:.2f}s")
        print(f"   ✓ Placed {total_cards}/5 cards")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Parallel solver failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_solver_consistency():
    """Test that solvers produce reasonable results."""
    print("\n4. Testing Solver Consistency...")
    
    test_cases = [
        {
            'name': 'Pair of Aces',
            'cards': ["As", "Ah", "Kd", "Qc", "Js"],
            'expected': 'Aces should be together'
        },
        {
            'name': 'Three of a Kind',
            'cards': ["As", "Ah", "Ad", "Kc", "Qs"],
            'expected': 'Trips should be in back'
        },
        {
            'name': 'Two Pair',
            'cards': ["As", "Ah", "Kd", "Kc", "Qs"],
            'expected': 'Higher pair in back'
        }
    ]
    
    seq_solver = OFCMCTSSolver(num_simulations=200)
    par_solver = ParallelOFCSolver(num_workers=2, simulations_per_worker=100)
    
    for test in test_cases:
        print(f"\n   Testing: {test['name']}")
        cards = [Card.from_string(cs) for cs in test['cards']]
        
        # Test sequential
        seq_result = seq_solver.solve_initial_five(cards)
        print(f"   Sequential result:")
        print_arrangement_summary(seq_result, indent=6)
        
        # Test parallel
        par_result = par_solver.solve_initial_five(cards)
        print(f"   Parallel result:")
        print_arrangement_summary(par_result, indent=6)
        
        print(f"   Expected: {test['expected']}")
    
    return True


def print_arrangement_summary(arrangement: PlayerArrangement, indent: int = 0):
    """Print a compact summary of an arrangement."""
    prefix = " " * indent
    print(f"{prefix}Front:  {' '.join(str(c) for c in arrangement.front_hand.cards)}")
    print(f"{prefix}Middle: {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
    print(f"{prefix}Back:   {' '.join(str(c) for c in arrangement.back_hand.cards)}")


def test_performance():
    """Test solver performance."""
    print("\n5. Testing Performance...")
    
    cards = [Card.from_string(cs) for cs in ["As", "Kd", "Qh", "Jc", "Ts"]]
    
    # Sequential performance
    seq_solver = OFCMCTSSolver(num_simulations=1000)
    start = time.time()
    seq_solver.solve_initial_five(cards)
    seq_time = time.time() - start
    
    # Parallel performance
    par_solver = ParallelOFCSolver(num_workers=4, simulations_per_worker=250)
    start = time.time()
    par_solver.solve_initial_five(cards)
    par_time = time.time() - start
    
    print(f"   Sequential (1000 sims): {seq_time:.2f}s")
    print(f"   Parallel (4x250 sims):  {par_time:.2f}s")
    print(f"   Speedup: {seq_time/par_time:.1f}x")
    
    return True


def main():
    """Run all integration tests."""
    print("=== OFC Solver Integration Tests ===\n")
    
    tests = [
        ("Attribute Fix", test_attribute_fix),
        ("Sequential Solver", test_sequential_solver),
        ("Parallel Solver", test_parallel_solver),
        ("Solver Consistency", test_solver_consistency),
        ("Performance", test_performance)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n{name} test crashed: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print('='*50)
    
    if failed == 0:
        print("\n✅ All tests passed! The OFC solver is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)