"""
Factory Boy factories for wishlist-related models.
"""

import factory
from factory.django import DjangoModelFactory

from store.models import Wishlist


class WishlistFactory(DjangoModelFactory):
    """Factory for creating Wishlist instances."""

    class Meta:
        model = Wishlist

    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    product = factory.SubFactory("tests.factories.product_factories.ProductFactory")
    added_at = factory.Faker("date_time_this_year")
    notes = factory.Faker("text", max_nb_chars=100)
