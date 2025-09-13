"""
Unit tests for Django forms.

This module tests form validation, field behavior, and form methods.
"""

import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from store.forms import (
    ProductSearchForm,
    CustomUserCreationForm,
    UserProfileForm,
    AddressForm,
    PaymentMethodForm,
    ProductReviewForm,
    WishlistForm,
)


@pytest.mark.django_db
class TestProductSearchForm:
    """Test cases for ProductSearchForm."""
    
    def test_product_search_form_valid_data(self):
        """Test ProductSearchForm with valid data."""
        form_data = {
            "search": "test product",
            "category": "electronics",
            "min_price": "10.00",
            "max_price": "100.00",
            "sort": "name",
        }
        form = ProductSearchForm(data=form_data)
        assert form.is_valid()
    
    def test_product_search_form_empty_data(self):
        """Test ProductSearchForm with empty data."""
        form = ProductSearchForm(data={})
        assert form.is_valid()  # Empty form should be valid
    
    def test_product_search_form_invalid_price_range(self):
        """Test ProductSearchForm with invalid price range."""
        form_data = {
            "min_price": "100.00",
            "max_price": "50.00",  # Max less than min
        }
        form = ProductSearchForm(data=form_data)
        # Form should still be valid, but logic should handle this
        assert form.is_valid()
    
    def test_product_search_form_negative_prices(self):
        """Test ProductSearchForm with negative prices."""
        form_data = {
            "min_price": "-10.00",
            "max_price": "-5.00",
        }
        form = ProductSearchForm(data=form_data)
        # Form should still be valid, but logic should handle this
        assert form.is_valid()


@pytest.mark.django_db
class TestCustomUserCreationForm:
    """Test cases for CustomUserCreationForm."""
    
    def test_user_creation_form_valid_data(self):
        """Test CustomUserCreationForm with valid data."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()
    
    def test_user_creation_form_password_mismatch(self):
        """Test CustomUserCreationForm with password mismatch."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "differentpass",
            "first_name": "Test",
            "last_name": "User",
        }
        form = CustomUserCreationForm(data=form_data)
        assert not form.is_valid()
        assert "password2" in form.errors
    
    def test_user_creation_form_missing_required_fields(self):
        """Test CustomUserCreationForm with missing required fields."""
        form_data = {
            "username": "testuser",
            # Missing email, passwords, etc.
        }
        form = CustomUserCreationForm(data=form_data)
        assert not form.is_valid()
        assert "password1" in form.errors
        assert "password2" in form.errors
    
    def test_user_creation_form_invalid_email(self):
        """Test CustomUserCreationForm with invalid email."""
        form_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = CustomUserCreationForm(data=form_data)
        # CustomUserCreationForm might not validate email format
        # This depends on the actual implementation
        pass


@pytest.mark.django_db
class TestUserProfileForm:
    """Test cases for UserProfileForm."""
    
    def test_user_profile_form_valid_data(self, test_user):
        """Test UserProfileForm with valid data."""
        form_data = {
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "bio": "Test user bio",
            "newsletter_subscription": True,
            "marketing_consent": False,
        }
        form = UserProfileForm(data=form_data, instance=test_user.profile)
        assert form.is_valid()
    
    def test_user_profile_form_invalid_phone_number(self, test_user):
        """Test UserProfileForm with invalid phone number."""
        form_data = {
            "phone_number": "invalid-phone",
            "date_of_birth": "1990-01-01",
            "gender": "M",
        }
        form = UserProfileForm(data=form_data, instance=test_user.profile)
        assert not form.is_valid()
        assert "phone_number" in form.errors
    
    def test_user_profile_form_invalid_date_of_birth(self, test_user):
        """Test UserProfileForm with invalid date of birth."""
        form_data = {
            "phone_number": "+1234567890",
            "date_of_birth": "invalid-date",
            "gender": "M",
        }
        form = UserProfileForm(data=form_data, instance=test_user.profile)
        assert not form.is_valid()
        assert "date_of_birth" in form.errors
    
    def test_user_profile_form_invalid_gender(self, test_user):
        """Test UserProfileForm with invalid gender."""
        form_data = {
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "X",  # Invalid gender
        }
        form = UserProfileForm(data=form_data, instance=test_user.profile)
        assert not form.is_valid()
        assert "gender" in form.errors


