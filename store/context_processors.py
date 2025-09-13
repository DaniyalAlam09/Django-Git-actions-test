"""
Context processors for the store application.

This module provides context processors that add common data
to all templates across the application.
"""

from .models import Category


def categories(request):
    """
    Add active categories to template context.

    Args:
        request: HTTP request object

    Returns:
        dict: Context data with categories
    """
    return {"categories": Category.objects.filter(is_active=True).order_by("name")}
