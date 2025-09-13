"""
Store app configuration.

This file configures the store Django application with proper metadata
and initialization settings.
"""

from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "store"
    verbose_name = "E-Commerce Store"

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that signal handlers are properly registered.
        """
        try:
            import store.signals
        except ImportError:
            pass