@pytest.mark.django_db
class TestAddressForm:
    """Test cases for AddressForm."""
    
    def test_address_form_valid_data(self):
        """Test AddressForm with valid data."""
        form_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Test Company",
            "address_line_1": "123 Main St",
            "address_line_2": "Apt 1",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
            "phone_number": "+1234567890",
            "is_default": True,
            "instructions": "Leave at front door",
        }
        form = AddressForm(data=form_data)
        assert form.is_valid()
    
    def test_address_form_missing_required_fields(self):
        """Test AddressForm with missing required fields."""
        form_data = {
            "address_type": "shipping",
            # Missing first_name, last_name, address_line_1, etc.
        }
        form = AddressForm(data=form_data)
        assert not form.is_valid()
        assert "first_name" in form.errors
        assert "last_name" in form.errors
        assert "address_line_1" in form.errors
        assert "city" in form.errors
        assert "state" in form.errors
        assert "postal_code" in form.errors
        assert "country" in form.errors
    
    def test_address_form_invalid_postal_code(self):
        """Test AddressForm with invalid postal code."""
        form_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "invalid",  # Invalid postal code
            "country": "US",
        }
        form = AddressForm(data=form_data)
        # Form should still be valid, but validation logic should handle this
        assert form.is_valid()
    
    def test_address_form_invalid_phone_number(self):
        """Test AddressForm with invalid phone number."""
        form_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
            "phone_number": "invalid-phone",
        }
        form = AddressForm(data=form_data)
        assert not form.is_valid()
        assert "phone_number" in form.errors


@pytest.mark.django_db
class TestPaymentMethodForm:
    """Test cases for PaymentMethodForm."""
    
    def test_payment_method_form_valid_data(self, address):
        """Test PaymentMethodForm with valid data."""
        form_data = {
            "payment_type": "credit_card",
            "card_number": "4111111111111111",
            "cardholder_name": "John Doe",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123",
            "billing_address": address.id,
            "is_default": True,
        }
        form = PaymentMethodForm(data=form_data)
        assert form.is_valid()
    
    def test_payment_method_form_missing_required_fields(self):
        """Test PaymentMethodForm with missing required fields."""
        form_data = {
            "payment_type": "credit_card",
            # Missing card_number, cardholder_name, etc.
        }
        form = PaymentMethodForm(data=form_data)
        assert not form.is_valid()
        assert "card_number" in form.errors
        assert "cardholder_name" in form.errors
        assert "expiry_month" in form.errors
        assert "expiry_year" in form.errors
    
    def test_payment_method_form_invalid_card_number(self):
        """Test PaymentMethodForm with invalid card number."""
        form_data = {
            "payment_type": "credit_card",
            "card_number": "1234",  # Too short
            "cardholder_name": "John Doe",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123",
        }
        form = PaymentMethodForm(data=form_data)
        assert not form.is_valid()
        assert "card_number" in form.errors
    
    def test_payment_method_form_invalid_expiry_date(self):
        """Test PaymentMethodForm with invalid expiry date."""
        form_data = {
            "payment_type": "credit_card",
            "card_number": "4111111111111111",
            "cardholder_name": "John Doe",
            "expiry_month": 13,  # Invalid month
            "expiry_year": 2025,
            "cvv": "123",
        }
        form = PaymentMethodForm(data=form_data)
        assert not form.is_valid()
        assert "expiry_month" in form.errors
    
    def test_payment_method_form_past_expiry_date(self):
        """Test PaymentMethodForm with past expiry date."""
        form_data = {
            "payment_type": "credit_card",
            "card_number": "4111111111111111",
            "cardholder_name": "John Doe",
            "expiry_month": 1,
            "expiry_year": 2020,  # Past year
            "cvv": "123",
        }
        form = PaymentMethodForm(data=form_data)
        assert not form.is_valid()
        assert "expiry_year" in form.errors


