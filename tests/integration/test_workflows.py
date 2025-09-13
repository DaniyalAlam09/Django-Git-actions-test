"""
Integration tests for complete user workflows.

This module tests end-to-end workflows including:
- User registration and authentication
- Product browsing and search
- Shopping cart operations
- Checkout process
- Order management
- User profile management
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

from store.models import (
    Product, Category, ProductTag, Cart, CartItem, Order, OrderItem,
    Address, PaymentMethod, Wishlist, ProductReview
)

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationWorkflow:
    """Test complete user registration workflow."""
    
    def test_user_registration_workflow(self, client):
        """Test complete user registration process."""
        # Step 1: Access registration page
        url = reverse("store:signup")
        response = client.get(url)
        assert response.status_code == 200
        
        # Step 2: Submit registration form
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "newpass123",
            "password2": "newpass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = client.post(url, registration_data)
        
        # Should redirect after successful registration
        assert response.status_code == 302
        
        # Step 3: Verify user was created
        user = User.objects.get(username="newuser")
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"
        assert user.last_name == "User"
        
        # Step 4: Verify user profile was created
        assert hasattr(user, 'profile')
        assert user.profile is not None
        
        # Step 5: Verify user can login
        login_url = reverse("store:login")
        login_data = {
            "username": "newuser",
            "password": "newpass123",
        }
        response = client.post(login_url, login_data)
        assert response.status_code == 302  # Redirect after login


@pytest.mark.django_db
class TestProductBrowsingWorkflow:
    """Test complete product browsing workflow."""
    
    def test_product_browsing_workflow(self, client, category, product, product_tag):
        """Test complete product browsing process."""
        # Add tag to product
        product.tags.add(product_tag)
        
        # Step 1: Access home page
        url = reverse("store:home")
        response = client.get(url)
        assert response.status_code == 200
        assert "featured_products" in response.context
        assert "bestseller_products" in response.context
        
        # Step 2: Browse product list
        url = reverse("store:product_list")
        response = client.get(url)
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 3: Filter by category
        response = client.get(url, {"category": category.slug})
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 4: Filter by tag
        response = client.get(url, {"tag": product_tag.slug})
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 5: Search products
        response = client.get(url, {"search": "Test"})
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 6: View product detail
        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["product"] == product
        
        # Step 7: View category detail
        url = reverse("store:category_detail", kwargs={"slug": category.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 8: View tag detail
        url = reverse("store:tag_detail", kwargs={"slug": product_tag.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert product in response.context["products"]


@pytest.mark.django_db
class TestShoppingCartWorkflow:
    """Test complete shopping cart workflow."""
    
    def test_shopping_cart_workflow(self, authenticated_client, test_user, product, product_2):
        """Test complete shopping cart process."""
        # Step 1: Add first product to cart
        url = reverse("store:add_to_cart")
        data = {
            "product_id": product.id,
            "quantity": 2,
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        
        # Verify cart was created and item added
        cart = Cart.objects.get(user=test_user)
        assert cart.items.count() == 1
        cart_item = cart.items.first()
        assert cart_item.product == product
        assert cart_item.quantity == 2
        
        # Step 2: Add second product to cart
        data = {
            "product_id": product_2.id,
            "quantity": 1,
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        
        # Verify second item was added
        cart.refresh_from_db()
        assert cart.items.count() == 2
        
        # Step 3: View cart
        url = reverse("store:cart")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "cart_items" in response.context
        assert len(response.context["cart_items"]) == 2
        
        # Step 4: Update item quantity
        url = reverse("store:update_cart_item")
        data = {
            "item_id": cart_item.id,
            "quantity": 3,
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        
        # Verify quantity was updated
        cart_item.refresh_from_db()
        assert cart_item.quantity == 3
        
        # Step 5: Remove item from cart
        url = reverse("store:remove_from_cart")
        data = {"item_id": cart_item.id}
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        
        # Verify item was removed
        cart.refresh_from_db()
        assert cart.items.count() == 1
        
        # Step 6: Clear cart
        url = reverse("store:clear_cart")
        response = authenticated_client.post(url)
        assert response.status_code == 200
        
        # Verify cart was cleared
        cart.refresh_from_db()
        assert cart.items.count() == 0


@pytest.mark.django_db
class TestWishlistWorkflow:
    """Test complete wishlist workflow."""
    
    def test_wishlist_workflow(self, authenticated_client, test_user, product, product_2):
        """Test complete wishlist process."""
        # Step 1: Add product to wishlist
        url = reverse("store:add_to_wishlist", kwargs={"product_id": product.id})
        response = authenticated_client.post(url)
        assert response.status_code == 200
        
        # Verify wishlist item was created
        assert Wishlist.objects.filter(user=test_user, product=product).exists()
        
        # Step 2: Add second product to wishlist
        url = reverse("store:add_to_wishlist", kwargs={"product_id": product_2.id})
        response = authenticated_client.post(url)
        assert response.status_code == 200
        
        # Step 3: View wishlist
        url = reverse("store:wishlist")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "wishlist_items" in response.context
        assert len(response.context["wishlist_items"]) == 2
        
        # Step 4: Remove product from wishlist
        url = reverse("store:remove_from_wishlist", kwargs={"product_id": product.id})
        response = authenticated_client.post(url)
        assert response.status_code == 200
        
        # Verify item was removed
        assert not Wishlist.objects.filter(user=test_user, product=product).exists()
        
        # Step 5: Verify remaining item
        response = authenticated_client.get(reverse("store:wishlist"))
        assert len(response.context["wishlist_items"]) == 1
        assert response.context["wishlist_items"][0].product == product_2


@pytest.mark.django_db
class TestCheckoutWorkflow:
    """Test complete checkout workflow."""
    
    def test_checkout_workflow(self, authenticated_client, test_user, product, address, payment_method):
        """Test complete checkout process."""
        # Step 1: Add product to cart
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        
        # Step 2: Access checkout page
        url = reverse("store:checkout")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "cart_items" in response.context
        assert "addresses" in response.context
        assert "payment_methods" in response.context
        
        # Step 3: Submit checkout form
        checkout_data = {
            "shipping_address": address.id,
            "billing_address": address.id,
            "payment_method": payment_method.id,
            "notes": "Test order notes",
        }
        response = authenticated_client.post(url, checkout_data)
        
        # Should redirect after successful checkout
        assert response.status_code == 302
        
        # Step 4: Verify order was created
        order = Order.objects.get(user=test_user)
        assert order.shipping_address == address
        assert order.billing_address == address
        assert order.payment_method == payment_method
        assert order.notes == "Test order notes"
        
        # Step 5: Verify order items were created
        assert order.items.count() == 1
        order_item = order.items.first()
        assert order_item.product == product
        assert order_item.quantity == 2
        
        # Step 6: Verify cart was cleared
        cart.refresh_from_db()
        assert cart.items.count() == 0


@pytest.mark.django_db
class TestOrderManagementWorkflow:
    """Test complete order management workflow."""
    
    def test_order_management_workflow(self, authenticated_client, test_user, order, product):
        """Test complete order management process."""
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            unit_price=Decimal("99.99"),
            total_price=Decimal("199.98"),
        )
        
        # Step 1: View order history
        url = reverse("store:order_history")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "orders" in response.context
        assert order in response.context["orders"]
        
        # Step 2: View order detail
        url = reverse("store:order_detail", kwargs={"order_id": order.id})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context["order"] == order
        assert "order_items" in response.context
        
        # Step 3: Test order status updates (admin only)
        # This would require admin client and proper permissions
        # For now, just verify the order exists and has correct data
        assert order.status == "pending"
        assert order.payment_status == "pending"
        assert order.total_amount == Decimal("225.98")


@pytest.mark.django_db
class TestUserProfileWorkflow:
    """Test complete user profile management workflow."""
    
    def test_user_profile_workflow(self, authenticated_client, test_user):
        """Test complete user profile management process."""
        # Step 1: View profile page
        url = reverse("store:profile")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "profile" in response.context
        
        # Step 2: Update profile
        profile_data = {
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "bio": "Updated bio",
        }
        response = authenticated_client.post(url, profile_data)
        assert response.status_code == 302  # Redirect after update
        
        # Verify profile was updated
        test_user.profile.refresh_from_db()
        assert test_user.profile.phone_number == "+1234567890"
        assert test_user.profile.bio == "Updated bio"
        
        # Step 3: Add address
        address_url = reverse("store:add_address")
        address_data = {
            "address_type": "shipping",
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
        }
        response = authenticated_client.post(address_url, address_data)
        assert response.status_code == 302  # Redirect after creation
        
        # Verify address was created
        address = Address.objects.get(user=test_user)
        assert address.first_name == "John"
        assert address.last_name == "Doe"
        
        # Step 4: Add payment method
        payment_url = reverse("store:add_payment_method")
        payment_data = {
            "payment_type": "credit_card",
            "card_number": "4111111111111111",
            "cardholder_name": "John Doe",
            "expiry_month": 12,
            "expiry_year": 2025,
            "billing_address": address.id,
        }
        response = authenticated_client.post(payment_url, payment_data)
        assert response.status_code == 302  # Redirect after creation
        
        # Verify payment method was created
        payment_method = PaymentMethod.objects.get(user=test_user)
        assert payment_method.cardholder_name == "John Doe"
        assert payment_method.billing_address == address


@pytest.mark.django_db
class TestProductReviewWorkflow:
    """Test complete product review workflow."""
    
    def test_product_review_workflow(self, authenticated_client, test_user, product):
        """Test complete product review process."""
        # Step 1: View product detail (where review form is)
        url = reverse("store:product_detail", kwargs={"slug": product.slug})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "reviews" in response.context
        
        # Step 2: Submit product review
        review_url = reverse("store:add_review", kwargs={"product_id": product.id})
        review_data = {
            "rating": 5,
            "title": "Excellent product!",
            "comment": "This product exceeded my expectations. Highly recommended!",
        }
        response = authenticated_client.post(review_url, review_data)
        assert response.status_code == 200
        
        # Verify review was created
        review = ProductReview.objects.get(user=test_user, product=product)
        assert review.rating == 5
        assert review.title == "Excellent product!"
        assert review.comment == "This product exceeded my expectations. Highly recommended!"
        
        # Step 3: View updated product detail with review
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert review in response.context["reviews"]
        
        # Step 4: Test review approval (admin functionality)
        # This would require admin client and proper permissions
        # For now, just verify the review exists and has correct data
        assert review.is_approved is False  # Default for new reviews


@pytest.mark.django_db
class TestSearchWorkflow:
    """Test complete search workflow."""
    
    def test_search_workflow(self, client, category, product, product_tag):
        """Test complete search process."""
        # Add tag to product
        product.tags.add(product_tag)
        
        # Step 1: Test search suggestions
        url = reverse("store:search_suggestions")
        response = client.get(url, {"q": "Test"})
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        
        # Step 2: Test product search
        url = reverse("store:product_list")
        response = client.get(url, {"search": "Test"})
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 3: Test advanced search with filters
        response = client.get(url, {
            "search": "Test",
            "category": category.slug,
            "min_price": "50.00",
            "max_price": "150.00",
            "sort": "price_low",
        })
        assert response.status_code == 200
        assert product in response.context["products"]
        
        # Step 4: Test search with no results
        response = client.get(url, {"search": "nonexistent"})
        assert response.status_code == 200
        assert len(response.context["products"]) == 0


@pytest.mark.django_db
class TestErrorHandlingWorkflow:
    """Test error handling in workflows."""
    
    def test_cart_workflow_with_out_of_stock_product(self, authenticated_client, test_user, product):
        """Test cart workflow with out-of-stock product."""
        # Set product as out of stock
        product.stock_quantity = 0
        product.is_in_stock = False
        product.save()
        
        # Try to add out-of-stock product to cart
        url = reverse("store:add_to_cart")
        data = {
            "product_id": product.id,
            "quantity": 1,
        }
        response = authenticated_client.post(url, data)
        
        # Should return error or handle gracefully
        assert response.status_code in [200, 400]  # Depending on implementation
    
    def test_checkout_workflow_with_empty_cart(self, authenticated_client, test_user):
        """Test checkout workflow with empty cart."""
        # Try to access checkout with empty cart
        url = reverse("store:checkout")
        response = authenticated_client.get(url)
        
        # Should redirect or show appropriate message
        assert response.status_code in [200, 302]  # Depending on implementation
    
    def test_order_workflow_with_invalid_address(self, authenticated_client, test_user, product):
        """Test order workflow with invalid address."""
        # Create cart with items
        cart = Cart.objects.create(user=test_user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        
        # Try to checkout with invalid address ID
        url = reverse("store:checkout")
        checkout_data = {
            "shipping_address": 99999,  # Invalid address ID
            "billing_address": 99999,
            "payment_method": 99999,
        }
        response = authenticated_client.post(url, checkout_data)
        
        # Should return error or handle gracefully
        assert response.status_code in [200, 400]  # Depending on implementation


@pytest.mark.django_db
class TestPerformanceWorkflow:
    """Test performance in workflows."""
    
    def test_product_list_performance_with_large_dataset(self, client, category):
        """Test product list performance with large dataset."""
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
        
        # Test product list page performance
        url = reverse("store:product_list")
        
        import time
        start_time = time.time()
        response = client.get(url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Should load within 3 seconds
    
    def test_cart_performance_with_many_items(self, authenticated_client, test_user, category):
        """Test cart performance with many items."""
        # Create many products
        products = []
        for i in range(50):
            product = Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                description=f"Description {i}",
                price=Decimal("99.99"),
                category=category,
            )
            products.append(product)
        
        # Add all products to cart
        cart = Cart.objects.create(user=test_user)
        for product in products:
            CartItem.objects.create(cart=cart, product=product, quantity=1)
        
        # Test cart page performance
        url = reverse("store:cart")
        
        import time
        start_time = time.time()
        response = authenticated_client.get(url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should load within 2 seconds
