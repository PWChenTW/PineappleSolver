#!/usr/bin/env python3
"""
Test script for initial 5-card placement solver.

This script tests the MCTS integration for solving initial placements.
"""

import time
import logging
from typing import List

from src.application import OFCSolverService, SolveRequestDTO


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_initial_placement(cards: List[str], time_limit: float = 5.0):
    """Test solving initial placement for given cards."""
    logger.info("=" * 60)
    logger.info(f"Testing initial placement for cards: {cards}")
    logger.info(f"Time limit: {time_limit}s")
    
    # Create solver service
    solver_service = OFCSolverService()
    
    # Create request
    request = SolveRequestDTO(
        cards=cards,
        time_limit=time_limit,
        num_threads=4
    )
    
    try:
        # Solve
        start_time = time.time()
        result = solver_service.solve_initial_placement(request)
        
        # Display results
        logger.info("\nResults:")
        logger.info(f"Computation time: {result.computation_time:.2f}s")
        logger.info(f"Simulations: {result.statistics['total_simulations']}")
        logger.info(f"Nodes evaluated: {result.statistics['nodes_evaluated']}")
        logger.info(f"Evaluation score: {result.evaluation:.3f}")
        logger.info(f"Confidence: {result.confidence:.3f}")
        logger.info(f"Visit count: {result.visit_count}")
        
        logger.info("\nOptimal placement:")
        # Group placements by position
        front_cards = []
        middle_cards = []
        back_cards = []
        
        for placement in result.placements:
            card_str = f"{placement.card}[{placement.index}]"
            if placement.position == 'front':
                front_cards.append((placement.index, placement.card))
            elif placement.position == 'middle':
                middle_cards.append((placement.index, placement.card))
            elif placement.position == 'back':
                back_cards.append((placement.index, placement.card))
        
        # Sort by index and display
        front_cards.sort()
        middle_cards.sort()
        back_cards.sort()
        
        logger.info(f"  Front:  {' '.join([c[1] for c in front_cards])}")
        logger.info(f"  Middle: {' '.join([c[1] for c in middle_cards])}")
        logger.info(f"  Back:   {' '.join([c[1] for c in back_cards])}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error solving placement: {e}", exc_info=True)
        return None


def main():
    """Run test cases."""
    # Test cases
    test_cases = [
        # Test 1: High cards
        {
            'cards': ['As', 'Ah', 'Kh', 'Qc', 'Jd'],
            'time_limit': 5.0,
            'description': 'High cards with pair of aces'
        },
        
        # Test 2: Mixed hand
        {
            'cards': ['Ac', 'Kd', '8h', '5s', '2c'],
            'time_limit': 10.0,
            'description': 'Mixed high and low cards'
        },
        
        # Test 3: Flush draw potential
        {
            'cards': ['Ah', 'Kh', 'Qh', '7c', '2d'],
            'time_limit': 10.0,
            'description': 'Three hearts - flush draw potential'
        },
        
        # Test 4: Two pairs
        {
            'cards': ['Ks', 'Kh', '8d', '8c', '3h'],
            'time_limit': 15.0,
            'description': 'Two pairs - Kings and Eights'
        },
        
        # Test 5: Straight potential
        {
            'cards': ['9h', '8c', '7d', '6s', '4h'],
            'time_limit': 20.0,
            'description': 'Straight draw potential'
        }
    ]
    
    # Run tests
    logger.info("Starting OFC Initial Placement Tests")
    logger.info("=" * 60)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test_case['description']}")
        result = test_initial_placement(
            test_case['cards'],
            test_case['time_limit']
        )
        results.append(result)
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    successful = sum(1 for r in results if r is not None)
    logger.info(f"Successful: {successful}/{len(test_cases)}")
    
    if successful == len(test_cases):
        logger.info("All tests passed!")
    else:
        logger.warning("Some tests failed!")


if __name__ == '__main__':
    main()