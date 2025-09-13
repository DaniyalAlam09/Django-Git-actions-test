"""
Factory Boy factories for user-related models.
"""

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from store.models import UserProfile

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or "testpass123"
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""
    
    username = "admin"
    email = "admin@example.com"
    is_staff = True
    is_superuser = True


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""
    
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    phone_number = factory.Faker("phone_number")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=18, maximum_age=80)
    gender = factory.Iterator(["M", "F", "O"])
    bio = factory.Faker("text", max_nb_chars=200)
    avatar = factory.django.ImageField(color="blue")
    is_verified = factory.Faker("boolean", chance_of_getting_true=80)
    newsletter_subscription = factory.Faker("boolean", chance_of_getting_true=60)
    marketing_consent = factory.Faker("boolean", chance_of_getting_true=40)
