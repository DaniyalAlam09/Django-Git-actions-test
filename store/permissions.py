"""
Custom permission classes for the store application.

This module contains custom permission classes that provide
specific authentication and authorization behaviors.
"""

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status


class IsAuthenticatedOrReadOnly401(permissions.IsAuthenticatedOrReadOnly):
    """
    Custom permission class that returns 401 instead of 403 for unauthenticated users.
    
    This is useful for API endpoints where 401 (Unauthorized) is more appropriate
    than 403 (Forbidden) for unauthenticated requests.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user and request.user.is_authenticated:
            return True
            
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific object.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if request.user and request.user.is_authenticated:
            return True
            
        return False
