"""
Django signals for the store application.

This module contains signal handlers for automatic creation
of related objects when users are created.
"""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a User is created.

    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.

    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
