"""
Factory Boy factories for creating test data.

This module contains factories for all models in the e-commerce application,
providing a convenient way to create test data with realistic defaults.
"""

from .user_factories import UserFactory, UserProfileFactory
from .product_factories import (
    CategoryFactory,
    ProductTagFactory,
    ProductFactory,
    ProductReviewFactory,
)
from .order_factories import (
    AddressFactory,
    PaymentMethodFactory,
    CartFactory,
    CartItemFactory,
    OrderFactory,
    OrderItemFactory,
)
from .wishlist_factories import WishlistFactory

__all__ = [
    "UserFactory",
    "UserProfileFactory",
    "CategoryFactory",
    "ProductTagFactory",
    "ProductFactory",
    "ProductReviewFactory",
    "AddressFactory",
    "PaymentMethodFactory",
    "CartFactory",
    "CartItemFactory",
    "OrderFactory",
    "OrderItemFactory",
    "WishlistFactory",
]
