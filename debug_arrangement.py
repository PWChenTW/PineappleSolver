#!/usr/bin/env python3
"""Debug script to find PlayerArrangement attribute issue."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import and inspect PlayerArrangement
try:
    # Try different possible import paths
    try:
        from ofcpoker import PlayerArrangement
        print("✓ Imported PlayerArrangement from ofcpoker")
    except ImportError:
        try:
            from game_logic import PlayerArrangement
            print("✓ Imported PlayerArrangement from game_logic")
        except ImportError:
            try:
                from src.game.models import PlayerArrangement
                print("✓ Imported PlayerArrangement from src.game.models")
            except ImportError:
                try:
                    from src.core.arrangement import PlayerArrangement
                    print("✓ Imported PlayerArrangement from src.core.arrangement")
                except ImportError:
                    print("✗ Could not find PlayerArrangement in any expected location")
                    sys.exit(1)
    
    # Create an instance and inspect its attributes
    print("\nPlayerArrangement attributes:")
    arrangement = PlayerArrangement()
    
    # List all attributes
    for attr in dir(arrangement):
        if not attr.startswith('_'):
            print(f"  - {attr}: {type(getattr(arrangement, attr, None))}")
    
    # Check specific attributes
    print("\nChecking specific attributes:")
    attrs_to_check = ['front', 'front_hand', 'middle', 'middle_hand', 'back', 'back_hand']
    for attr in attrs_to_check:
        if hasattr(arrangement, attr):
            print(f"  ✓ {attr} exists")
        else:
            print(f"  ✗ {attr} does NOT exist")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()