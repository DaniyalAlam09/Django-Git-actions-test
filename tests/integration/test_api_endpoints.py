"""
Integration tests for API endpoints.

This module tests API endpoints, authentication, serialization,
and complete API workflows.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from store.models import Cart, CartItem, Category, Order, OrderItem, Product, ProductTag


@pytest.mark.django_db
class TestProductAPI:
    """Test cases for Product API endpoints."""

    def test_product_list_api(self, api_client, category, product):
        """Test GET /api/products/ endpoint."""
        url = reverse("api:product-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == product.name

    def test_product_detail_api(self, api_client, category, product):
        """Test GET /api/products/{id}/ endpoint."""
        url = reverse("api:product-detail", kwargs={"pk": product.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == product.name
        assert response.data["price"] == str(product.price)
        assert response.data["category"]["name"] == category.name

    def test_product_list_api_with_filters(self, api_client, category, product):
        """Test Product API with various filters."""
        # Test category filter
        url = reverse("api:product-list")
        response = api_client.get(url, {"category": category.slug})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Test search filter
        response = api_client.get(url, {"search": "Test"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Test price range filter
        response = api_client.get(url, {"min_price": "50.00", "max_price": "150.00"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_product_list_api_pagination(self, api_client, category):
        """Test Product API pagination."""
        # Create multiple products
        for i in range(15):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )

        url = reverse("api:product-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert len(response.data["results"]) == 10  # Default page size

    def test_product_list_api_ordering(self, api_client, category, product):
        """Test Product API ordering."""
        # Create another product with different price
        product2 = Product.objects.create(
            name="Cheap Product",
            slug="cheap-product",
            description="Cheap product description",
            price=Decimal("49.99"),
            category=category,
        )

        url = reverse("api:product-list")

        # Test price ascending
        response = api_client.get(url, {"ordering": "price"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "Cheap Product"

        # Test price descending
        response = api_client.get(url, {"ordering": "-price"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == product.name


@pytest.mark.django_db
class TestCategoryAPI:
    """Test cases for Category API endpoints."""

    def test_category_list_api(self, api_client, category, product):
        """Test GET /api/categories/ endpoint."""
        url = reverse("api:category-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == category.name

    def test_category_detail_api(self, api_client, category):
        """Test GET /api/categories/{id}/ endpoint."""
        url = reverse("api:category-detail", kwargs={"pk": category.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category.name
        assert response.data["slug"] == category.slug


@pytest.mark.django_db
class TestCartAPI:
    """Test cases for Cart API endpoints."""

    def test_cart_list_api_authenticated(self, authenticated_api_client, test_user):
        """Test GET /api/cart/ endpoint for authenticated user."""
        # Create a cart for the user
        cart = Cart.objects.create(user=test_user)

        url = reverse("api:cart-list")
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.data
        assert response.data["total_items"] == 0
        assert response.data["total_price"] == "0.00"

    def test_cart_list_api_unauthenticated(self, api_client):
        """Test GET /api/cart/ endpoint for unauthenticated user."""
        url = reverse("api:cart-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cart_add_item_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/cart/add/ endpoint."""
        url = reverse("api:cart-add")
        data = {
            "product_id": product.id,
            "quantity": 2,
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"
        assert response.data["message"] == "Item added to cart"

        # Verify cart item was created
        cart = Cart.objects.get(user=test_user)
        assert cart.items.count() == 1
        cart_item = cart.items.first()
        assert cart_item.product == product
        assert cart_item.quantity == 2

    def test_cart_remove_item_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/cart/remove/ endpoint."""
        # Create cart and add item
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:cart-remove")
        data = {"product_id": product.id}
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

        # Verify cart item was removed
        assert cart.items.count() == 0

    def test_cart_update_item_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/cart/update/ endpoint."""
        # Create cart and add item
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:cart-update")
        data = {
            "product_id": product.id,
            "quantity": 5,
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

        # Verify cart item quantity was updated
        cart_item = cart.items.first()
        assert cart_item.quantity == 5

    def test_cart_clear_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/cart/clear/ endpoint."""
        # Create cart and add items
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:cart-clear")
        response = authenticated_api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

        # Verify cart was cleared
        assert cart.items.count() == 0


@pytest.mark.django_db
class TestWishlistAPI:
    """Test cases for Wishlist API endpoints."""

    def test_wishlist_list_api_authenticated(
        self, authenticated_api_client, test_user, product
    ):
        """Test GET /api/wishlist/ endpoint for authenticated user."""
        # Add product to wishlist
        from store.models import Wishlist

        Wishlist.objects.create(user=test_user, product=product)

        url = reverse("api:wishlist-list")
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["product"]["name"] == product.name

    def test_wishlist_add_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/wishlist/add/ endpoint."""
        url = reverse("api:wishlist-add")
        data = {"product_id": product.id}
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"

        # Verify wishlist item was created
        from store.models import Wishlist

        assert Wishlist.objects.filter(user=test_user, product=product).exists()

    def test_wishlist_remove_api(self, authenticated_api_client, test_user, product):
        """Test POST /api/wishlist/remove/ endpoint."""
        # Add product to wishlist first
        from store.models import Wishlist

        Wishlist.objects.create(user=test_user, product=product)

        url = reverse("api:wishlist-remove")
        data = {"product_id": product.id}
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

        # Verify wishlist item was removed
        assert not Wishlist.objects.filter(user=test_user, product=product).exists()


@pytest.mark.django_db
class TestOrderAPI:
    """Test cases for Order API endpoints."""

    def test_order_list_api_authenticated(
        self, authenticated_api_client, test_user, order
    ):
        """Test GET /api/orders/ endpoint for authenticated user."""
        url = reverse("api:order-list")
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["order_number"] == order.order_number

    def test_order_detail_api_authenticated(
        self, authenticated_api_client, test_user, order
    ):
        """Test GET /api/orders/{id}/ endpoint for authenticated user."""
        url = reverse("api:order-detail", kwargs={"pk": order.id})
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["order_number"] == order.order_number
        assert response.data["status"] == order.status
        assert response.data["total_amount"] == str(order.total_amount)

    def test_order_create_api(
        self, authenticated_api_client, test_user, product, address, payment_method
    ):
        """Test POST /api/orders/ endpoint."""
        # Create cart with items
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:order-list")
        data = {
            "shipping_address_id": address.id,
            "billing_address_id": address.id,
            "payment_method_id": payment_method.id,
            "notes": "Test order",
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"
        assert response.data["payment_status"] == "pending"

        # Verify order was created
        order = Order.objects.get(user=test_user)
        assert order.shipping_address == address
        assert order.billing_address == address
        assert order.payment_method == payment_method


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Test cases for API error handling."""

    def test_product_detail_api_404(self, api_client):
        """Test Product detail API with non-existent product."""
        url = reverse("api:product-detail", kwargs={"pk": 99999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_add_item_api_invalid_product(self, authenticated_api_client):
        """Test Cart add item API with invalid product ID."""
        url = reverse("api:cart-add")
        data = {
            "product_id": 99999,
            "quantity": 2,
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_cart_add_item_api_invalid_quantity(
        self, authenticated_api_client, product
    ):
        """Test Cart add item API with invalid quantity."""
        url = reverse("api:cart-add")
        data = {
            "product_id": product.id,
            "quantity": -1,  # Invalid quantity
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_order_create_api_insufficient_stock(
        self, authenticated_api_client, test_user, product, address, payment_method
    ):
        """Test Order create API with insufficient stock."""
        # Set product stock to 0
        product.stock_quantity = 0
        product.save()

        # Create cart with items
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:order-list")
        data = {
            "shipping_address_id": address.id,
            "billing_address_id": address.id,
            "payment_method_id": payment_method.id,
        }
        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data


@pytest.mark.django_db
class TestAPIAuthentication:
    """Test cases for API authentication."""

    def test_protected_endpoints_require_authentication(self, api_client):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            reverse("api:cart-list"),
            reverse("api:cart-add"),
            reverse("api:wishlist-list"),
            reverse("api:order-list"),
        ]

        for url in protected_endpoints:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_public_endpoints_allow_unauthenticated_access(
        self, api_client, category, product
    ):
        """Test that public endpoints allow unauthenticated access."""
        public_endpoints = [
            reverse("api:product-list"),
            reverse("api:product-detail", kwargs={"pk": product.id}),
            reverse("api:category-list"),
            reverse("api:category-detail", kwargs={"pk": category.id}),
        ]

        for url in public_endpoints:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAPISerialization:
    """Test cases for API serialization."""

    def test_product_serialization(self, api_client, category, product, product_tag):
        """Test Product serialization includes all required fields."""
        product.tags.add(product_tag)

        url = reverse("api:product-detail", kwargs={"pk": product.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Check required fields
        required_fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "sale_price",
            "stock_quantity",
            "is_in_stock",
            "category",
            "tags",
            "main_image",
            "is_active",
            "is_featured",
            "is_bestseller",
            "view_count",
        ]

        for field in required_fields:
            assert field in data

        # Check nested serialization
        assert "name" in data["category"]
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == product_tag.name

    def test_cart_serialization(self, authenticated_api_client, test_user, product):
        """Test Cart serialization includes all required fields."""
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse("api:cart-list")
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Check required fields
        required_fields = [
            "id",
            "user",
            "items",
            "total_items",
            "total_price",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in data

        # Check items serialization
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert "product" in item
        assert "quantity" in item
        assert item["product"]["name"] == product.name


@pytest.mark.django_db
class TestAPIPerformance:
    """Test cases for API performance."""

    def test_product_list_api_performance(self, api_client, category):
        """Test Product list API performance with large dataset."""
        # Create many products
        products = []
        for i in range(100):
            product = Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )
            products.append(product)

        url = reverse("api:product-list")

        # Test response time (should be reasonable)
        import time

        start_time = time.time()
        response = api_client.get(url)
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

    def test_product_list_api_with_prefetch(self, api_client, category, product_tag):
        """Test Product list API with prefetch optimization."""
        # Add tags to products
        products = []
        for i in range(10):
            product = Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )
            product.tags.add(product_tag)
            products.append(product)

        url = reverse("api:product-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 10

        # Check that tags are included (prefetch optimization)
        for product_data in response.data["results"]:
            assert "tags" in product_data
            assert len(product_data["tags"]) == 1
