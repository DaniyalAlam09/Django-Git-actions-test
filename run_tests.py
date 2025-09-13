#!/usr/bin/env python
"""
Test runner script for the Django e-commerce application.

This script provides a convenient way to run different types of tests:
- Unit tests
- Integration tests
- E2E tests
- All tests
- Specific test modules

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run unit tests only
    python run_tests.py --integration     # Run integration tests only
    python run_tests.py --e2e             # Run E2E tests only
    python run_tests.py --coverage        # Run tests with coverage
    python run_tests.py --verbose         # Run tests with verbose output
    python run_tests.py --parallel       # Run tests in parallel
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()


def run_command(command, verbose=False):
    """Run a command and return the result."""
    if verbose:
        print(f"Running: {' '.join(command)}")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def run_unit_tests(verbose=False, parallel=False, coverage=False):
    """Run unit tests."""
    command = ['python', '-m', 'pytest', 'tests/unit/']
    
    if verbose:
        command.append('-v')
    
    if parallel:
        command.extend(['-n', 'auto'])
    
    if coverage:
        command.extend(['--cov=store', '--cov=ecommerce', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(command, verbose)


def run_integration_tests(verbose=False, parallel=False, coverage=False):
    """Run integration tests."""
    command = ['python', '-m', 'pytest', 'tests/integration/']
    
    if verbose:
        command.append('-v')
    
    if parallel:
        command.extend(['-n', 'auto'])
    
    if coverage:
        command.extend(['--cov=store', '--cov=ecommerce', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(command, verbose)


def run_e2e_tests(verbose=False, parallel=False, coverage=False):
    """Run E2E tests."""
    command = ['python', '-m', 'pytest', 'tests/e2e/', '-m', 'e2e']
    
    if verbose:
        command.append('-v')
    
    if parallel:
        command.extend(['-n', 'auto'])
    
    if coverage:
        command.extend(['--cov=store', '--cov=ecommerce', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(command, verbose)


def run_all_tests(verbose=False, parallel=False, coverage=False):
    """Run all tests."""
    command = ['python', '-m', 'pytest', 'tests/']
    
    if verbose:
        command.append('-v')
    
    if parallel:
        command.extend(['-n', 'auto'])
    
    if coverage:
        command.extend(['--cov=store', '--cov=ecommerce', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(command, verbose)


def run_specific_tests(test_path, verbose=False, parallel=False, coverage=False):
    """Run specific tests."""
    command = ['python', '-m', 'pytest', test_path]
    
    if verbose:
        command.append('-v')
    
    if parallel:
        command.extend(['-n', 'auto'])
    
    if coverage:
        command.extend(['--cov=store', '--cov=ecommerce', '--cov-report=html', '--cov-report=term-missing'])
    
    return run_command(command, verbose)


def run_linting():
    """Run code linting."""
    commands = [
        ['python', '-m', 'black', '--check', '.'],
        ['python', '-m', 'isort', '--check-only', '.'],
        ['python', '-m', 'flake8', 'store/', 'ecommerce/'],
    ]
    
    for command in commands:
        result = run_command(command)
        if result != 0:
            return result
    
    return 0


def run_type_checking():
    """Run type checking."""
    command = ['python', '-m', 'mypy', 'store/', 'ecommerce/']
    return run_command(command)


def run_security_check():
    """Run security check."""
    command = ['python', '-m', 'bandit', '-r', 'store/', 'ecommerce/']
    return run_command(command)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run tests for the Django e-commerce application')
    
    # Test type options
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    # Test options
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--verbose', '-v', action='store_true', help='Run tests with verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    
    # Quality checks
    parser.add_argument('--lint', action='store_true', help='Run code linting')
    parser.add_argument('--type-check', action='store_true', help='Run type checking')
    parser.add_argument('--security', action='store_true', help='Run security check')
    parser.add_argument('--quality', action='store_true', help='Run all quality checks')
    
    # Specific test options
    parser.add_argument('--test', help='Run specific test file or module')
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all tests
    if not any([args.unit, args.integration, args.e2e, args.all, args.test, args.lint, args.type_check, args.security, args.quality]):
        args.all = True
    
    exit_code = 0
    
    # Run quality checks
    if args.quality or args.lint:
        print("Running code linting...")
        exit_code = run_linting()
        if exit_code != 0:
            return exit_code
    
    if args.quality or args.type_check:
        print("Running type checking...")
        exit_code = run_type_checking()
        if exit_code != 0:
            return exit_code
    
    if args.quality or args.security:
        print("Running security check...")
        exit_code = run_security_check()
        if exit_code != 0:
            return exit_code
    
    # Run tests
    if args.unit:
        print("Running unit tests...")
        exit_code = run_unit_tests(args.verbose, args.parallel, args.coverage)
    elif args.integration:
        print("Running integration tests...")
        exit_code = run_integration_tests(args.verbose, args.parallel, args.coverage)
    elif args.e2e:
        print("Running E2E tests...")
        exit_code = run_e2e_tests(args.verbose, args.parallel, args.coverage)
    elif args.test:
        print(f"Running specific tests: {args.test}")
        exit_code = run_specific_tests(args.test, args.verbose, args.parallel, args.coverage)
    elif args.all:
        print("Running all tests...")
        exit_code = run_all_tests(args.verbose, args.parallel, args.coverage)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
