"""
API URL configuration for the store application.

This module defines REST API endpoints for the store application,
providing JSON responses for frontend applications and mobile apps.
"""

from django.urls import path

from . import api_views

app_name = "store_api"

urlpatterns = [
    # Product API endpoints
    path("products/", api_views.ProductListAPIView.as_view(), name="product-list"),
    path(
        "products/<int:pk>/",
        api_views.ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    # Category API endpoints
    path(
        "categories/", api_views.CategoryListAPIView.as_view(), name="category-list"
    ),
    path(
        "categories/<int:pk>/",
        api_views.CategoryDetailAPIView.as_view(),
        name="category-detail",
    ),
    path(
        "categories/<slug:slug>/products/",
        api_views.CategoryProductsAPIView.as_view(),
        name="category_products_api",
    ),
    # Tag API endpoints
    path("tags/", api_views.TagListAPIView.as_view(), name="tag_list_api"),
    path(
        "tags/<slug:slug>/", api_views.TagDetailAPIView.as_view(), name="tag_detail_api"
    ),
    path(
        "tags/<slug:slug>/products/",
        api_views.TagProductsAPIView.as_view(),
        name="tag_products_api",
    ),
    # Search API endpoints
    path("search/", api_views.ProductSearchAPIView.as_view(), name="search_api"),
    path(
        "search/suggestions/",
        api_views.SearchSuggestionsAPIView.as_view(),
        name="search_suggestions_api",
    ),
    # Review API endpoints
    path(
        "products/<slug:slug>/reviews/",
        api_views.ProductReviewsAPIView.as_view(),
        name="product_reviews_api",
    ),
    path("reviews/", api_views.ReviewCreateAPIView.as_view(), name="review_create_api"),
    # Wishlist API endpoints (require authentication)
    path("wishlist/", api_views.WishlistAPIView.as_view(), name="wishlist-list"),
    path(
        "wishlist/add/",
        api_views.AddToWishlistAPIView.as_view(),
        name="wishlist-add",
    ),
    path(
        "wishlist/remove/",
        api_views.RemoveFromWishlistAPIView.as_view(),
        name="wishlist-remove",
    ),
    # Cart API endpoints (require authentication)
    path("cart/", api_views.CartAPIView.as_view(), name="cart-list"),
    path("cart/add/", api_views.AddToCartAPIView.as_view(), name="cart-add"),
    path(
        "cart/update/",
        api_views.UpdateCartItemAPIView.as_view(),
        name="cart-update",
    ),
    path(
        "cart/remove/",
        api_views.RemoveFromCartAPIView.as_view(),
        name="cart-remove",
    ),
    path("cart/clear/", api_views.ClearCartAPIView.as_view(), name="cart-clear"),
    path("cart/count/", api_views.CartCountAPIView.as_view(), name="cart_count_api"),
    # Order API endpoints (require authentication)
    path("orders/", api_views.OrderListAPIView.as_view(), name="order-list"),
    path(
        "orders/<int:pk>/",
        api_views.OrderDetailAPIView.as_view(),
        name="order-detail",
    ),
    # Address API endpoints (require authentication)
    path("addresses/", api_views.AddressListAPIView.as_view(), name="address_list_api"),
    # Payment Method API endpoints (require authentication)
    path(
        "payment-methods/",
        api_views.PaymentMethodListAPIView.as_view(),
        name="payment_method_list_api",
    ),
    # Analytics and statistics
    path(
        "stats/products/",
        api_views.ProductStatsAPIView.as_view(),
        name="product_stats_api",
    ),
    path(
        "stats/categories/",
        api_views.CategoryStatsAPIView.as_view(),
        name="category_stats_api",
    ),
    # Health check and monitoring
    path("health/", api_views.HealthCheckAPIView.as_view(), name="health_check_api"),
]
