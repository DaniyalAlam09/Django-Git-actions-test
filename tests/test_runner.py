"""
Custom test runner for the Django e-commerce application.

This module provides a custom test runner that:
- Configures test settings
- Sets up test databases
- Handles test data loading
- Manages test cleanup
- Provides test reporting
"""

import os
import sys
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test.utils import get_runner


class ECommerceTestRunner:
    """Custom test runner for the e-commerce application."""

    def __init__(self, verbosity=1, interactive=True, keepdb=False, **kwargs):
        self.verbosity = verbosity
        self.interactive = interactive
        self.keepdb = keepdb
        self.kwargs = kwargs

    def setup_test_environment(self):
        """Set up test environment."""
        # Configure test settings
        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            "MEDIA_ROOT": tempfile.mkdtemp(),
            "STATIC_ROOT": tempfile.mkdtemp(),
            "PASSWORD_HASHERS": [
                "django.contrib.auth.hashers.MD5PasswordHasher",
            ],
            "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
            "CACHES": {
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                }
            },
            "CELERY_TASK_ALWAYS_EAGER": True,
            "CELERY_TASK_EAGER_PROPAGATES": True,
        }

        # Update settings
        for key, value in test_settings.items():
            setattr(settings, key, value)

    def setup_databases(self, **kwargs):
        """Set up test databases."""
        # Create test database
        call_command("migrate", verbosity=self.verbosity, interactive=False)

        # Load test fixtures
        if os.path.exists("tests/fixtures/sample_data.json"):
            call_command(
                "loaddata", "tests/fixtures/sample_data.json", verbosity=self.verbosity
            )

        return None

    def teardown_databases(self, old_config, **kwargs):
        """Tear down test databases."""
        # Clean up test database
        pass

    def run_tests(self, test_labels, **kwargs):
        """Run the test suite."""
        self.setup_test_environment()

        # Get Django test runner
        TestRunner = get_runner(settings)
        test_runner = TestRunner(
            verbosity=self.verbosity,
            interactive=self.interactive,
            keepdb=self.keepdb,
            **self.kwargs,
        )

        # Run tests
        failures = test_runner.run_tests(test_labels)

        return failures


def run_tests(test_labels=None, verbosity=1, interactive=True, keepdb=False, **kwargs):
    """
    Run the test suite.

    Args:
        test_labels: List of test labels to run
        verbosity: Verbosity level (0, 1, 2)
        interactive: Whether to run in interactive mode
        keepdb: Whether to keep the test database
        **kwargs: Additional arguments

    Returns:
        int: Number of test failures
    """
    runner = ECommerceTestRunner(
        verbosity=verbosity, interactive=interactive, keepdb=keepdb, **kwargs
    )

    return runner.run_tests(test_labels)


if __name__ == "__main__":
    # Allow running tests directly
    test_labels = sys.argv[1:] if len(sys.argv) > 1 else None
    failures = run_tests(test_labels)
    sys.exit(failures)
