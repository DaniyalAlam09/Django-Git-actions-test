"""
URL configuration for the store application.

This module defines the URL patterns for all store-related views
including product listings, details, categories, and user interactions.
"""

from django.urls import path

from . import auth_views, cart_views, checkout_views, views

app_name = "store"

urlpatterns = [
    # Homepage
    path("", views.HomePageView.as_view(), name="home"),
    # Product listing and search
    path("products/", views.ProductListView.as_view(), name="product_list"),
    # Product details
    path(
        "product/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"
    ),
    path(
        "products/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail_alt",
    ),
    # Category views
    path(
        "category/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        "categories/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category_detail_alt",
    ),
    # Tag views
    path("tag/<slug:slug>/", views.TagDetailView.as_view(), name="tag_detail"),
    path("tags/<slug:slug>/", views.TagDetailView.as_view(), name="tag_detail_alt"),
    # Search functionality
    path("search/", views.ProductListView.as_view(), name="search"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),
    # User-specific views (require authentication)
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path(
        "wishlist/add/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"
    ),
    path(
        "wishlist/remove/<int:product_id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    # Profile views
    path("profile/", auth_views.ProfileDetailView.as_view(), name="profile"),
    # Review views
    path("product/<int:product_id>/review/", views.add_review, name="add_review"),
    # Cached views for performance
    path("cached/", views.CachedProductListView.as_view(), name="cached_product_list"),
    path(
        "cached/category/<slug:slug>/",
        views.CachedCategoryDetailView.as_view(),
        name="cached_category_detail",
    ),
    # Authentication views
    path("signup/", auth_views.SignUpView.as_view(), name="signup"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("profile/setup/", auth_views.ProfileSetupView.as_view(), name="profile_setup"),
    path("profile/", auth_views.ProfileDetailView.as_view(), name="profile_detail"),
    path(
        "profile/edit/", auth_views.ProfileUpdateView.as_view(), name="profile_update"
    ),
    # Address management
    path("addresses/", auth_views.AddressListView.as_view(), name="address_list"),
    path(
        "addresses/add/", auth_views.AddressCreateView.as_view(), name="add_address"
    ),
    path(
        "addresses/<int:pk>/edit/",
        auth_views.AddressUpdateView.as_view(),
        name="address_update",
    ),
    path(
        "addresses/<int:pk>/delete/", auth_views.address_delete, name="address_delete"
    ),
    path(
        "addresses/add/",
        auth_views.AddressCreateView.as_view(),
        name="address_create",
    ),
    # Payment method management
    path(
        "payment-methods/",
        auth_views.PaymentMethodListView.as_view(),
        name="payment_method_list",
    ),
    path(
        "payment-methods/add/",
        auth_views.PaymentMethodCreateView.as_view(),
        name="add_payment_method",
    ),
    path(
        "payment-methods/create/",
        auth_views.PaymentMethodCreateView.as_view(),
        name="payment_method_create",
    ),
    path(
        "payment-methods/<int:pk>/delete/",
        auth_views.payment_method_delete,
        name="payment_method_delete",
    ),
    # Shopping cart
    path("cart/", cart_views.CartListView.as_view(), name="cart"),
    path("cart/", cart_views.CartListView.as_view(), name="cart_list"),
    path("cart/add/<int:product_id>/", cart_views.add_to_cart, name="add_to_cart"),
    path("cart/add/", cart_views.add_to_cart, name="add_to_cart_post"),
    path(
        "cart/update/<int:item_id>/",
        cart_views.update_cart_item,
        name="update_cart_item",
    ),
    path(
        "cart/update/",
        cart_views.update_cart_item,
        name="update_cart_item_post",
    ),
    path(
        "cart/remove/<int:item_id>/",
        cart_views.remove_from_cart,
        name="remove_from_cart",
    ),
    path(
        "cart/remove/",
        cart_views.remove_from_cart,
        name="remove_from_cart_post",
    ),
    path("cart/clear/", cart_views.clear_cart, name="clear_cart"),
    path("cart/count/", cart_views.get_cart_count, name="get_cart_count"),
    path("cart/apply-coupon/", cart_views.apply_coupon, name="apply_coupon"),
    path("cart/remove-coupon/", cart_views.remove_coupon, name="remove_coupon"),
    # Checkout
    path("checkout/", checkout_views.CheckoutView.as_view(), name="checkout"),
    path(
        "checkout/quick/<int:product_id>/",
        checkout_views.quick_checkout,
        name="quick_checkout",
    ),
    path(
        "order/confirmation/",
        checkout_views.OrderConfirmationView.as_view(),
        name="order_confirmation",
    ),
    path("orders/", checkout_views.OrderListView.as_view(), name="order_list"),
    path("orders/", checkout_views.OrderListView.as_view(), name="order_history"),
    path(
        "orders/<int:pk>/",
        checkout_views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "orders/<int:order_id>/",
        checkout_views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "orders/<int:order_id>/update-status/",
        checkout_views.update_order_status,
        name="update_order_status",
    ),
    path(
        "orders/<int:order_id>/add-tracking/",
        checkout_views.add_tracking_number,
        name="add_tracking_number",
    ),
]
