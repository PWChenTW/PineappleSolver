#!/usr/bin/env python3
"""
Test script for OFC Solver API.

This script tests the API endpoints for initial placement solving.
"""

import requests
import json
import time
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# API configuration
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test_key"  # For development
}


def test_health_check():
    """Test health check endpoint."""
    logger.info("Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/health")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Health check response: {json.dumps(data, indent=2)}")
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


def test_solver_health():
    """Test solver health endpoint."""
    logger.info("Testing solver health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/solver/health")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Solver health response: {json.dumps(data, indent=2)}")
        return True
        
    except Exception as e:
        logger.error(f"Solver health check failed: {e}")
        return False


def test_initial_placement(cards, time_limit=30.0):
    """Test initial placement endpoint."""
    logger.info(f"Testing initial placement for cards: {cards}")
    
    request_data = {
        "cards": cards,
        "time_limit": time_limit,
        "num_threads": 4
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/solver/initial",
            headers=HEADERS,
            json=request_data
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Display results
        logger.info(f"Computation time: {data['computation_time']:.2f}s")
        logger.info(f"Evaluation score: {data['evaluation']:.3f}")
        logger.info(f"Confidence: {data['confidence']:.3f}")
        logger.info(f"Visit count: {data['visit_count']}")
        
        # Display placements
        logger.info("Optimal placement:")
        placements = data['placements']
        
        # Group by position
        positions = {'front': [], 'middle': [], 'back': []}
        for p in placements:
            positions[p['position']].append((p['index'], p['card']))
        
        # Sort and display
        for pos in ['front', 'middle', 'back']:
            cards = sorted(positions[pos])
            logger.info(f"  {pos.capitalize()}: {' '.join([c[1] for c in cards])}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return False


def main():
    """Run API tests."""
    logger.info("Starting OFC Solver API Tests")
    logger.info("=" * 60)
    
    # Check if API is running
    logger.info("Checking API availability...")
    if not test_health_check():
        logger.error("API is not running. Please start the API server first.")
        logger.info("Run: python -m uvicorn src.api.app:app --reload")
        return
    
    # Test solver health
    if not test_solver_health():
        logger.warning("Solver health check failed, but continuing...")
    
    # Test cases
    test_cases = [
        {
            'cards': ['As', 'Kh', 'Qc', 'Jd', 'Ts'],
            'description': 'Royal straight cards'
        },
        {
            'cards': ['Ac', 'Ad', 'Kh', 'Ks', '5c'],
            'description': 'Two pairs - Aces and Kings'
        },
        {
            'cards': ['9h', '8h', '7h', '6c', '5d'],
            'description': 'Straight draw with flush potential'
        }
    ]
    
    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test_case['description']}")
        success = test_initial_placement(test_case['cards'])
        results.append(success)
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    successful = sum(1 for r in results if r)
    logger.info(f"Successful: {successful}/{len(test_cases)}")
    
    if successful == len(test_cases):
        logger.info("All API tests passed!")
    else:
        logger.warning("Some API tests failed!")


if __name__ == '__main__':
    main()