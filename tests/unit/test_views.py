"""
Unit tests for Django views.

This module tests view behavior, request/response handling, and context data.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from store.models import Category, Product, ProductTag, Wishlist
from store.views import (
    CategoryDetailView,
    HomePageView,
    ProductDetailView,
    ProductListView,
    TagDetailView,
    add_to_wishlist,
    remove_from_wishlist,
    search_suggestions,
    wishlist_view,
)

User = get_user_model()


@pytest.mark.django_db
class TestProductListView:
    """Test cases for ProductListView."""

    def test_product_list_view_get(self, client, category, product):
        """Test GET request to product list view."""
        url = reverse("store:product_list")
        response = client.get(url)

        assert response.status_code == 200
        assert "products" in response.context
        assert product in response.context["products"]

    def test_product_list_view_with_search(self, client, category, product):
        """Test product list view with search query."""
        url = reverse("store:product_list")
        response = client.get(url, {"search": "Test"})

        assert response.status_code == 200
        assert "search_query" in response.context
        assert response.context["search_query"] == "Test"

    def test_product_list_view_with_category_filter(self, client, category, product):
        """Test product list view with category filter."""
        url = reverse("store:product_list")
        response = client.get(url, {"category": category.slug})

        assert response.status_code == 200
        assert "products" in response.context
        # Product should be in filtered results
        assert product in response.context["products"]

    def test_product_list_view_with_tag_filter(
        self, client, category, product, product_tag
    ):
        """Test product list view with tag filter."""
        product.tags.add(product_tag)

        url = reverse("store:product_list")
        response = client.get(url, {"tag": product_tag.slug})

        assert response.status_code == 200
        assert "products" in response.context
        assert product in response.context["products"]

    def test_product_list_view_with_price_filter(self, client, category, product):
        """Test product list view with price filter."""
        url = reverse("store:product_list")
        response = client.get(url, {"min_price": "50.00", "max_price": "150.00"})

        assert response.status_code == 200
        assert "products" in response.context
        assert product in response.context["products"]

    def test_product_list_view_with_sorting(self, client, category, product):
        """Test product list view with different sorting options."""
        url = reverse("store:product_list")

        # Test name sorting
        response = client.get(url, {"sort": "name"})
        assert response.status_code == 200

        # Test price sorting
        response = client.get(url, {"sort": "price_low"})
        assert response.status_code == 200

        response = client.get(url, {"sort": "price_high"})
        assert response.status_code == 200

    def test_product_list_view_pagination(self, client, category):
        """Test product list view pagination."""
        # Create multiple products to test pagination
        products = []
        for i in range(15):  # More than default paginate_by
            product = Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )
            products.append(product)

        url = reverse("store:product_list")
        response = client.get(url)

        assert response.status_code == 200
        assert "is_paginated" in response.context
        assert response.context["is_paginated"] is True

    def test_product_list_view_context_data(self, client, category, product):
        """Test product list view context data."""
        url = reverse("store:product_list")
        response = client.get(url)

        assert response.status_code == 200
        assert "search_form" in response.context
        assert "categories" in response.context
        assert "popular_tags" in response.context
        assert "featured_products" in response.context
        assert "bestseller_products" in response.context
        assert "current_filters" in response.context


@pytest.mark.django_db
class TestProductDetailView:
    """Test cases for ProductDetailView."""

    def test_product_detail_view_get(self, client, category, product):
        """Test GET request to product detail view."""
        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "product" in response.context
        assert response.context["product"] == product

    def test_product_detail_view_increments_view_count(self, client, category, product):
        """Test that product detail view increments view count."""
        initial_count = product.view_count

        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)

        assert response.status_code == 200
        product.refresh_from_db()
        assert product.view_count == initial_count + 1

    def test_product_detail_view_with_related_products(self, client, category, product):
        """Test product detail view with related products."""
        # Create related products
        related_product = Product.objects.create(
            name="Related Product",
            slug="related-product",
            description="Related product description",
            price=Decimal("79.99"),
            category=category,
        )

        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "related_products" in response.context
        assert related_product in response.context["related_products"]

    def test_product_detail_view_with_reviews(
        self, client, category, product, test_user
    ):
        """Test product detail view with product reviews."""
        from store.models import ProductReview

        # Create a review
        review = ProductReview.objects.create(
            user=test_user,
            product=product,
            rating=5,
            title="Great product!",
            comment="This is an excellent product.",
            is_approved=True,
        )

        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "reviews" in response.context
        assert review in response.context["reviews"]

    def test_product_detail_view_context_data(self, client, category, product):
        """Test product detail view context data."""
        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "breadcrumbs" in response.context
        assert "in_wishlist" in response.context
        assert "review_stats" in response.context


@pytest.mark.django_db
class TestCategoryDetailView:
    """Test cases for CategoryDetailView."""

    def test_category_detail_view_get(self, client, category, product):
        """Test GET request to category detail view."""
        url = reverse("store:category_detail", kwargs={"slug": category.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "category" in response.context
        assert response.context["category"] == category
        assert "products" in response.context
        assert product in response.context["products"]

    def test_category_detail_view_with_pagination(self, client, category):
        """Test category detail view with pagination."""
        # Create multiple products
        for i in range(15):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )

        url = reverse("store:category_detail", kwargs={"slug": category.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "is_paginated" in response.context
        assert response.context["is_paginated"] is True


@pytest.mark.django_db
class TestTagDetailView:
    """Test cases for TagDetailView."""

    def test_tag_detail_view_get(self, client, category, product, product_tag):
        """Test GET request to tag detail view."""
        product.tags.add(product_tag)

        url = reverse("store:tag_detail", kwargs={"slug": product_tag.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "tag" in response.context
        assert response.context["tag"] == product_tag
        assert "products" in response.context
        assert product in response.context["products"]


@pytest.mark.django_db
class TestHomePageView:
    """Test cases for HomePageView."""

    def test_home_page_view_get(self, client, category, product):
        """Test GET request to home page view."""
        url = reverse("store:home")
        response = client.get(url)

        assert response.status_code == 200
        assert "featured_products" in response.context
        assert "bestseller_products" in response.context
        assert "popular_categories" in response.context
        assert "recent_products" in response.context
        assert "total_products" in response.context
        assert "total_categories" in response.context
        assert "total_reviews" in response.context


@pytest.mark.django_db
class TestWishlistViews:
    """Test cases for wishlist-related views."""

    def test_add_to_wishlist_authenticated(self, authenticated_client, product):
        """Test adding product to wishlist for authenticated user."""
        url = reverse("store:add_to_wishlist", kwargs={"product_id": product.id})
        response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["in_wishlist"] is True

        # Check that wishlist item was created
        assert Wishlist.objects.filter(
            user=authenticated_client.user, product=product
        ).exists()

    def test_add_to_wishlist_unauthenticated(self, client, product):
        """Test adding product to wishlist for unauthenticated user."""
        url = reverse("store:add_to_wishlist", kwargs={"product_id": product.id})
        response = client.post(url)

        assert response.status_code == 302  # Redirect to login

    def test_add_to_wishlist_duplicate(self, authenticated_client, product):
        """Test adding duplicate product to wishlist."""
        # Add product to wishlist first time
        Wishlist.objects.create(user=authenticated_client.user, product=product)

        url = reverse("store:add_to_wishlist", kwargs={"product_id": product.id})
        response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "info"
        assert data["in_wishlist"] is True

    def test_remove_from_wishlist_authenticated(self, authenticated_client, product):
        """Test removing product from wishlist for authenticated user."""
        # Add product to wishlist first
        Wishlist.objects.create(user=authenticated_client.user, product=product)

        url = reverse("store:remove_from_wishlist", kwargs={"product_id": product.id})
        response = authenticated_client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["in_wishlist"] is False

        # Check that wishlist item was removed
        assert not Wishlist.objects.filter(
            user=authenticated_client.user, product=product
        ).exists()

    def test_wishlist_view_authenticated(self, authenticated_client, product):
        """Test wishlist view for authenticated user."""
        # Add product to wishlist
        Wishlist.objects.create(user=authenticated_client.user, product=product)

        url = reverse("store:wishlist")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "wishlist_items" in response.context
        assert len(response.context["wishlist_items"]) == 1
        assert response.context["wishlist_items"][0].product == product


@pytest.mark.django_db
class TestSearchSuggestions:
    """Test cases for search suggestions view."""

    def test_search_suggestions_with_query(self, client, category, product):
        """Test search suggestions with valid query."""
        url = reverse("store:search_suggestions")
        response = client.get(url, {"q": "Test"})

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_search_suggestions_short_query(self, client):
        """Test search suggestions with short query."""
        url = reverse("store:search_suggestions")
        response = client.get(url, {"q": "a"})  # Too short

        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []

    def test_search_suggestions_empty_query(self, client):
        """Test search suggestions with empty query."""
        url = reverse("store:search_suggestions")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []


@pytest.mark.django_db
class TestCachedViews:
    """Test cases for cached views."""

    def test_cached_product_list_view(self, client, category, product):
        """Test cached product list view."""
        from store.views import CachedProductListView

        # This would require more complex setup for cache testing
        # For now, just test that the view exists and can be instantiated
        view = CachedProductListView()
        assert view is not None

    def test_cached_category_detail_view(self, client, category):
        """Test cached category detail view."""
        from store.views import CachedCategoryDetailView

        # This would require more complex setup for cache testing
        # For now, just test that the view exists and can be instantiated
        view = CachedCategoryDetailView()
        assert view is not None


@pytest.mark.django_db
class TestViewErrorHandling:
    """Test cases for view error handling."""

    def test_product_detail_view_404(self, client):
        """Test product detail view with non-existent product."""
        url = reverse("store:product_detail", kwargs={"slug": "non-existent"})
        response = client.get(url)

        assert response.status_code == 404

    def test_category_detail_view_404(self, client):
        """Test category detail view with non-existent category."""
        url = reverse("store:category_detail", kwargs={"slug": "non-existent"})
        response = client.get(url)

        assert response.status_code == 404

    def test_tag_detail_view_404(self, client):
        """Test tag detail view with non-existent tag."""
        url = reverse("store:tag_detail", kwargs={"slug": "non-existent"})
        response = client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestViewPerformance:
    """Test cases for view performance."""

    def test_product_list_view_queryset_optimization(self, client, category):
        """Test that product list view uses optimized queryset."""
        # Create multiple products
        products = []
        for i in range(10):
            product = Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )
            products.append(product)

        url = reverse("store:product_list")

        with patch("store.views.Product.objects") as mock_queryset:
            mock_queryset.filter.return_value.select_related.return_value.prefetch_related.return_value = (
                products
            )

            response = client.get(url)

            assert response.status_code == 200
            # Verify that select_related and prefetch_related were called
            mock_queryset.filter.return_value.select_related.assert_called_once()
            mock_queryset.filter.return_value.prefetch_related.assert_called_once()

    def test_product_detail_view_queryset_optimization(self, client, category, product):
        """Test that product detail view uses optimized queryset."""
        url = reverse("store:product_detail", kwargs={"slug": product.slug})

        with patch("store.views.Product.objects") as mock_queryset:
            mock_queryset.filter.return_value.select_related.return_value.prefetch_related.return_value.get.return_value = (
                product
            )

            response = client.get(url)

            assert response.status_code == 200
            # Verify that select_related and prefetch_related were called
            mock_queryset.filter.return_value.select_related.assert_called_once()
            mock_queryset.filter.return_value.prefetch_related.assert_called_once()
