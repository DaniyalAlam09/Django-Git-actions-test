"""
Unit tests for Django models.

This module tests model behavior, validation, methods, and business logic.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

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


@pytest.mark.django_db
class TestCategoryModel:
    """Test cases for Category model."""

    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices",
            is_active=True,
        )
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.is_active is True
        assert str(category) == "Electronics"

    def test_category_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        category = Category.objects.create(
            name="Test Category",
            description="Test description",
        )
        assert category.slug == "test-category"

    def test_category_get_absolute_url(self):
        """Test category absolute URL generation."""
        category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        expected_url = "/category/test-category/"
        assert category.get_absolute_url() == expected_url

    def test_category_str_representation(self):
        """Test string representation of category."""
        category = Category.objects.create(name="Test Category")
        assert str(category) == "Test Category"

    def test_category_ordering(self):
        """Test category ordering by sort_order."""
        cat1 = Category.objects.create(name="Category 1", sort_order=2)
        cat2 = Category.objects.create(name="Category 2", sort_order=1)
        cat3 = Category.objects.create(name="Category 3", sort_order=3)

        categories = Category.objects.all()
        assert categories[0] == cat2  # sort_order=1
        assert categories[1] == cat1  # sort_order=2
        assert categories[2] == cat3  # sort_order=3


@pytest.mark.django_db
class TestProductModel:
    """Test cases for Product model."""

    def test_product_creation(self, category):
        """Test basic product creation."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test description",
            price=Decimal("99.99"),
            category=category,
        )
        assert product.name == "Test Product"
        assert product.price == Decimal("99.99")
        assert product.category == category
        assert str(product) == "Test Product"

    def test_product_slug_auto_generation(self, category):
        """Test automatic slug generation from name."""
        product = Product.objects.create(
            name="Test Product Name",
            description="Test description",
            price=Decimal("99.99"),
            category=category,
        )
        assert product.slug == "test-product-name"

    def test_product_get_absolute_url(self, category):
        """Test product absolute URL generation."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test description",
            price=Decimal("99.99"),
            category=category,
        )
        expected_url = "/product/test-product/"
        assert product.get_absolute_url() == expected_url

    def test_product_price_validation(self, category):
        """Test product price validation."""
        # Test minimum price validation
        with pytest.raises(ValidationError):
            product = Product(
                name="Test Product",
                description="Test description",
                price=Decimal("0.00"),  # Below minimum
                category=category,
            )
            product.full_clean()

    def test_product_stock_management(self, category):
        """Test product stock management methods."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            stock_quantity=10,
            category=category,
        )

        # Test initial stock
        assert product.is_in_stock is True
        assert product.stock_quantity == 10

        # Test stock reduction
        product.reduce_stock(3)
        assert product.stock_quantity == 7
        assert product.is_in_stock is True

        # Test stock reduction below threshold
        product.reduce_stock(5)
        assert product.stock_quantity == 2
        assert product.is_in_stock is True  # Still above threshold

        # Test out of stock
        product.reduce_stock(2)
        assert product.stock_quantity == 0
        assert product.is_in_stock is False

    def test_product_sale_price_calculation(self, category):
        """Test product sale price and discount calculation."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("100.00"),
            sale_price=Decimal("80.00"),
            category=category,
        )

        assert product.get_current_price() == Decimal("80.00")
        assert product.get_discount_percentage() == 20.0
        assert product.is_on_sale is True

        # Test product without sale price
        product.sale_price = None
        product.save()
        assert product.get_current_price() == Decimal("100.00")
        assert product.get_discount_percentage() == 0.0
        assert product.is_on_sale is False

    def test_product_view_count_increment(self, category):
        """Test product view count increment."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            category=category,
        )

        initial_count = product.view_count
        product.increment_view_count()
        assert product.view_count == initial_count + 1

        # Test multiple increments
        product.increment_view_count()
        assert product.view_count == initial_count + 2

    def test_product_tags_relationship(self, category, product_tag):
        """Test product-tag many-to-many relationship."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            category=category,
        )

        product.tags.add(product_tag)
        assert product_tag in product.tags.all()
        assert product in product_tag.products.all()


@pytest.mark.django_db
class TestProductTagModel:
    """Test cases for ProductTag model."""

    def test_product_tag_creation(self):
        """Test basic product tag creation."""
        tag = ProductTag.objects.create(
            name="New Arrival",
            slug="new-arrival",
            description="Newly added products",
            color="#FF0000",
            is_active=True,
        )
        assert tag.name == "New Arrival"
        assert tag.color == "#FF0000"
        assert str(tag) == "New Arrival"

    def test_product_tag_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        tag = ProductTag.objects.create(
            name="Test Tag Name",
            description="Test description",
        )
        assert tag.slug == "test-tag-name"

    def test_product_tag_get_absolute_url(self):
        """Test product tag absolute URL generation."""
        tag = ProductTag.objects.create(
            name="Test Tag",
            slug="test-tag",
            description="Test description",
        )
        expected_url = "/tag/test-tag/"
        assert tag.get_absolute_url() == expected_url


@pytest.mark.django_db
class TestProductReviewModel:
    """Test cases for ProductReview model."""

    def test_product_review_creation(self, test_user, product):
        """Test basic product review creation."""
        review = ProductReview.objects.create(
            user=test_user,
            product=product,
            rating=5,
            title="Great product!",
            comment="This is an excellent product.",
            is_approved=True,
        )
        assert review.rating == 5
        assert review.title == "Great product!"
        assert str(review) == "Great product!"

    def test_product_review_rating_validation(self, test_user, product):
        """Test product review rating validation."""
        # Test valid ratings
        for rating in [1, 3, 5]:
            review = ProductReview(
                user=test_user,
                product=product,
                rating=rating,
                title="Test review",
                comment="This is a test review comment",
            )
            review.full_clean()  # Should not raise ValidationError

        # Test invalid ratings
        for rating in [0, 6, -1]:
            with pytest.raises(ValidationError):
                review = ProductReview(
                    user=test_user,
                    product=product,
                    rating=rating,
                    title="Test review",
                )
                review.full_clean()

    def test_product_review_helpful_votes(self, test_user, product):
        """Test product review helpful votes functionality."""
        review = ProductReview.objects.create(
            user=test_user,
            product=product,
            rating=5,
            title="Test review",
        )

        initial_votes = review.helpful_votes
        review.increment_helpful_votes()
        assert review.helpful_votes == initial_votes + 1


@pytest.mark.django_db
class TestUserProfileModel:
    """Test cases for UserProfile model."""

    def test_user_profile_creation(self, test_user):
        """Test basic user profile creation."""
        # Get the profile created by the signal
        profile = test_user.profile
        # Update the profile with test data
        profile.phone_number = "+1234567890"
        profile.date_of_birth = "1990-01-01"
        profile.gender = "M"
        profile.bio = "Test user bio"
        profile.save()
        
        assert profile.user == test_user
        assert profile.phone_number == "+1234567890"
        assert str(profile) == f"{test_user.username}'s Profile"

    def test_user_profile_auto_creation(self, test_user):
        """Test automatic user profile creation via signal."""
        # Refresh user from database to get the profile
        test_user.refresh_from_db()
        # Profile should be created automatically when user is created
        assert hasattr(test_user, "profile")
        assert test_user.profile is not None


@pytest.mark.django_db
class TestAddressModel:
    """Test cases for Address model."""

    def test_address_creation(self, test_user):
        """Test basic address creation."""
        address = Address.objects.create(
            user=test_user,
            address_type="shipping",
            first_name="John",
            last_name="Doe",
            address_line_1="123 Main St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        assert address.user == test_user
        assert address.address_type == "shipping"
        assert str(address) == "John Doe - 123 Main St, Test City, TS 12345"

    def test_address_full_name_property(self, test_user):
        """Test address full name property."""
        address = Address.objects.create(
            user=test_user,
            first_name="John",
            last_name="Doe",
            address_line_1="123 Main St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        assert address.full_name == "John Doe"

    def test_address_formatted_address_property(self, test_user):
        """Test address formatted address property."""
        address = Address.objects.create(
            user=test_user,
            first_name="John",
            last_name="Doe",
            address_line_1="123 Main St",
            address_line_2="Apt 1",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        expected = "123 Main St, Apt 1, Test City, TS 12345, US"
        assert address.formatted_address == expected


@pytest.mark.django_db
class TestPaymentMethodModel:
    """Test cases for PaymentMethod model."""

    def test_payment_method_creation(self, test_user, address):
        """Test basic payment method creation."""
        payment_method = PaymentMethod.objects.create(
            user=test_user,
            payment_type="credit_card",
            card_number="4111111111111111",
            cardholder_name="John Doe",
            expiry_month=12,
            expiry_year=2025,
            billing_address=address,
        )
        assert payment_method.user == test_user
        assert payment_method.payment_type == "credit_card"
        assert str(payment_method) == "John Doe - ****1111"

    def test_payment_method_masked_card_number(self, test_user, address):
        """Test payment method masked card number."""
        payment_method = PaymentMethod.objects.create(
            user=test_user,
            payment_type="credit_card",
            card_number="4111111111111111",
            cardholder_name="John Doe",
            expiry_month=12,
            expiry_year=2025,
            billing_address=address,
        )
        assert payment_method.masked_card_number == "****1111"


@pytest.mark.django_db
class TestCartModel:
    """Test cases for Cart model."""

    def test_cart_creation(self, test_user):
        """Test basic cart creation."""
        cart = Cart.objects.create(user=test_user)
        assert cart.user == test_user
        assert cart.total_items == 0
        assert cart.total_price == Decimal("0.00")

    def test_cart_total_calculation(self, test_user, product):
        """Test cart total calculation."""
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
        )

        # Refresh from database
        cart.refresh_from_db()
        assert cart.total_items == 2
        assert cart.total_price == product.get_display_price() * 2


@pytest.mark.django_db
class TestCartItemModel:
    """Test cases for CartItem model."""

    def test_cart_item_creation(self, cart, product):
        """Test basic cart item creation."""
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3,
        )
        assert cart_item.cart == cart
        assert cart_item.product == product
        assert cart_item.quantity == 3

    def test_cart_item_total_price_calculation(self, cart, product):
        """Test cart item total price calculation."""
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
        )
        expected_total = product.get_display_price() * 2
        assert cart_item.get_total_price() == expected_total

    def test_cart_item_currency_formatting(self, cart, product):
        """Test cart item currency formatting."""
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
        )
        formatted_price = cart_item.get_total_price_with_currency()
        assert formatted_price.startswith("$")
        assert "$" in formatted_price


@pytest.mark.django_db
class TestOrderModel:
    """Test cases for Order model."""

    def test_order_creation(self, test_user, address, payment_method):
        """Test basic order creation."""
        order = Order.objects.create(
            user=test_user,
            order_number="TEST-001",
            status="pending",
            payment_status="pending",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("8.00"),
            shipping_amount=Decimal("10.00"),
            total_amount=Decimal("118.00"),
            shipping_address=address,
            billing_address=address,
            payment_method=payment_method,
        )
        assert order.user == test_user
        assert order.order_number == "TEST-001"
        assert str(order) == "TEST-001"

    def test_order_status_choices(self, test_user, address):
        """Test order status choices validation."""
        valid_statuses = [
            "pending",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
        ]
        for status in valid_statuses:
            order = Order(
                user=test_user,
                order_number=f"TEST-{status}",
                status=status,
                subtotal=Decimal("100.00"),
                total_amount=Decimal("100.00"),
                shipping_address=address,
                billing_address=address,
            )
            order.full_clean()  # Should not raise ValidationError

    def test_order_payment_status_choices(self, test_user, address):
        """Test order payment status choices validation."""
        valid_statuses = ["pending", "paid", "failed", "refunded"]
        for status in valid_statuses:
            order = Order(
                user=test_user,
                order_number=f"TEST-{status}",
                payment_status=status,
                subtotal=Decimal("100.00"),
                total_amount=Decimal("100.00"),
                shipping_address=address,
                billing_address=address,
            )
            order.full_clean()  # Should not raise ValidationError


@pytest.mark.django_db
class TestOrderItemModel:
    """Test cases for OrderItem model."""

    def test_order_item_creation(self, order, product):
        """Test basic order item creation."""
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            unit_price=Decimal("50.00"),
            total_price=Decimal("100.00"),
        )
        assert order_item.order == order
        assert order_item.product == product
        assert order_item.quantity == 2
        assert str(order_item) == "2x Test Product in Order TEST-001"

    def test_order_item_currency_formatting(self, order, product):
        """Test order item currency formatting."""
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=Decimal("50.00"),
            total_price=Decimal("50.00"),
        )

        unit_formatted = order_item.get_unit_price_with_currency()
        total_formatted = order_item.get_total_with_currency()

        assert unit_formatted.startswith("$")
        assert total_formatted.startswith("$")
        assert "$50.00" in unit_formatted
        assert "$50.00" in total_formatted


@pytest.mark.django_db
class TestWishlistModel:
    """Test cases for Wishlist model."""

    def test_wishlist_creation(self, test_user, product):
        """Test basic wishlist item creation."""
        wishlist_item = Wishlist.objects.create(
            user=test_user,
            product=product,
        )
        assert wishlist_item.user == test_user
        assert wishlist_item.product == product
        assert str(wishlist_item) == f"{test_user.username} - {product.name}"

    def test_wishlist_unique_constraint(self, test_user, product):
        """Test wishlist unique constraint (user, product)."""
        # Create first wishlist item
        Wishlist.objects.create(user=test_user, product=product)

        # Try to create duplicate - should raise IntegrityError
        with pytest.raises(IntegrityError):
            Wishlist.objects.create(user=test_user, product=product)
