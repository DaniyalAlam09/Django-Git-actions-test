"""
Admin configuration for the store application.

This module provides comprehensive admin interface configuration
for all store models with proper display, filtering, and search capabilities.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    ProductImage,
    ProductReview,
    ProductTag,
    UserProfile,
    Wishlist,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""

    list_display = [
        "name",
        "slug",
        "parent",
        "is_active",
        "product_count",
        "created_at",
    ]
    list_filter = ["is_active", "parent", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]
    list_per_page = 25

    def product_count(self, obj):
        """Display the number of products in this category."""
        count = obj.products.count()
        if count > 0:
            url = (
                reverse("admin:store_product_changelist")
                + f"?category__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"

    product_count.short_description = "Products"
    product_count.admin_order_field = "products__count"


class ProductImageInline(admin.TabularInline):
    """Inline admin for ProductImage model."""

    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "caption", "order", "is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    list_display = [
        "name",
        "category",
        "price",
        "sale_price",
        "stock_quantity",
        "is_in_stock",
        "is_active",
        "is_featured",
        "view_count",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_featured",
        "is_bestseller",
        "is_in_stock",
        "category",
        "created_at",
        "updated_at",
    ]
    search_fields = ["name", "description", "short_description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["view_count", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25
    list_editable = ["is_active", "is_featured"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "slug", "description", "short_description")},
        ),
        ("Pricing", {"fields": ("price", "sale_price")}),
        (
            "Inventory",
            {"fields": ("stock_quantity", "is_in_stock", "low_stock_threshold")},
        ),
        ("Categorization", {"fields": ("category", "tags")}),
        ("Media", {"fields": ("main_image",)}),
        ("Status", {"fields": ("is_active", "is_featured", "is_bestseller")}),
        (
            "SEO & Analytics",
            {
                "fields": ("meta_title", "meta_description", "view_count"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [ProductImageInline]

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("tags")
        )

    def save_model(self, request, obj, form, change):
        """Custom save logic for products."""
        if not change:  # New product
            obj.view_count = 0
        super().save_model(request, obj, form, change)

    def get_list_display(self, request):
        """Customize list display based on user permissions."""
        list_display = list(super().get_list_display(request))
        if not request.user.is_superuser:
            # Remove sensitive fields for non-superusers
            if "view_count" in list_display:
                list_display.remove("view_count")
        return list_display


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Admin configuration for ProductImage model."""

    list_display = [
        "product",
        "image_preview",
        "alt_text",
        "order",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["product__name", "alt_text", "caption"]
    list_editable = ["order", "is_active"]
    ordering = ["product", "order"]
    list_per_page = 25

    def image_preview(self, obj):
        """Display a thumbnail preview of the image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("product")


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    """Admin configuration for ProductTag model."""

    list_display = [
        "name",
        "slug",
        "color_preview",
        "product_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]
    ordering = ["name"]
    list_per_page = 25

    def color_preview(self, obj):
        """Display a color preview."""
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; border: 1px solid #ccc;"></div>',
            obj.color,
        )

    color_preview.short_description = "Color"

    def product_count(self, obj):
        """Display the number of products with this tag."""
        count = obj.products.count()
        if count > 0:
            url = (
                reverse("admin:store_product_changelist") + f"?tags__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"

    product_count.short_description = "Products"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Admin configuration for ProductReview model."""

    list_display = [
        "product",
        "user",
        "rating",
        "title",
        "is_verified_purchase",
        "is_approved",
        "created_at",
    ]
    list_filter = ["rating", "is_verified_purchase", "is_approved", "created_at"]
    search_fields = ["product__name", "user__username", "title", "comment"]
    list_editable = ["is_approved"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25

    fieldsets = (
        (
            "Review Information",
            {"fields": ("product", "user", "rating", "title", "comment")},
        ),
        ("Status", {"fields": ("is_verified_purchase", "is_approved")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("product", "user")

    def save_model(self, request, obj, form, change):
        """Custom save logic for reviews."""
        if obj.is_verified_purchase:
            obj.is_approved = True
        super().save_model(request, obj, form, change)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin configuration for Wishlist model."""

    list_display = ["user", "product", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["user__username", "product__name"]
    ordering = ["-added_at"]
    list_per_page = 25

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user", "product")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""

    list_display = ["user", "phone_number", "newsletter_subscription", "created_at"]
    list_filter = ["newsletter_subscription", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin configuration for Address model."""

    list_display = [
        "user",
        "first_name",
        "last_name",
        "city",
        "state",
        "address_type",
        "is_default",
        "created_at",
    ]
    list_filter = ["address_type", "is_default", "country", "created_at"]
    search_fields = [
        "user__username",
        "first_name",
        "last_name",
        "city",
        "state",
        "postal_code",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentMethod model."""

    list_display = [
        "user",
        "payment_type",
        "card_brand",
        "card_last_four",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = ["payment_type", "is_default", "is_active", "created_at"]
    search_fields = ["user__username", "card_brand", "card_last_four"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin configuration for Cart model."""

    list_display = [
        "user",
        "session_key",
        "item_count",
        "total_price",
        "created_at",
        "updated_at",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username", "session_key"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-updated_at"]
    list_per_page = 25

    def item_count(self, obj):
        """Display the number of items in the cart."""
        return obj.get_total_items()

    item_count.short_description = "Items"

    def total_price(self, obj):
        """Display the total price of the cart."""
        return obj.get_total_price_with_currency()

    total_price.short_description = "Total"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin configuration for CartItem model."""

    list_display = [
        "cart",
        "product",
        "quantity",
        "unit_price",
        "total_price",
        "added_at",
    ]
    list_filter = ["added_at", "updated_at"]
    search_fields = ["cart__user__username", "product__name"]
    readonly_fields = ["added_at", "updated_at"]
    ordering = ["-added_at"]
    list_per_page = 25

    def unit_price(self, obj):
        """Display the unit price."""
        return obj.product.get_display_price()

    unit_price.short_description = "Unit Price"

    def total_price(self, obj):
        """Display the total price for this item."""
        return obj.get_total_price_with_currency()

    total_price.short_description = "Total"


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem model."""

    model = OrderItem
    extra = 0
    readonly_fields = ["unit_price", "total_price"]
    fields = ["product", "quantity", "unit_price", "total_price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model."""

    list_display = [
        "order_number",
        "user",
        "status",
        "payment_status",
        "total_amount",
        "item_count",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "created_at", "updated_at"]
    search_fields = [
        "order_number",
        "user__username",
        "user__email",
        "shipping_address__first_name",
        "shipping_address__last_name",
        "tracking_number",
    ]
    readonly_fields = [
        "order_number",
        "created_at",
        "updated_at",
        "subtotal",
        "tax_amount",
        "shipping_amount",
        "discount_amount",
        "total_amount",
    ]
    ordering = ["-created_at"]
    list_per_page = 25
    list_editable = ["status", "payment_status"]

    fieldsets = (
        (
            "Order Information",
            {"fields": ("order_number", "user", "status", "payment_status")},
        ),
        (
            "Pricing",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "shipping_amount",
                    "discount_amount",
                    "total_amount",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Addresses",
            {
                "fields": ("shipping_address", "billing_address"),
                "classes": ("collapse",),
            },
        ),
        (
            "Payment",
            {
                "fields": ("payment_method", "payment_reference"),
                "classes": ("collapse",),
            },
        ),
        (
            "Tracking",
            {
                "fields": ("tracking_number", "estimated_delivery"),
                "classes": ("collapse",),
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [OrderItemInline]

    def item_count(self, obj):
        """Display the number of items in the order."""
        return obj.items.count()

    item_count.short_description = "Items"

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user", "shipping_address", "billing_address", "payment_method"
            )
            .prefetch_related("items__product")
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for OrderItem model."""

    list_display = ["order", "product", "quantity", "unit_price", "total_price"]
    list_filter = ["order__status", "order__created_at"]
    search_fields = ["order__order_number", "product__name", "order__user__username"]
    readonly_fields = ["unit_price", "total_price"]
    ordering = ["-order__created_at", "id"]
    list_per_page = 25

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("order", "product")


# Customize admin site
admin.site.site_header = "E-Commerce Store Administration"
admin.site.site_title = "E-Commerce Admin"
admin.site.index_title = "Welcome to E-Commerce Store Administration"

# Register models with custom admin classes
# (Already done above with decorators)
