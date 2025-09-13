"""
Test image fixtures for media testing.

This module provides utilities for creating test images
and handling media files in tests.
"""

import os
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings


def create_test_image(filename="test.jpg", size=(100, 100), color="red", format="JPEG"):
    """
    Create a test image file.
    
    Args:
        filename: Name of the image file
        size: Tuple of (width, height) for image dimensions
        color: Color of the image (name or hex code)
        format: Image format (JPEG, PNG, etc.)
    
    Returns:
        SimpleUploadedFile: Django file object for testing
    """
    image = Image.new("RGB", size, color=color)
    image_io = tempfile.NamedTemporaryFile(suffix=f".{format.lower()}")
    image.save(image_io, format=format)
    image_io.seek(0)
    
    return SimpleUploadedFile(
        filename,
        image_io.getvalue(),
        content_type=f"image/{format.lower()}"
    )


def create_test_image_suite():
    """
    Create a suite of test images for comprehensive testing.
    
    Returns:
        dict: Dictionary containing various test images
    """
    return {
        "small_jpeg": create_test_image("small.jpg", (50, 50), "blue", "JPEG"),
        "medium_jpeg": create_test_image("medium.jpg", (200, 200), "green", "JPEG"),
        "large_jpeg": create_test_image("large.jpg", (800, 600), "red", "JPEG"),
        "small_png": create_test_image("small.png", (50, 50), "yellow", "PNG"),
        "medium_png": create_test_image("medium.png", (200, 200), "purple", "PNG"),
        "large_png": create_test_image("large.png", (800, 600), "orange", "PNG"),
        "square_image": create_test_image("square.jpg", (300, 300), "teal", "JPEG"),
        "wide_image": create_test_image("wide.jpg", (800, 400), "pink", "JPEG"),
        "tall_image": create_test_image("tall.jpg", (400, 800), "brown", "JPEG"),
    }


def create_product_image_variants():
    """
    Create product image variants for testing.
    
    Returns:
        dict: Dictionary containing product image variants
    """
    return {
        "main_image": create_test_image("main.jpg", (500, 500), "blue", "JPEG"),
        "thumbnail": create_test_image("thumb.jpg", (150, 150), "blue", "JPEG"),
        "gallery_1": create_test_image("gallery1.jpg", (400, 400), "green", "JPEG"),
        "gallery_2": create_test_image("gallery2.jpg", (400, 400), "red", "JPEG"),
        "gallery_3": create_test_image("gallery3.jpg", (400, 400), "yellow", "JPEG"),
    }


def create_user_avatar_variants():
    """
    Create user avatar variants for testing.
    
    Returns:
        dict: Dictionary containing user avatar variants
    """
    return {
        "small_avatar": create_test_image("avatar_small.jpg", (50, 50), "purple", "JPEG"),
        "medium_avatar": create_test_image("avatar_medium.jpg", (100, 100), "purple", "JPEG"),
        "large_avatar": create_test_image("avatar_large.jpg", (200, 200), "purple", "JPEG"),
    }


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
def create_temp_media_directory():
    """
    Create a temporary media directory for testing.
    
    Returns:
        str: Path to the temporary media directory
    """
    return tempfile.mkdtemp()


def cleanup_test_images():
    """
    Clean up test images after testing.
    This should be called in test teardown.
    """
    # This would be implemented based on your specific cleanup needs
    pass


# Test image data for different scenarios
TEST_IMAGE_DATA = {
    "valid_images": [
        {"filename": "valid1.jpg", "size": (100, 100), "color": "blue"},
        {"filename": "valid2.png", "size": (200, 200), "color": "green"},
        {"filename": "valid3.jpeg", "size": (300, 300), "color": "red"},
    ],
    "invalid_images": [
        {"filename": "invalid1.txt", "size": (100, 100), "color": "blue"},  # Wrong extension
        {"filename": "invalid2.jpg", "size": (0, 0), "color": "blue"},      # Zero size
        {"filename": "invalid3.jpg", "size": (100, 100), "color": "blue"},  # Corrupted data
    ],
    "large_images": [
        {"filename": "large1.jpg", "size": (2000, 2000), "color": "blue"},
        {"filename": "large2.jpg", "size": (4000, 3000), "color": "green"},
    ],
    "small_images": [
        {"filename": "small1.jpg", "size": (10, 10), "color": "blue"},
        {"filename": "small2.jpg", "size": (20, 20), "color": "green"},
    ],
}
