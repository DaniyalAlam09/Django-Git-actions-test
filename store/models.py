"""
Store models for the e-commerce application.

This module contains the Product model and related database structures
following Django best practices and MVT architecture.
"""

import os

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """
    Product category model for organizing products.

    This model provides a hierarchical structure for organizing products
    and improving user navigation and search functionality.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    """
    Product model for the e-commerce store.

    This model represents individual products with comprehensive information
    including pricing, description, images, and inventory management.
    """

    # Basic Information
    name = models.CharField(
        max_length=200, help_text="Product name (max 200 characters)"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="URL-friendly product identifier",
    )
    description = models.TextField(help_text="Detailed product description")
    short_description = models.CharField(
        max_length=500, blank=True, help_text="Brief product summary"
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Product price (minimum $0.01)",
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)],
        help_text="Sale price (optional)",
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        default=0, help_text="Available stock quantity"
    )
    is_in_stock = models.BooleanField(
        default=True, help_text="Product availability status"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5, help_text="Stock level to trigger low stock alerts"
    )

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="Product category",
    )
    tags = models.ManyToManyField("ProductTag", blank=True, related_name="products")

    # Media
    main_image = models.ImageField(
        upload_to="products/main/", help_text="Primary product image"
    )

    # Status and Metadata
    is_active = models.BooleanField(default=True, help_text="Product visibility status")
    is_featured = models.BooleanField(
        default=False, help_text="Featured product status"
    )
    is_bestseller = models.BooleanField(
        default=False, help_text="Bestseller product status"
    )

    # SEO and Analytics
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO meta title")
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="SEO meta description"
    )
    view_count = models.PositiveIntegerField(
        default=0, help_text="Product view counter"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Update stock status based on quantity
        if self.stock_quantity <= 0:
            self.is_in_stock = False
        elif self.stock_quantity > 0 and not self.is_in_stock:
            self.is_in_stock = True

        # Auto-generate meta fields if not provided
        if not self.meta_title:
            self.meta_title = self.name[:60]
        if not self.meta_description:
            self.meta_description = (
                self.short_description[:160]
                if self.short_description
                else self.description[:160]
            )

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the canonical URL for the product."""
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    def get_display_price(self):
        """Return the current display price (sale price if available, otherwise regular price)."""
        return self.sale_price if self.sale_price else self.price

    def is_on_sale(self):
        """Check if the product is currently on sale."""
        return bool(self.sale_price and self.sale_price < self.price)

    def get_discount_percentage(self):
        """Calculate discount percentage if product is on sale."""
        if self.is_on_sale():
            discount = ((self.price - self.sale_price) / self.price) * 100
            return round(discount, 1)
        return 0

    def increment_view_count(self):
        """Increment the product view counter."""
        self.view_count += 1
        self.save(update_fields=["view_count"])

    @property
    def is_low_stock(self):
        """Check if product stock is below threshold."""
        return self.stock_quantity <= self.low_stock_threshold


class ProductImage(models.Model):
    """
    Additional product images model.

    This model allows multiple images per product for galleries
    and detailed product views.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="additional_images"
    )
    image = models.ImageField(upload_to="products/additional/")
    alt_text = models.CharField(
        max_length=200, blank=True, help_text="Image alt text for accessibility"
    )
    caption = models.CharField(max_length=200, blank=True, help_text="Image caption")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"{self.product.name} - {self.caption or 'Product image'}"
        super().save(*args, **kwargs)


class ProductTag(models.Model):
    """
    Product tags for categorization and search.

    Tags provide flexible categorization and improve product discoverability
    through search and filtering functionality.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Tag color in hex format"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Product Tag"
        verbose_name_plural = "Product Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:tag_detail", kwargs={"slug": self.slug})


