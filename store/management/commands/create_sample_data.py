"""
Django management command to create sample data for testing.

This command creates sample categories, tags, and products for the e-commerce store.
"""

import random
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from store.models import (
    Address,
    Cart,
    CartItem,
    Category,
    PaymentMethod,
    Product,
    ProductReview,
    ProductTag,
    UserProfile,
    Wishlist,
)


class Command(BaseCommand):
    help = "Create sample data for the e-commerce store"

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")

        # Create categories
        categories_data = [
            {
                "name": "Electronics",
                "description": "Latest electronic devices and gadgets",
                "slug": "electronics",
            },
            {
                "name": "Clothing",
                "description": "Fashion and apparel for all seasons",
                "slug": "clothing",
            },
            {
                "name": "Home & Garden",
                "description": "Everything for your home and garden",
                "slug": "home-garden",
            },
            {
                "name": "Sports & Fitness",
                "description": "Sports equipment and fitness gear",
                "slug": "sports-fitness",
            },
            {
                "name": "Books",
                "description": "Books for all ages and interests",
                "slug": "books",
            },
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data["slug"], defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Create tags
        tags_data = [
            {"name": "New Arrival", "color": "#28a745"},
            {"name": "Best Seller", "color": "#dc3545"},
            {"name": "On Sale", "color": "#ffc107"},
            {"name": "Featured", "color": "#17a2b8"},
            {"name": "Limited Edition", "color": "#6f42c1"},
            {"name": "Eco Friendly", "color": "#20c997"},
            {"name": "Premium", "color": "#fd7e14"},
            {"name": "Budget", "color": "#6c757d"},
        ]

        tags = []
        for tag_data in tags_data:
            tag, created = ProductTag.objects.get_or_create(
                name=tag_data["name"], defaults=tag_data
            )
            tags.append(tag)
            if created:
                self.stdout.write(f"Created tag: {tag.name}")

        # Create products with realistic data and image URLs
        products_data = [
            {
                "name": "Sony WH-1000XM4 Wireless Headphones",
                "description": "Industry-leading noise canceling with Dual Noise Sensor technology. Next-generation music experience with 30-hour battery life and quick charge. Touch sensor controls to pause/play/skip tracks, control volume, activate your voice assistant, and answer phone calls.",
                "short_description": "Premium noise-canceling wireless headphones with 30-hour battery",
                "price": Decimal("349.99"),
                "sale_price": Decimal("279.99"),
                "stock_quantity": 25,
                "category": categories[0],  # Electronics
                "tags": [tags[0], tags[2], tags[3]],  # New Arrival, On Sale, Featured
                "is_featured": True,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop",
            },
            {
                "name": "Apple Watch Series 9",
                "description": "The most advanced Apple Watch yet. Features a powerful S9 chip, advanced health monitoring, crash detection, and emergency SOS. Water resistant to 50 meters. Available in multiple colors and band styles.",
                "short_description": "Most advanced Apple Watch with health monitoring and crash detection",
                "price": Decimal("399.99"),
                "sale_price": Decimal("349.99"),
                "stock_quantity": 18,
                "category": categories[0],  # Electronics
                "tags": [
                    tags[0],
                    tags[1],
                    tags[6],
                ],  # New Arrival, Best Seller, Premium
                "is_featured": True,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=500&h=500&fit=crop",
            },
            {
                "name": "Patagonia Organic Cotton T-Shirt",
                "description": "Made from 100% organic cotton, this t-shirt is soft, comfortable, and environmentally friendly. Features a classic fit and is available in multiple colors. Perfect for everyday wear and outdoor activities.",
                "short_description": "100% organic cotton t-shirt with classic fit",
                "price": Decimal("35.00"),
                "sale_price": Decimal("28.00"),
                "stock_quantity": 85,
                "category": categories[1],  # Clothing
                "tags": [tags[2], tags[5]],  # On Sale, Eco Friendly
                "is_featured": False,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop",
            },
            {
                "name": "Nike Air Zoom Pegasus 40",
                "description": "The perfect running shoe for daily training. Features responsive Zoom Air cushioning, breathable mesh upper, and durable rubber outsole. Designed for comfort and performance on every run.",
                "short_description": "Responsive running shoes with Zoom Air cushioning",
                "price": Decimal("120.00"),
                "stock_quantity": 42,
                "category": categories[3],  # Sports & Fitness
                "tags": [tags[1], tags[3]],  # Best Seller, Featured
                "is_featured": True,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
            },
            {
                "name": "Succulent Garden Starter Kit",
                "description": "Perfect for beginners! Includes 6 different succulent varieties, decorative ceramic pots, premium soil mix, and detailed care instructions. Create your own beautiful indoor garden.",
                "short_description": "Complete succulent starter kit with 6 plants",
                "price": Decimal("45.00"),
                "sale_price": Decimal("35.00"),
                "stock_quantity": 30,
                "category": categories[2],  # Home & Garden
                "tags": [tags[5], tags[0]],  # Eco Friendly, New Arrival
                "is_featured": False,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&h=500&fit=crop",
            },
            {
                "name": "Python Programming Complete Guide",
                "description": "Comprehensive guide to Python programming covering basics to advanced topics. Includes practical projects, coding exercises, and real-world applications. Perfect for beginners and intermediate developers.",
                "short_description": "Complete Python programming guide with projects",
                "price": Decimal("49.99"),
                "sale_price": Decimal("39.99"),
                "stock_quantity": 55,
                "category": categories[4],  # Books
                "tags": [tags[2], tags[6]],  # On Sale, Premium
                "is_featured": False,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop",
            },
            {
                "name": "Lululemon Reversible Yoga Mat",
                "description": "Premium non-slip yoga mat with reversible design. Features superior grip, cushioning, and durability. Includes carrying strap and is made from eco-friendly materials. Perfect for all yoga styles.",
                "short_description": "Premium reversible yoga mat with carrying strap",
                "price": Decimal("78.00"),
                "stock_quantity": 28,
                "category": categories[3],  # Sports & Fitness
                "tags": [tags[1], tags[5]],  # Best Seller, Eco Friendly
                "is_featured": False,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop",
            },
            {
                "name": "Amazon Echo Dot (5th Gen)",
                "description": "Smart speaker with Alexa. Play music, control smart home devices, make calls, and get information hands-free. Features improved audio and built-in hub for smart home devices.",
                "short_description": "Smart speaker with Alexa and smart home hub",
                "price": Decimal("49.99"),
                "sale_price": Decimal("39.99"),
                "stock_quantity": 35,
                "category": categories[0],  # Electronics
                "tags": [
                    tags[0],
                    tags[4],
                    tags[6],
                ],  # New Arrival, Limited Edition, Premium
                "is_featured": True,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop",
            },
            {
                "name": "Levi's 501 Original Jeans",
                "description": "The original blue jean. Classic straight fit with button fly and five-pocket styling. Made from 100% cotton denim with authentic vintage wash. Timeless style that never goes out of fashion.",
                "short_description": "Classic straight fit jeans with vintage wash",
                "price": Decimal("89.50"),
                "sale_price": Decimal("69.50"),
                "stock_quantity": 38,
                "category": categories[1],  # Clothing
                "tags": [tags[5], tags[3]],  # Eco Friendly, Featured
                "is_featured": True,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500&h=500&fit=crop",
            },
            {
                "name": "Fiskars Garden Tool Set",
                "description": "Professional-grade garden tools including hand trowel, cultivator, weeder, and pruning shears. Features ergonomic handles and rust-resistant steel blades. Perfect for serious gardeners.",
                "short_description": "Professional garden tools with ergonomic handles",
                "price": Decimal("65.00"),
                "stock_quantity": 22,
                "category": categories[2],  # Home & Garden
                "tags": [tags[7], tags[1]],  # Budget, Best Seller
                "is_featured": False,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&h=500&fit=crop",
            },
            {
                "name": "MacBook Air M2",
                "description": "Supercharged by the M2 chip, MacBook Air delivers exceptional performance and efficiency. Features a stunning 13.6-inch Liquid Retina display, all-day battery life, and advanced camera and audio.",
                "short_description": "MacBook Air with M2 chip and 13.6-inch display",
                "price": Decimal("1199.00"),
                "sale_price": Decimal("1099.00"),
                "stock_quantity": 12,
                "category": categories[0],  # Electronics
                "tags": [
                    tags[0],
                    tags[6],
                    tags[4],
                ],  # New Arrival, Premium, Limited Edition
                "is_featured": True,
                "is_bestseller": True,
                "main_image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&h=500&fit=crop",
            },
            {
                "name": "Dyson V15 Detect Cordless Vacuum",
                "description": "Advanced cordless vacuum with laser dust detection and powerful suction. Features intelligent suction adjustment, advanced filtration, and up to 60 minutes of runtime. Perfect for deep cleaning.",
                "short_description": "Cordless vacuum with laser dust detection",
                "price": Decimal("649.99"),
                "sale_price": Decimal("599.99"),
                "stock_quantity": 8,
                "category": categories[2],  # Home & Garden
                "tags": [tags[0], tags[6], tags[3]],  # New Arrival, Premium, Featured
                "is_featured": True,
                "is_bestseller": False,
                "main_image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop",
            },
        ]

        products = []
        for product_data in products_data:
            tags_list = product_data.pop("tags")
            image_url = product_data.pop("main_image_url", None)

            product, created = Product.objects.get_or_create(
                name=product_data["name"], defaults=product_data
            )
            if created:
                product.tags.set(tags_list)

                # Set a placeholder image URL for now (in production, you'd download and save the actual image)
                if image_url:
                    # For demo purposes, we'll store the URL in a text field
                    # In production, you'd download the image and save it to the ImageField
                    product.main_image = None  # We'll handle this differently

                products.append(product)
                self.stdout.write(f"Created product: {product.name}")

        # Create test users
        users_data = [
            {
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            },
            {
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
            {
                "username": "jane_smith",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
            },
        ]

        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
                users.append(user)
                self.stdout.write(
                    f"Created user: {user.username} (password: testpass123)"
                )
            else:
                users.append(user)

        # Create user profiles, addresses, and payment methods
        self.create_user_data(users)

        # Add some products to wishlist for test users
        if products and users:
            for user in users[:2]:  # Add to first 2 users
                for product in random.sample(products, 3):
                    Wishlist.objects.get_or_create(user=user, product=product)
                self.stdout.write(f"Added products to {user.username} wishlist")

        # Create some sample reviews
        if products and users:
            test_user = users[0]  # Use first user
            review_data = [
                {
                    "product": products[0],  # Wireless Headphones
                    "user": test_user,
                    "rating": 5,
                    "title": "Excellent sound quality!",
                    "comment": "These headphones are amazing! The sound quality is crystal clear and the noise cancellation works perfectly. Battery life is as advertised. Highly recommended!",
                    "is_verified_purchase": True,
                },
                {
                    "product": products[1],  # Fitness Watch
                    "user": test_user,
                    "rating": 4,
                    "title": "Great fitness tracker",
                    "comment": "Love the GPS feature and heart rate monitoring. The battery lasts about 5 days with regular use. The only downside is the app could be better.",
                    "is_verified_purchase": True,
                },
                {
                    "product": products[2],  # Organic T-Shirt
                    "user": test_user,
                    "rating": 5,
                    "title": "Very comfortable",
                    "comment": "Super soft and comfortable. Love that it's organic cotton. The fit is perfect and the quality is excellent for the price.",
                    "is_verified_purchase": True,
                },
            ]

            for review_info in review_data:
                review, created = ProductReview.objects.get_or_create(
                    product=review_info["product"],
                    user=review_info["user"],
                    defaults=review_info,
                )
                if created:
                    self.stdout.write(f"Created review for {review.product.name}")

        self.stdout.write(self.style.SUCCESS("Successfully created sample data!"))
        self.stdout.write("You can now:")
        self.stdout.write("1. Visit the admin panel at /admin/ (username: admin)")
        self.stdout.write(
            "2. Login as test user (username: testuser, password: testpass123)"
        )
        self.stdout.write("3. Browse products and test the wishlist functionality")
        self.stdout.write("4. Test the shopping cart and checkout functionality")

    def create_user_data(self, users):
        """Create user profiles, addresses, and payment methods."""
        for user in users:
            # Create user profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "phone_number": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "bio": f"Hi, I'm {user.first_name}! I love shopping for quality products.",
                    "newsletter_subscription": random.choice([True, False]),
                },
            )
            if created:
                self.stdout.write(f"Created profile for {user.username}")

            # Create addresses
            address_data = [
                {
                    "address_type": "both",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "address_line_1": f"{random.randint(100, 9999)} Main St",
                    "city": random.choice(
                        ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
                    ),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "country": "United States",
                    "phone_number": profile.phone_number,
                    "is_default": True,
                },
                {
                    "address_type": "shipping",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "address_line_1": f"{random.randint(100, 9999)} Oak Ave",
                    "city": random.choice(
                        ["Boston", "Seattle", "Denver", "Miami", "Atlanta"]
                    ),
                    "state": random.choice(["MA", "WA", "CO", "FL", "GA"]),
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "country": "United States",
                    "phone_number": profile.phone_number,
                    "is_default": False,
                },
            ]

            for addr_data in address_data:
                address, created = Address.objects.get_or_create(
                    user=user,
                    address_line_1=addr_data["address_line_1"],
                    city=addr_data["city"],
                    defaults=addr_data,
                )
                if created:
                    self.stdout.write(f"Created address for {user.username}")

            # Create payment methods
            payment_methods_data = [
                {
                    "payment_type": "credit_card",
                    "card_brand": "Visa",
                    "card_last_four": f"{random.randint(1000, 9999)}",
                    "expiry_month": f"{random.randint(1, 12):02d}",
                    "expiry_year": f"{random.randint(2025, 2030)}",
                    "is_default": True,
                },
                {
                    "payment_type": "credit_card",
                    "card_brand": "MasterCard",
                    "card_last_four": f"{random.randint(1000, 9999)}",
                    "expiry_month": f"{random.randint(1, 12):02d}",
                    "expiry_year": f"{random.randint(2025, 2030)}",
                    "is_default": False,
                },
            ]

            for pm_data in payment_methods_data:
                payment_method, created = PaymentMethod.objects.get_or_create(
                    user=user,
                    card_last_four=pm_data["card_last_four"],
                    defaults=pm_data,
                )
                if created:
                    self.stdout.write(f"Created payment method for {user.username}")

            # Create cart for user
            cart, created = Cart.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f"Created cart for {user.username}")
