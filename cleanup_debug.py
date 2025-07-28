#!/usr/bin/env python3
"""Clean up debug files."""

import os
import glob

# Files to remove
debug_files = [
    'debug_arrangement.py',
    'cleanup_debug.py'  # Remove self after running
]

for file in debug_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"Removed: {file}")

print("Cleanup complete.")