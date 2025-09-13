"""
End-to-end tests for critical user journeys.

This module tests complete user journeys using Selenium WebDriver
to simulate real user interactions with the application.
"""

import pytest
import time
from decimal import Decimal

# Optional Selenium imports - tests will be skipped if not available
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from store.models import Product, Category, Cart, CartItem, Order, User


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestNewUserJourney:
    """Test complete journey for a new user."""
    
    def test_new_user_complete_journey(self, selenium_driver, live_server_url, category, product):
        """Test complete journey from registration to order completion."""
        driver = selenium_driver
        driver.get(f"{live_server_url}/")
        
        # Step 1: Navigate to registration
        driver.find_element(By.LINK_TEXT, "Sign Up").click()
        
        # Fill registration form
        driver.find_element(By.NAME, "username").send_keys("newuser")
        driver.find_element(By.NAME, "email").send_keys("newuser@example.com")
        driver.find_element(By.NAME, "password1").send_keys("newpass123")
        driver.find_element(By.NAME, "password2").send_keys("newpass123")
        driver.find_element(By.NAME, "first_name").send_keys("New")
        driver.find_element(By.NAME, "last_name").send_keys("User")
        
        # Submit registration
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for redirect and verify login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user-menu"))
        )
        
        # Step 2: Browse products
        driver.find_element(By.LINK_TEXT, "Products").click()
        
        # Wait for products to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
        )
        
        # Step 3: View product detail
        product_link = driver.find_element(By.PARTIAL_LINK_TEXT, product.name)
        product_link.click()
        
        # Wait for product detail page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-detail"))
        )
        
        # Step 4: Add product to cart
        quantity_input = driver.find_element(By.NAME, "quantity")
        quantity_input.clear()
        quantity_input.send_keys("2")
        
        add_to_cart_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='add-to-cart']")
        add_to_cart_btn.click()
        
        # Wait for cart update
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-success-message"))
        )
        
        # Step 5: View cart
        driver.find_element(By.CLASS_NAME, "cart-icon").click()
        
        # Wait for cart page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-items"))
        )
        
        # Verify cart contents
        cart_items = driver.find_elements(By.CLASS_NAME, "cart-item")
        assert len(cart_items) == 1
        
        # Step 6: Proceed to checkout
        checkout_btn = driver.find_element(By.LINK_TEXT, "Proceed to Checkout")
        checkout_btn.click()
        
        # Wait for checkout page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "checkout-form"))
        )
        
        # Step 7: Fill checkout form
        # Add shipping address
        driver.find_element(By.NAME, "shipping_first_name").send_keys("John")
        driver.find_element(By.NAME, "shipping_last_name").send_keys("Doe")
        driver.find_element(By.NAME, "shipping_address_line_1").send_keys("123 Main St")
        driver.find_element(By.NAME, "shipping_city").send_keys("Test City")
        driver.find_element(By.NAME, "shipping_state").send_keys("TS")
        driver.find_element(By.NAME, "shipping_postal_code").send_keys("12345")
        driver.find_element(By.NAME, "shipping_country").send_keys("US")
        
        # Add billing address (same as shipping)
        driver.find_element(By.ID, "same-as-shipping").click()
        
        # Add payment method
        driver.find_element(By.NAME, "card_number").send_keys("4111111111111111")
        driver.find_element(By.NAME, "cardholder_name").send_keys("John Doe")
        driver.find_element(By.NAME, "expiry_month").send_keys("12")
        driver.find_element(By.NAME, "expiry_year").send_keys("2025")
        driver.find_element(By.NAME, "cvv").send_keys("123")
        
        # Step 8: Submit order
        place_order_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        place_order_btn.click()
        
        # Wait for order confirmation
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "order-confirmation"))
        )
        
        # Verify order was created
        order_number = driver.find_element(By.CLASS_NAME, "order-number").text
        assert order_number.startswith("ORD-")
        
        # Verify order in database
        order = Order.objects.get(order_number=order_number)
        assert order.user.username == "newuser"
        assert order.items.count() == 1


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestReturningUserJourney:
    """Test complete journey for a returning user."""
    
    def test_returning_user_journey(self, selenium_driver, live_server_url, test_user, category, product):
        """Test complete journey for a logged-in user."""
        driver = selenium_driver
        driver.get(f"{live_server_url}/login/")
        
        # Step 1: Login
        driver.find_element(By.NAME, "username").send_keys(test_user.username)
        driver.find_element(By.NAME, "password").send_keys("testpass123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for login redirect
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user-menu"))
        )
        
        # Step 2: Search for products
        search_input = driver.find_element(By.NAME, "search")
        search_input.send_keys("Test")
        search_input.send_keys(Keys.RETURN)
        
        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
        )
        
        # Step 3: Add product to wishlist
        wishlist_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='add-to-wishlist']")
        wishlist_btn.click()
        
        # Wait for wishlist update
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "wishlist-success-message"))
        )
        
        # Step 4: View wishlist
        driver.find_element(By.LINK_TEXT, "Wishlist").click()
        
        # Wait for wishlist page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "wishlist-items"))
        )
        
        # Verify wishlist contents
        wishlist_items = driver.find_elements(By.CLASS_NAME, "wishlist-item")
        assert len(wishlist_items) == 1
        
        # Step 5: Add product to cart from wishlist
        add_to_cart_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='add-to-cart']")
        add_to_cart_btn.click()
        
        # Wait for cart update
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-success-message"))
        )
        
        # Step 6: View cart and update quantity
        driver.find_element(By.CLASS_NAME, "cart-icon").click()
        
        # Wait for cart page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-items"))
        )
        
        # Update quantity
        quantity_input = driver.find_element(By.CSS_SELECTOR, "input[data-action='update-quantity']")
        quantity_input.clear()
        quantity_input.send_keys("3")
        quantity_input.send_keys(Keys.RETURN)
        
        # Wait for quantity update
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-updated-message"))
        )
        
        # Step 7: Proceed to checkout
        checkout_btn = driver.find_element(By.LINK_TEXT, "Proceed to Checkout")
        checkout_btn.click()
        
        # Wait for checkout page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "checkout-form"))
        )
        
        # Step 8: Complete checkout (simplified for E2E)
        place_order_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        place_order_btn.click()
        
        # Wait for order confirmation
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "order-confirmation"))
        )


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestProductBrowsingJourney:
    """Test product browsing and filtering journey."""
    
    def test_product_browsing_journey(self, selenium_driver, live_server_url, category, product, product_tag):
        """Test complete product browsing and filtering journey."""
        driver = selenium_driver
        driver.get(f"{live_server_url}/products/")
        
        # Step 1: Test category filtering
        category_filter = driver.find_element(By.CSS_SELECTOR, f"a[href*='category={category.slug}']")
        category_filter.click()
        
        # Wait for filtered results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "filtered-products"))
        )
        
        # Step 2: Test price range filtering
        min_price_input = driver.find_element(By.NAME, "min_price")
        min_price_input.send_keys("50")
        
        max_price_input = driver.find_element(By.NAME, "max_price")
        max_price_input.send_keys("150")
        
        filter_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        filter_btn.click()
        
        # Wait for filtered results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "price-filtered-products"))
        )
        
        # Step 3: Test sorting
        sort_select = driver.find_element(By.NAME, "sort")
        sort_select.send_keys("price_low")
        
        # Wait for sorted results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sorted-products"))
        )
        
        # Step 4: Test search
        search_input = driver.find_element(By.NAME, "search")
        search_input.send_keys("Test")
        search_input.send_keys(Keys.RETURN)
        
        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
        )
        
        # Step 5: View product detail
        product_link = driver.find_element(By.PARTIAL_LINK_TEXT, product.name)
        product_link.click()
        
        # Wait for product detail page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-detail"))
        )
        
        # Step 6: Test product image gallery
        try:
            image_gallery = driver.find_element(By.CLASS_NAME, "product-images")
            assert image_gallery.is_displayed()
        except NoSuchElementException:
            # Image gallery might not be present
            pass
        
        # Step 7: Test product reviews section
        try:
            reviews_section = driver.find_element(By.CLASS_NAME, "product-reviews")
            assert reviews_section.is_displayed()
        except NoSuchElementException:
            # Reviews might not be present
            pass


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestMobileResponsiveJourney:
    """Test mobile responsive journey."""
    
    def test_mobile_responsive_journey(self, selenium_driver, live_server_url, category, product):
        """Test complete journey on mobile device."""
        driver = selenium_driver
        
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        driver.get(f"{live_server_url}/")
        
        # Step 1: Test mobile navigation
        try:
            mobile_menu_btn = driver.find_element(By.CLASS_NAME, "mobile-menu-toggle")
            mobile_menu_btn.click()
            
            # Wait for mobile menu
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mobile-menu"))
            )
        except NoSuchElementException:
            # Mobile menu might not be present
            pass
        
        # Step 2: Test mobile product browsing
        driver.get(f"{live_server_url}/products/")
        
        # Wait for products to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
        )
        
        # Step 3: Test mobile product detail
        product_link = driver.find_element(By.PARTIAL_LINK_TEXT, product.name)
        product_link.click()
        
        # Wait for product detail page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-detail"))
        )
        
        # Step 4: Test mobile cart functionality
        add_to_cart_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='add-to-cart']")
        add_to_cart_btn.click()
        
        # Wait for cart update
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-success-message"))
        )
        
        # Step 5: Test mobile cart view
        driver.find_element(By.CLASS_NAME, "cart-icon").click()
        
        # Wait for cart page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cart-items"))
        )


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestErrorHandlingJourney:
    """Test error handling in user journeys."""
    
    def test_error_handling_journey(self, selenium_driver, live_server_url, test_user, product):
        """Test error handling in various scenarios."""
        driver = selenium_driver
        driver.get(f"{live_server_url}/login/")
        
        # Step 1: Test invalid login
        driver.find_element(By.NAME, "username").send_keys("invaliduser")
        driver.find_element(By.NAME, "password").send_keys("wrongpassword")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for error message
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        # Step 2: Test valid login
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "username").send_keys(test_user.username)
        driver.find_element(By.NAME, "password").send_keys("testpass123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for successful login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user-menu"))
        )
        
        # Step 3: Test adding out-of-stock product to cart
        # Set product as out of stock
        product.stock_quantity = 0
        product.is_in_stock = False
        product.save()
        
        driver.get(f"{live_server_url}/product/{product.slug}/")
        
        # Wait for product detail page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-detail"))
        )
        
        # Try to add out-of-stock product
        add_to_cart_btn = driver.find_element(By.CSS_SELECTOR, "button[data-action='add-to-cart']")
        add_to_cart_btn.click()
        
        # Wait for error message
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        # Step 4: Test 404 page
        driver.get(f"{live_server_url}/product/non-existent-product/")
        
        # Wait for 404 page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-404"))
        )


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestPerformanceJourney:
    """Test performance in user journeys."""
    
    def test_performance_journey(self, selenium_driver, live_server_url, category):
        """Test performance with large dataset."""
        driver = selenium_driver
        
        # Create many products for performance testing
        products = []
        for i in range(50):
            product = Product.objects.create(
                name=f"Performance Test Product {i}",
                slug=f"performance-test-product-{i}",
                description=f"Description for performance test product {i}",
                price=Decimal("99.99"),
                category=category,
            )
            products.append(product)
        
        # Step 1: Test product list page performance
        start_time = time.time()
        driver.get(f"{live_server_url}/products/")
        
        # Wait for products to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
        )
        end_time = time.time()
        
        # Should load within 5 seconds
        assert (end_time - start_time) < 5.0
        
        # Step 2: Test search performance
        start_time = time.time()
        search_input = driver.find_element(By.NAME, "search")
        search_input.send_keys("Performance")
        search_input.send_keys(Keys.RETURN)
        
        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
        )
        end_time = time.time()
        
        # Should search within 3 seconds
        assert (end_time - start_time) < 3.0
        
        # Step 3: Test pagination performance
        try:
            next_page_btn = driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
            start_time = time.time()
            next_page_btn.click()
            
            # Wait for next page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
            )
            end_time = time.time()
            
            # Should load next page within 2 seconds
            assert (end_time - start_time) < 2.0
        except NoSuchElementException:
            # Pagination might not be present
            pass


