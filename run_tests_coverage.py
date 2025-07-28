#!/usr/bin/env python3
"""
Test runner with coverage reporting for OFC Solver.

This script runs all tests and generates a comprehensive coverage report.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(message):
    """Print a formatted header."""
    print(f"\n{BLUE}{BOLD}{'=' * 60}{RESET}")
    print(f"{BLUE}{BOLD}{message:^60}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 60}{RESET}\n")


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message):
    """Print warning message."""
    print(f"{YELLOW}⚠ {message}{RESET}")


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{BOLD}Running: {description}{RESET}")
    print(f"Command: {' '.join(command)}")
    
    start_time = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    print(f"Time: {elapsed:.2f}s")
    
    if result.returncode == 0:
        print_success(f"{description} completed successfully")
    else:
        print_error(f"{description} failed with exit code {result.returncode}")
        if result.stderr:
            print(f"\nError output:\n{result.stderr}")
    
    return result


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    dependencies = ['pytest', 'pytest-cov', 'coverage']
    missing = []
    
    for dep in dependencies:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', dep], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"{dep} is installed")
        else:
            print_error(f"{dep} is not installed")
            missing.append(dep)
    
    if missing:
        print_warning(f"\nInstalling missing dependencies: {', '.join(missing)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
        print_success("Dependencies installed")
    
    return True


def run_tests_with_coverage():
    """Run tests with coverage measurement."""
    print_header("Running Tests with Coverage")
    
    # Test command with coverage
    test_command = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html',
        '--cov-report=xml',
        '--cov-branch',
        '--no-cov-on-fail'
    ]
    
    result = run_command(test_command, "Test Suite with Coverage")
    
    return result.returncode == 0


def generate_coverage_report():
    """Generate detailed coverage report."""
    print_header("Generating Coverage Report")
    
    # Generate coverage report
    coverage_command = [
        sys.executable, '-m', 'coverage', 'report',
        '--show-missing',
        '--skip-covered',
        '--sort=cover'
    ]
    
    result = run_command(coverage_command, "Coverage Report")
    
    if result.returncode == 0:
        print(f"\n{result.stdout}")
    
    return result.returncode == 0


def check_coverage_threshold():
    """Check if coverage meets the threshold."""
    print_header("Checking Coverage Threshold")
    
    # Get coverage percentage
    result = subprocess.run(
        [sys.executable, '-m', 'coverage', 'report'],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        total_line = lines[-1]  # Last line contains total
        
        # Extract percentage
        import re
        match = re.search(r'(\d+)%', total_line)
        if match:
            coverage_percentage = int(match.group(1))
            print(f"\nTotal Coverage: {coverage_percentage}%")
            
            if coverage_percentage >= 80:
                print_success(f"Coverage target met: {coverage_percentage}% >= 80%")
                return True
            else:
                print_error(f"Coverage below target: {coverage_percentage}% < 80%")
                return False
    
    print_error("Could not determine coverage percentage")
    return False


def analyze_uncovered_modules():
    """Analyze which modules need more tests."""
    print_header("Analyzing Uncovered Code")
    
    # Get detailed coverage data
    result = subprocess.run(
        [sys.executable, '-m', 'coverage', 'report', '--show-missing'],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        
        # Find modules with low coverage
        low_coverage_modules = []
        for line in lines[2:-1]:  # Skip header and total
            parts = line.split()
            if len(parts) >= 4:
                try:
                    coverage = int(parts[3].rstrip('%'))
                    if coverage < 80:
                        module = parts[0]
                        missing = ' '.join(parts[4:]) if len(parts) > 4 else "N/A"
                        low_coverage_modules.append((module, coverage, missing))
                except (ValueError, IndexError):
                    continue
        
        if low_coverage_modules:
            print("\nModules needing more tests:")
            for module, coverage, missing in sorted(low_coverage_modules, key=lambda x: x[1]):
                print(f"  {module}: {coverage}%")
                if missing != "N/A" and len(missing) < 100:
                    print(f"    Missing: {missing}")
        else:
            print_success("All modules have adequate coverage")


def create_test_summary():
    """Create a summary of test results."""
    print_header("Test Summary")
    
    # Count test files and test functions
    test_files = list(Path('tests').glob('test_*.py'))
    test_count = 0
    
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
            test_count += content.count('def test_')
    
    print(f"Test Files: {len(test_files)}")
    print(f"Test Functions: {test_count}")
    
    # List test files
    print("\nTest Files:")
    for test_file in sorted(test_files):
        print(f"  - {test_file.name}")
    
    # Check for HTML report
    if Path('htmlcov/index.html').exists():
        print_success("\nHTML coverage report generated: htmlcov/index.html")
        print("  Open with: python -m http.server --directory htmlcov 8000")


def main():
    """Main execution function."""
    print_header("OFC Solver Test Coverage Report")
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Run tests with coverage
    if not run_tests_with_coverage():
        print_error("Tests failed")
        return 1
    
    # Generate coverage report
    if not generate_coverage_report():
        print_error("Failed to generate coverage report")
        return 1
    
    # Check coverage threshold
    coverage_met = check_coverage_threshold()
    
    # Analyze uncovered modules
    analyze_uncovered_modules()
    
    # Create summary
    create_test_summary()
    
    # Final result
    print_header("Final Result")
    if coverage_met:
        print_success("All tests passed and coverage target met!")
        return 0
    else:
        print_error("Coverage target not met. Please add more tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())