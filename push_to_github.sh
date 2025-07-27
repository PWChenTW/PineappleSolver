#!/bin/bash
# Script to push PineappleSolver to GitHub

echo "=== Pushing PineappleSolver to GitHub ==="

# Add remote origin (replace with your actual repository URL)
echo "Adding remote origin..."
git remote add origin git@github.com:PWChenTW/PineappleSolver.git

# Verify remote
echo "Remote URLs:"
git remote -v

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Your repository should now be on GitHub."
echo "Visit: https://github.com/PWChenTW/PineappleSolver"