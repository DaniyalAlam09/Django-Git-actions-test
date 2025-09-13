"""
Pytest configuration and shared fixtures for the e-commerce application.

This module contains:
- Pytest configuration
- Shared fixtures for database setup
- Common test utilities
- Mock configurations
"""

import os
import tempfile
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from store.models import (
    Address,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    ProductReview,
    ProductTag,
    UserProfile,
    Wishlist,
)

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure test database for the entire test session."""
    with django_db_blocker.unblock():
        # Create test data that will be shared across all tests
        pass


@pytest.fixture
def test_user():
    """Create a test user for authentication tests."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def test_user_2():
    """Create a second test user for multi-user tests."""
    return User.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User2",
    )


@pytest.fixture
def admin_user():
    """Create an admin user for admin tests."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin123",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def category():
    """Create a test category."""
    return Category.objects.create(
        name="Electronics",
        slug="electronics",
        description="Electronic devices and gadgets",
        is_active=True,
    )


@pytest.fixture
def category_2():
    """Create a second test category."""
    return Category.objects.create(
        name="Clothing",
        slug="clothing",
        description="Fashion and apparel",
        is_active=True,
    )


@pytest.fixture
def product_tag():
    """Create a test product tag."""
    return ProductTag.objects.create(
        name="New Arrival",
        slug="new-arrival",
        description="Newly added products",
        is_active=True,
    )


@pytest.fixture
def product_tag_2():
    """Create a second test product tag."""
    return ProductTag.objects.create(
        name="On Sale",
        slug="on-sale",
        description="Discounted products",
        is_active=True,
    )


@pytest.fixture
def product(category, product_tag):
    """Create a test product."""
    # Create a simple test image
    image = SimpleUploadedFile(
        "test_image.jpg", b"file_content", content_type="image/jpeg"
    )

    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product for testing purposes",
        short_description="Test product",
        price=Decimal("99.99"),
        sale_price=Decimal("79.99"),
        stock_quantity=10,
        is_in_stock=True,
        category=category,
        main_image=image,
        is_active=True,
        is_featured=True,
        is_bestseller=False,
    )
    product.tags.add(product_tag)
    return product


@pytest.fixture
def product_2(category_2, product_tag_2):
    """Create a second test product."""
    image = SimpleUploadedFile(
        "test_image_2.jpg", b"file_content_2", content_type="image/jpeg"
    )

    product = Product.objects.create(
        name="Test Product 2",
        slug="test-product-2",
        description="Another test product for testing purposes",
        short_description="Test product 2",
        price=Decimal("149.99"),
        stock_quantity=5,
        is_in_stock=True,
        category=category_2,
        main_image=image,
        is_active=True,
        is_featured=False,
        is_bestseller=True,
    )
    product.tags.add(product_tag_2)
    return product


@pytest.fixture
def user_profile(test_user):
    """Create a user profile for the test user."""
    return UserProfile.objects.create(
        user=test_user,
        phone_number="+1234567890",
        date_of_birth="1990-01-01",
        gender="M",
        bio="Test user bio",
    )


@pytest.fixture
def address(test_user):
    """Create a test address."""
    return Address.objects.create(
        user=test_user,
        address_type="shipping",
        first_name="Test",
        last_name="User",
        company="Test Company",
        address_line_1="123 Test Street",
        address_line_2="Apt 1",
        city="Test City",
        state="TS",
        postal_code="12345",
        country="US",
        phone_number="+1234567890",
        is_default=True,
    )


@pytest.fixture
def payment_method(test_user):
    """Create a test payment method."""
    return PaymentMethod.objects.create(
        user=test_user,
        payment_type="credit_card",
        card_number="4111111111111111",
        cardholder_name="Test User",
        expiry_month=12,
        expiry_year=2025,
        is_default=True,
    )


@pytest.fixture
def cart(test_user):
    """Create a test cart."""
    return Cart.objects.create(user=test_user)


@pytest.fixture
def cart_item(cart, product):
    """Create a test cart item."""
    return CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2,
    )


@pytest.fixture
def order(test_user, address, payment_method):
    """Create a test order."""
    return Order.objects.create(
        user=test_user,
        order_number="TEST-001",
        status="pending",
        payment_status="pending",
        subtotal=Decimal("199.98"),
        tax_amount=Decimal("16.00"),
        shipping_amount=Decimal("10.00"),
        total_amount=Decimal("225.98"),
        shipping_address=address,
        billing_address=address,
        payment_method=payment_method,
    )


@pytest.fixture
def order_item(order, product):
    """Create a test order item."""
    return OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=Decimal("99.99"),
        total_price=Decimal("199.98"),
    )


@pytest.fixture
def product_review(test_user, product):
    """Create a test product review."""
    return ProductReview.objects.create(
        user=test_user,
        product=product,
        rating=5,
        title="Great product!",
        comment="This is an excellent product. Highly recommended!",
        is_approved=True,
    )


@pytest.fixture
def wishlist_item(test_user, product):
    """Create a test wishlist item."""
    return Wishlist.objects.create(
        user=test_user,
        product=product,
    )


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    client.force_login(test_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create an authenticated admin test client."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def temp_media_dir():
    """Create a temporary media directory for file upload tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with override_settings(MEDIA_ROOT=temp_dir):
            yield temp_dir


