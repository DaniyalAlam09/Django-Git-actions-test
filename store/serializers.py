"""
Serializers for the store application.

This module provides Django REST Framework serializers for all store models,
enabling JSON API responses with proper field mapping and validation.
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductReview, ProductTag, Wishlist


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.

    Provides user information for reviews and wishlist items
    with appropriate field exposure.
    """

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]
        read_only_fields = ["id", "email"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.

    Provides category information including:
    - Basic category details
    - Product count
    - Parent category information
    """

    product_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "parent_name",
            "is_active",
            "created_at",
            "updated_at",
            "product_count",
            "url",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_product_count(self, obj):
        """Get the number of active products in this category."""
        if hasattr(obj, "product_count"):
            return obj.product_count
        return obj.products.filter(is_active=True).count()

    def get_url(self, obj):
        """Get the category detail URL."""
        return obj.get_absolute_url()


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductTag model.

    Provides tag information including:
    - Basic tag details
    - Product count
    - Color information
    """

    product_count = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductTag
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "color",
            "is_active",
            "created_at",
            "product_count",
            "url",
        ]
        read_only_fields = ["id", "slug", "created_at"]

    def get_product_count(self, obj):
        """Get the number of active products with this tag."""
        if hasattr(obj, "product_count"):
            return obj.product_count
        return obj.products.filter(is_active=True).count()

    def get_url(self, obj):
        """Get the tag detail URL."""
        return obj.get_absolute_url()


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.

    Provides product image information including:
    - Image file
    - Alt text and caption
    - Display order
    """

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "image_url",
            "alt_text",
            "caption",
            "order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_image_url(self, obj):
        """Get the full URL for the image."""
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model (list view).

    Provides essential product information for listings including:
    - Basic product details
    - Category and tags
    - Pricing information
    - Stock status
    """

    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    display_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "price",
            "sale_price",
            "display_price",
            "is_on_sale",
            "discount_percentage",
            "stock_quantity",
            "is_in_stock",
            "is_low_stock",
            "category",
            "tags",
            "main_image",
            "main_image_url",
            "is_featured",
            "is_bestseller",
            "view_count",
            "created_at",
            "updated_at",
            "url",
        ]
        read_only_fields = ["id", "slug", "view_count", "created_at", "updated_at"]

    def get_main_image_url(self, obj):
        """Get the full URL for the main product image."""
        if obj.main_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_display_price(self, obj):
        """Get the current display price (sale price if available)."""
        return obj.get_display_price()

    def get_is_on_sale(self, obj):
        """Check if the product is currently on sale."""
        return obj.is_on_sale

    def get_discount_percentage(self, obj):
        """Get the discount percentage if product is on sale."""
        return obj.get_discount_percentage()

    def get_url(self, obj):
        """Get the product detail URL."""
        return obj.get_absolute_url()


class ProductDetailSerializer(ProductSerializer):
    """
    Serializer for Product model (detail view).

    Extends the basic product serializer with additional information:
    - Full description
    - Additional images
    - Review statistics
    - SEO metadata
    """

    additional_images = ProductImageSerializer(many=True, read_only=True)
    review_stats = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + [
            "description",
            "additional_images",
            "review_stats",
            "meta_title",
            "meta_description",
            "low_stock_threshold",
        ]

    def get_review_stats(self, obj):
        """Get review statistics for the product."""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return {
                "total_reviews": reviews.count(),
                "average_rating": round(
                    reviews.aggregate(avg_rating=serializers.Avg("rating"))[
                        "avg_rating"
                    ],
                    1,
                ),
                "rating_distribution": reviews.values("rating")
                .annotate(count=serializers.Count("id"))
                .order_by("rating"),
            }
        return None


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductReview model.

    Provides review information including:
    - Review content and rating
    - User information
    - Approval status
    """

    user = UserSerializer(read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    rating_display = serializers.CharField(source="rating_display", read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",
            "product_name",
            "user",
            "rating",
            "rating_display",
            "title",
            "comment",
            "is_verified_purchase",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "product",
            "is_verified_purchase",
            "is_approved",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):
        """Validate rating value."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_title(self, value):
        """Validate review title length."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Review title must be at least 5 characters long."
            )
        return value.strip()

    def validate_comment(self, value):
        """Validate review comment length."""
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Review comment must be at least 20 characters long."
            )
        return value.strip()


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for Wishlist model.

    Provides wishlist information including:
    - Product details
    - User information
    - Addition date
    """

    product = ProductSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "user", "product", "product_id", "added_at"]
        read_only_fields = ["id", "user", "added_at"]


class ProductSearchSerializer(serializers.Serializer):
    """
    Serializer for product search functionality.

    Provides search parameters and results including:
    - Search query
    - Filter options
    - Sorting preferences
    """

    query = serializers.CharField(max_length=100, required=False)
    category = serializers.CharField(max_length=100, required=False)
    tag = serializers.CharField(max_length=100, required=False)
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    max_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    in_stock = serializers.BooleanField(required=False)
    sort_by = serializers.CharField(max_length=50, required=False)

    def validate(self, data):
        """Validate search parameters."""
        min_price = data.get("min_price")
        max_price = data.get("max_price")

        if min_price and max_price and min_price > max_price:
            raise serializers.ValidationError(
                "Minimum price cannot be greater than maximum price."
            )

        return data


class CategoryDetailSerializer(CategorySerializer):
    """
    Serializer for Category model (detail view).

    Extends the basic category serializer with additional information:
    - Subcategories
    - Featured products
    - Category statistics
    """

    subcategories = CategorySerializer(many=True, read_only=True)
    featured_products = ProductSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ["subcategories", "featured_products"]


class TagDetailSerializer(TagSerializer):
    """
    Serializer for ProductTag model (detail view).

    Extends the basic tag serializer with additional information:
    - Related tags
    - Popular products
    - Tag statistics
    """

    related_tags = TagSerializer(many=True, read_only=True)
    popular_products = ProductSerializer(many=True, read_only=True)

    class Meta(TagSerializer.Meta):
        fields = TagSerializer.Meta.fields + ["related_tags", "popular_products"]


class ProductStatsSerializer(serializers.Serializer):
    """
    Serializer for product statistics.

    Provides aggregated product statistics including:
    - Total counts
    - Price statistics
    - Category distribution
    """

    total_products = serializers.IntegerField()
    in_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    price_statistics = serializers.DictField()
    category_distribution = serializers.ListField()
    featured_products = serializers.IntegerField()
    bestseller_products = serializers.IntegerField()


class CategoryStatsSerializer(serializers.Serializer):
    """
    Serializer for category statistics.

    Provides aggregated category statistics including:
    - Category counts
    - Product distribution
    - Performance metrics
    """

    total_categories = serializers.IntegerField()
    categories_with_products = serializers.IntegerField()
    top_categories = serializers.ListField()


class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer for health check responses.

    Provides system health information including:
    - Status information
    - Database connectivity
    - Model counts
    """

    status = serializers.CharField()
    database = serializers.CharField()
    models = serializers.DictField(required=False)
    error = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField()


class SearchSuggestionSerializer(serializers.Serializer):
    """
    Serializer for search suggestions.

    Provides search suggestion information including:
    - Suggestion type
    - Name and URL
    - Category information
    """

    type = serializers.CharField()
    name = serializers.CharField()
    url = serializers.CharField()
    category = serializers.CharField()
