#!/usr/bin/env python3
"""Run error handling tests for OFC Solver."""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_error_handling.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)