@pytest.mark.e2e
@pytest.mark.django_db
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestAccessibilityJourney:
    """Test accessibility in user journeys."""
    
    def test_accessibility_journey(self, selenium_driver, live_server_url, category, product):
        """Test accessibility features in user journey."""
        driver = selenium_driver
        driver.get(f"{live_server_url}/")
        
        # Step 1: Test keyboard navigation
        # Tab through main navigation
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)
        
        # Step 2: Test form accessibility
        driver.get(f"{live_server_url}/login/")
        
        # Check for proper form labels
        username_label = driver.find_element(By.CSS_SELECTOR, "label[for='id_username']")
        assert username_label.is_displayed()
        
        password_label = driver.find_element(By.CSS_SELECTOR, "label[for='id_password']")
        assert password_label.is_displayed()
        
        # Step 3: Test image alt text
        driver.get(f"{live_server_url}/product/{product.slug}/")
        
        # Wait for product detail page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-detail"))
        )
        
        # Check for alt text on product images
        try:
            product_images = driver.find_elements(By.CSS_SELECTOR, "img[alt]")
            assert len(product_images) > 0
        except NoSuchElementException:
            # Images might not be present
            pass
        
        # Step 4: Test heading hierarchy
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        assert len(headings) > 0
        
        # Check for h1 tag
        h1_tags = driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1_tags) > 0