class ProductReview(models.Model):
    """
    Product review and rating model.

    This model allows customers to leave reviews and ratings,
    building trust and helping other customers make informed decisions.
    """

    RATING_CHOICES = [
        (1, "1 - Poor"),
        (2, "2 - Fair"),
        (3, "3 - Good"),
        (4, "4 - Very Good"),
        (5, "5 - Excellent"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="product_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, help_text="Review title")
    comment = models.TextField(help_text="Review comment")
    is_verified_purchase = models.BooleanField(
        default=False, help_text="Verified purchase status"
    )
    is_approved = models.BooleanField(default=True, help_text="Review approval status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["product", "user"]  # One review per user per product
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.user.username}'s review of {self.product.name}"

    def save(self, *args, **kwargs):
        # Auto-approve reviews for verified purchases
        if self.is_verified_purchase:
            self.is_approved = True
        super().save(*args, **kwargs)

    @property
    def rating_display(self):
        """Return the rating as a human-readable string."""
        return dict(self.RATING_CHOICES)[self.rating]


class Wishlist(models.Model):
    """
    User wishlist model.

    This model allows users to save products they're interested in
    for future reference and purchase.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]
        ordering = ["-added_at"]
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    def get_absolute_url(self):
        return self.product.get_absolute_url()


class UserProfile(models.Model):
    """
    Extended user profile model.

    This model provides additional user information beyond Django's default User model.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    newsletter_subscription = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Address(models.Model):
    """
    User address model for shipping and billing.

    This model stores multiple addresses per user for flexible shipping options.
    """

    ADDRESS_TYPES = [
        ("shipping", "Shipping Address"),
        ("billing", "Billing Address"),
        ("both", "Both Shipping and Billing"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(
        max_length=10, choices=ADDRESS_TYPES, default="shipping"
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company = models.CharField(max_length=100, blank=True)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default="United States")
    phone_number = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}, {self.state}"

    def get_full_address(self):
        """Return formatted full address."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country,
        ]
        return ", ".join(filter(None, address_parts))


class PaymentMethod(models.Model):
    """
    User payment method model.

    This model stores encrypted payment information for repeat purchases.
    """

    PAYMENT_TYPES = [
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("paypal", "PayPal"),
        ("bank_transfer", "Bank Transfer"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payment_methods"
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    expiry_month = models.CharField(max_length=2, blank=True)
    expiry_year = models.CharField(max_length=4, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        if self.payment_type in ["credit_card", "debit_card"]:
            return f"{self.card_brand} ****{self.card_last_four}"
        return self.get_payment_type_display()


class Cart(models.Model):
    """
    Shopping cart model.

    This model represents a user's shopping cart with session-based and user-based carts.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="carts"
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"
        ordering = ["-updated_at"]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart for session {self.session_key}"

    def get_total_items(self):
        """Return total number of items in cart."""
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """Return total price of all items in cart."""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_price_with_currency(self):
        """Return total price with currency symbol."""
        total = self.get_total_price()
        return f"${total:.2f}"


class CartItem(models.Model):
    """
    Shopping cart item model.

    This model represents individual items in a shopping cart.
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ["cart", "product"]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    def get_total_price(self):
        """Return total price for this cart item."""
        return self.product.get_display_price() * self.quantity

    def get_total_price_with_currency(self):
        """Return total price with currency symbol."""
        total = self.get_total_price()
        return f"${total:.2f}"


class Order(models.Model):
    """
    Order model for completed purchases.

    This model represents a completed order with all necessary information.
    """

    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Addresses
    shipping_address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="shipping_orders"
    )
    billing_address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="billing_orders"
    )

    # Payment
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.PROTECT, null=True, blank=True
    )
    payment_reference = models.CharField(max_length=100, blank=True)

    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"

    def get_absolute_url(self):
        """Return the URL for this order's detail view."""
        from django.urls import reverse

        return reverse("store:order_detail", kwargs={"pk": self.pk})

    def get_total_with_currency(self):
        """Return total amount with currency symbol."""
        return f"${self.total_amount:.2f}"

    def get_status_display_class(self):
        """Return CSS class for status display."""
        status_classes = {
            "pending": "warning",
            "processing": "info",
            "shipped": "primary",
            "delivered": "success",
            "cancelled": "danger",
            "refunded": "secondary",
        }
        return status_classes.get(self.status, "secondary")


class OrderItem(models.Model):
    """
    Order item model for individual products in an order.

    This model represents individual products within a completed order.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.quantity}x {self.product.name} in Order {self.order.order_number}"
        )

    def get_total_with_currency(self):
        """Return total price with currency symbol."""
        return f"${self.total_price:.2f}"

    def get_unit_price_with_currency(self):
        """Return unit price with currency symbol."""
        return f"${self.unit_price:.2f}"