@pytest.fixture
def mock_image_upload():
    """Mock image upload for testing."""
    with patch("PIL.Image.open") as mock_open:
        mock_image = mock_open.return_value
        mock_image.verify.return_value = True
        mock_image.format = "JPEG"
        mock_image.size = (800, 600)
        yield mock_image


@pytest.fixture
def mock_email_backend():
    """Mock email backend for testing email functionality."""
    with patch("django.core.mail.send_mail") as mock_send_mail:
        mock_send_mail.return_value = True
        yield mock_send_mail


@pytest.fixture
def mock_payment_processing():
    """Mock payment processing for testing checkout."""
    with patch("store.checkout_views.process_payment") as mock_process:
        mock_process.return_value = {
            "success": True,
            "transaction_id": "test_txn_123",
            "status": "completed",
        }
        yield mock_process


@pytest.fixture
def mock_inventory_check():
    """Mock inventory check for testing cart operations."""
    with patch("store.cart_views.check_inventory") as mock_check:
        mock_check.return_value = True
        yield mock_check


# Test data fixtures
@pytest.fixture
def sample_products_data():
    """Sample product data for bulk testing."""
    return [
        {
            "name": "Sample Product 1",
            "slug": "sample-product-1",
            "description": "Description for sample product 1",
            "price": Decimal("29.99"),
            "stock_quantity": 50,
        },
        {
            "name": "Sample Product 2",
            "slug": "sample-product-2",
            "description": "Description for sample product 2",
            "price": Decimal("49.99"),
            "stock_quantity": 25,
        },
        {
            "name": "Sample Product 3",
            "slug": "sample-product-3",
            "description": "Description for sample product 3",
            "price": Decimal("79.99"),
            "stock_quantity": 10,
        },
    ]


@pytest.fixture
def sample_categories_data():
    """Sample category data for bulk testing."""
    return [
        {
            "name": "Electronics",
            "slug": "electronics",
            "description": "Electronic devices and gadgets",
        },
        {
            "name": "Clothing",
            "slug": "clothing",
            "description": "Fashion and apparel",
        },
        {
            "name": "Books",
            "slug": "books",
            "description": "Books and literature",
        },
    ]


# Performance testing fixtures
@pytest.fixture
def large_product_dataset(category):
    """Create a large dataset of products for performance testing."""
    products = []
    for i in range(100):
        product = Product.objects.create(
            name=f"Performance Test Product {i}",
            slug=f"performance-test-product-{i}",
            description=f"Description for performance test product {i}",
            price=Decimal(f"{10 + i}.99"),
            stock_quantity=10,
            category=category,
            is_active=True,
        )
        products.append(product)
    return products


# API testing fixtures
@pytest.fixture
def api_client():
    """Create an API test client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """Create an authenticated API test client."""
    api_client.force_authenticate(user=test_user)
    return api_client


# E2E testing fixtures
@pytest.fixture
def selenium_driver():
    """Create a Selenium WebDriver for E2E testing."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    except ImportError:
        pytest.skip("Selenium not available")
    except Exception as e:
        pytest.skip(f"Selenium WebDriver not available: {e}")


@pytest.fixture
def live_server_url(live_server):
    """Get the live server URL for E2E testing."""
    return live_server.url


# Utility functions for tests
def create_test_image(filename="test.jpg", size=(100, 100)):
    """Create a test image file."""
    import io

    from PIL import Image

    image = Image.new("RGB", size, color="red")
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)

    return SimpleUploadedFile(filename, image_io.getvalue(), content_type="image/jpeg")


def assert_response_contains(response, text, status_code=200):
    """Assert that response contains text and has correct status code."""
    assert response.status_code == status_code
    assert text in response.content.decode()


def assert_json_response(response, expected_data, status_code=200):
    """Assert that response is valid JSON with expected data."""
    assert response.status_code == status_code
    assert response["Content-Type"] == "application/json"
    data = response.json()
    for key, value in expected_data.items():
        assert data[key] == value