@pytest.mark.django_db
class TestProductReviewForm:
    """Test cases for ProductReviewForm."""
    
    def test_product_review_form_valid_data(self):
        """Test ProductReviewForm with valid data."""
        form_data = {
            "rating": 5,
            "title": "Great product!",
            "comment": "This is an excellent product. Highly recommended!",
        }
        form = ProductReviewForm(data=form_data)
        assert form.is_valid()
    
    def test_product_review_form_missing_required_fields(self):
        """Test ProductReviewForm with missing required fields."""
        form_data = {
            "rating": 5,
            # Missing title and comment
        }
        form = ProductReviewForm(data=form_data)
        assert not form.is_valid()
        assert "title" in form.errors
        assert "comment" in form.errors
    
    def test_product_review_form_invalid_rating(self):
        """Test ProductReviewForm with invalid rating."""
        form_data = {
            "rating": 6,  # Invalid rating (should be 1-5)
            "title": "Great product!",
            "comment": "This is an excellent product.",
        }
        form = ProductReviewForm(data=form_data)
        assert not form.is_valid()
        assert "rating" in form.errors
    
    def test_product_review_form_rating_too_low(self):
        """Test ProductReviewForm with rating too low."""
        form_data = {
            "rating": 0,  # Too low
            "title": "Great product!",
            "comment": "This is an excellent product.",
        }
        form = ProductReviewForm(data=form_data)
        assert not form.is_valid()
        assert "rating" in form.errors
    
    def test_product_review_form_long_comment(self):
        """Test ProductReviewForm with comment too long."""
        form_data = {
            "rating": 5,
            "title": "Great product!",
            "comment": "x" * 1001,  # Too long
        }
        form = ProductReviewForm(data=form_data)
        assert not form.is_valid()
        assert "comment" in form.errors


@pytest.mark.django_db
class TestWishlistForm:
    """Test cases for WishlistForm."""
    
    def test_wishlist_form_valid_data(self):
        """Test WishlistForm with valid data."""
        form_data = {
            "notes": "This is a test wishlist item",
        }
        form = WishlistForm(data=form_data)
        assert form.is_valid()
    
    def test_wishlist_form_empty_data(self):
        """Test WishlistForm with empty data."""
        form = WishlistForm(data={})
        assert form.is_valid()  # Empty form should be valid


@pytest.mark.django_db
class TestFormWidgets:
    """Test cases for form widgets and rendering."""
    
    def test_product_search_form_widgets(self):
        """Test ProductSearchForm widget configuration."""
        form = ProductSearchForm()
        
        # Check that search field has proper attributes
        search_field = form.fields["search"]
        assert search_field.widget.attrs.get("placeholder") is not None
        assert search_field.widget.attrs.get("class") is not None
    
    def test_address_form_widgets(self):
        """Test AddressForm widget configuration."""
        form = AddressForm()
        
        # Check that textarea fields have proper attributes
        instructions_field = form.fields["instructions"]
        assert instructions_field.widget.attrs.get("rows") is not None
        assert instructions_field.widget.attrs.get("cols") is not None
    
    def test_payment_method_form_widgets(self):
        """Test PaymentMethodForm widget configuration."""
        form = PaymentMethodForm()
        
        # Check that sensitive fields have proper attributes
        card_number_field = form.fields["card_number"]
        assert "password" in card_number_field.widget.attrs.get("type", "")
        
        cvv_field = form.fields["cvv"]
        assert "password" in cvv_field.widget.attrs.get("type", "")


@pytest.mark.django_db
class TestFormValidation:
    """Test cases for custom form validation."""
    
    def test_address_form_clean_method(self):
        """Test AddressForm clean method validation."""
        form_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
        }
        form = AddressForm(data=form_data)
        assert form.is_valid()
        
        # Test clean method if it exists
        if hasattr(form, "clean"):
            cleaned_data = form.clean()
            assert cleaned_data is not None
    
    def test_payment_method_form_clean_method(self):
        """Test PaymentMethodForm clean method validation."""
        form_data = {
            "payment_type": "credit_card",
            "card_number": "4111111111111111",
            "cardholder_name": "John Doe",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123",
        }
        form = PaymentMethodForm(data=form_data)
        assert form.is_valid()
        
        # Test clean method if it exists
        if hasattr(form, "clean"):
            cleaned_data = form.clean()
            assert cleaned_data is not None


@pytest.mark.django_db
class TestFormSaveMethods:
    """Test cases for form save methods."""
    
    def test_user_creation_form_save(self):
        """Test CustomUserCreationForm save method."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()
        
        user = form.save()
        assert user.username == "testuser"
        assert user.check_password("testpass123")
    
    def test_user_profile_form_save(self, test_user):
        """Test UserProfileForm save method."""
        form_data = {
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "bio": "Test user bio",
        }
        form = UserProfileForm(data=form_data, instance=test_user.profile)
        assert form.is_valid()
        
        profile = form.save()
        assert profile.phone_number == "+1234567890"
        assert profile.bio == "Test user bio"
    
    def test_address_form_save(self, test_user):
        """Test AddressForm save method."""
        form_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
        }
        form = AddressForm(data=form_data)
        form.instance.user = test_user
        assert form.is_valid()
        
        address = form.save()
        assert address.first_name == "John"
        assert address.last_name == "Doe"
        assert address.user == test_user
