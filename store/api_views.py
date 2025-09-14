"""
API views for the store application.

This module provides REST API endpoints using Django REST Framework
for frontend applications, mobile apps, and third-party integrations.
"""

import logging

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .forms import ProductSearchForm
from .models import (
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
    Wishlist,
)
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductSerializer,
    ReviewSerializer,
    TagSerializer,
    WishlistSerializer,
)

# Set up logging
logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API responses.

    Provides consistent pagination across all API endpoints
    with configurable page sizes.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListAPIView(generics.ListAPIView):
    """
    API endpoint for listing products with filtering and search.

    Supports:
    - Pagination
    - Search functionality
    - Category and tag filtering
    - Price range filtering
    - Sorting options
    """

    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = [
        "name",
        "description",
        "short_description",
        "category__name",
        "tags__name",
    ]
    ordering_fields = ["name", "price", "created_at", "view_count"]
    ordering = ["-created_at"]
    filterset_fields = [
        "category__slug",
        "tags__slug",
        "is_active",
        "is_featured",
        "is_bestseller",
        "is_in_stock",
    ]

    def get_queryset(self):
        """
        Build optimized queryset with filtering and search.

        Returns:
            QuerySet: Filtered and optimized product queryset
        """
        queryset = Product.objects.filter(is_active=True).select_related("category")

        # Apply custom filters
        category_slug = self.request.query_params.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        tag_slug = self.request.query_params.get("tag_slug")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Price filtering
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                logger.warning(f"Invalid min_price value: {min_price}")
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                logger.warning(f"Invalid max_price value: {max_price}")

        # Stock filtering
        in_stock = self.request.query_params.get("in_stock")
        if in_stock == "true":
            queryset = queryset.filter(is_in_stock=True)
        elif in_stock == "false":
            queryset = queryset.filter(is_in_stock=False)

        # Prefetch related data for performance
        queryset = queryset.prefetch_related("tags", "additional_images")

        return queryset


class ProductDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for detailed product information.

    Provides comprehensive product details including:
    - Basic product information
    - Category and tag details
    - Additional images
    - Review statistics
    """

    serializer_class = ProductDetailSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        """
        Get product with optimized queryset.

        Returns:
            QuerySet: Optimized product queryset
        """
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags", "additional_images", "reviews__user")
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve product and increment view count.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Serialized product data
        """
        product = self.get_object()

        # Increment view count
        try:
            product.increment_view_count()
        except Exception as e:
            logger.error(
                f"Failed to increment view count for product {product.id}: {e}"
            )

        serializer = self.get_serializer(product)
        return Response(serializer.data)


class CategoryListAPIView(generics.ListAPIView):
    """
    API endpoint for listing categories.

    Provides category information with product counts
    for navigation and filtering.
    """

    serializer_class = CategorySerializer
    pagination_class = None
    queryset = (
        Category.objects.filter(is_active=True)
        .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
        .filter(product_count__gt=0)
    )
    ordering = ["name"]


class CategoryDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for detailed category information.

    Provides category details including:
    - Category information
    - Subcategories
    - Product count
    """

    serializer_class = CategorySerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    queryset = Category.objects.filter(is_active=True)


class CategoryProductsAPIView(generics.ListAPIView):
    """
    API endpoint for products in a specific category.

    Provides paginated list of products within a category
    with filtering and sorting options.
    """

    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["name", "price", "created_at", "view_count"]
    ordering = ["-created_at"]
    filterset_fields = ["tags", "is_featured", "is_bestseller", "is_in_stock"]

    def get_queryset(self):
        """
        Get products in the specified category.

        Returns:
            QuerySet: Products in the category
        """
        category_slug = self.kwargs.get("slug")
        category = get_object_or_404(Category, slug=category_slug, is_active=True)

        return (
            Product.objects.filter(category=category, is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )


class TagListAPIView(generics.ListAPIView):
    """
    API endpoint for listing tags.

    Provides tag information with product counts
    for filtering and discovery.
    """

    serializer_class = TagSerializer
    queryset = (
        ProductTag.objects.filter(is_active=True)
        .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
        .filter(product_count__gt=0)
        .order_by("-product_count")
    )


class TagDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for detailed tag information.

    Provides tag details including:
    - Tag information
    - Related tags
    - Product count
    """

    serializer_class = TagSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    queryset = ProductTag.objects.filter(is_active=True)


class TagProductsAPIView(generics.ListAPIView):
    """
    API endpoint for products with a specific tag.

    Provides paginated list of products with a specific tag
    with filtering and sorting options.
    """

    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["name", "price", "created_at", "view_count"]
    ordering = ["-created_at"]
    filterset_fields = ["category", "is_featured", "is_bestseller", "is_in_stock"]

    def get_queryset(self):
        """
        Get products with the specified tag.

        Returns:
            QuerySet: Products with the tag
        """
        tag_slug = self.kwargs.get("slug")
        tag = get_object_or_404(ProductTag, slug=tag_slug, is_active=True)

        return (
            Product.objects.filter(tags=tag, is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )


class ProductSearchAPIView(generics.ListAPIView):
    """
    API endpoint for product search.

    Provides advanced search functionality with:
    - Full-text search
    - Multiple filter options
    - Sorting and pagination
    """

    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["name", "price", "created_at", "view_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Build search queryset based on query parameters.

        Returns:
            QuerySet: Filtered search results
        """
        queryset = Product.objects.filter(is_active=True).select_related("category")

        # Apply search query
        search_query = self.request.query_params.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(short_description__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        # Apply additional filters
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        tag_slug = self.request.query_params.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        # Prefetch related data
        queryset = queryset.prefetch_related("tags", "additional_images")

        return queryset


class SearchSuggestionsAPIView(generics.ListAPIView):
    """
    API endpoint for search suggestions.

    Provides autocomplete suggestions for:
    - Product names
    - Category names
    - Tag names
    """

    serializer_class = ProductSerializer

    def get_queryset(self):
        """
        Get search suggestions based on query.

        Returns:
            QuerySet: Search suggestions
        """
        query = self.request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Product.objects.none()

        return Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            is_active=True,
        ).select_related("category")[:5]


class ProductReviewsAPIView(generics.ListAPIView):
    """
    API endpoint for product reviews.

    Provides paginated list of reviews for a specific product
    with user information and ratings.
    """

    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Get reviews for the specified product.

        Returns:
            QuerySet: Product reviews
        """
        product_slug = self.kwargs.get("slug")
        product = get_object_or_404(Product, slug=product_slug, is_active=True)

        return (
            ProductReview.objects.filter(product=product, is_approved=True)
            .select_related("user")
            .order_by("-created_at")
        )


class ReviewCreateAPIView(generics.CreateAPIView):
    """
    API endpoint for creating product reviews.

    Allows authenticated users to submit reviews
    with proper validation and moderation.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Create review with user and product information.

        Args:
            serializer: Review serializer instance
        """
        product_slug = self.kwargs.get("slug")
        product = get_object_or_404(Product, slug=product_slug, is_active=True)

        serializer.save(user=self.request.user, product=product)


class WishlistAPIView(generics.ListAPIView):
    """
    API endpoint for user wishlist.

    Provides authenticated user's wishlist items
    with product details and management options.
    """

    serializer_class = WishlistSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get user's wishlist items.

        Returns:
            QuerySet: User's wishlist
        """
        return (
            Wishlist.objects.filter(user=self.request.user)
            .select_related("product", "product__category")
            .prefetch_related("product__tags")
        )


class AddToWishlistAPIView(generics.CreateAPIView):
    """
    API endpoint for adding products to wishlist.

    Allows authenticated users to add products
    to their personal wishlist.
    """

    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Add product to wishlist or return existing item.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Wishlist item data
        """
        product_id = request.data.get("product_id")
        
        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        product = get_object_or_404(Product, id=product_id, is_active=True)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )

        serializer = self.get_serializer(wishlist_item)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response({
            "status": "success",
            "message": "Item added to wishlist" if created else "Item already in wishlist",
            "wishlist_item": serializer.data
        }, status=status_code)


class RemoveFromWishlistAPIView(generics.GenericAPIView):
    """
    API endpoint for removing products from wishlist.

    Allows authenticated users to remove products
    from their personal wishlist.
    """

    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Remove product from wishlist.

        Args:
            request: HTTP request object with product_id

        Returns:
            Response: Success message
        """
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user, product_id=product_id
            )
            wishlist_item.delete()
            return Response({"status": "success", "message": "Item removed from wishlist successfully"})
        except Wishlist.DoesNotExist:
            return Response(
                {"error": "Wishlist item not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ProductStatsAPIView(generics.GenericAPIView):
    """
    API endpoint for product statistics.

    Provides aggregated statistics about products including:
    - Total product count
    - Category distribution
    - Price statistics
    - Stock information
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        """
        Get product statistics.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Product statistics
        """
        # Basic counts
        total_products = Product.objects.filter(is_active=True).count()
        in_stock_products = Product.objects.filter(
            is_active=True, is_in_stock=True
        ).count()
        out_of_stock_products = total_products - in_stock_products

        # Price statistics
        price_stats = Product.objects.filter(is_active=True).aggregate(
            avg_price=Avg("price"), min_price=Min("price"), max_price=Max("price")
        )

        # Category distribution
        category_stats = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
            .values("name", "product_count")
        )

        # Featured and bestseller counts
        featured_count = Product.objects.filter(
            is_active=True, is_featured=True
        ).count()
        bestseller_count = Product.objects.filter(
            is_active=True, is_bestseller=True
        ).count()

        stats = {
            "total_products": total_products,
            "in_stock_products": in_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "price_statistics": price_stats,
            "category_distribution": list(category_stats),
            "featured_products": featured_count,
            "bestseller_products": bestseller_count,
        }

        return Response(stats)


class CategoryStatsAPIView(generics.GenericAPIView):
    """
    API endpoint for category statistics.

    Provides aggregated statistics about categories including:
    - Category counts
    - Product distribution
    - Performance metrics
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        """
        Get category statistics.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Category statistics
        """
        # Category counts
        total_categories = Category.objects.filter(is_active=True).count()
        categories_with_products = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
            .count()
        )

        # Top categories by product count
        top_categories = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
            .order_by("-product_count")[:10]
        )

        # Category performance metrics
        category_performance = []
        for category in top_categories:
            avg_price = (
                category.products.filter(is_active=True).aggregate(
                    avg_price=Avg("price")
                )["avg_price"]
                or 0
            )

            category_performance.append(
                {
                    "name": category.name,
                    "slug": category.slug,
                    "product_count": category.product_count,
                    "average_price": float(avg_price),
                }
            )

        stats = {
            "total_categories": total_categories,
            "categories_with_products": categories_with_products,
            "top_categories": category_performance,
        }

        return Response(stats)


class HealthCheckAPIView(generics.GenericAPIView):
    """
    API endpoint for health check and monitoring.

    Provides system health information including:
    - Database connectivity
    - Model counts
    - System status
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        """
        Get system health information.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Health check information
        """
        try:
            # Check database connectivity
            product_count = Product.objects.count()
            category_count = Category.objects.count()
            user_count = User.objects.count()

            health_status = {
                "status": "healthy",
                "database": "connected",
                "models": {
                    "products": product_count,
                    "categories": category_count,
                    "users": user_count,
                },
                "timestamp": timezone.now().isoformat(),
            }

            return Response(health_status, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status = {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# Cart API Views
class CartAPIView(generics.RetrieveAPIView):
    """
    API endpoint for user's shopping cart.

    Provides authenticated user's cart items
    with product details and totals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get user's cart with items and totals.

        Returns:
            Response: Cart data with items and totals
        """
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related("product")

        items_data = []
        total_items = 0
        total_price = 0

        for item in cart_items:
            item_total = item.product.price * item.quantity
            items_data.append(
                {
                    "id": item.id,
                    "product": {
                        "id": item.product.id,
                        "name": item.product.name,
                        "slug": item.product.slug,
                        "price": float(item.product.price),
                        "image": item.product.main_image.url if item.product.main_image else None,
                        "is_in_stock": item.product.is_in_stock,
                        "stock_quantity": item.product.stock_quantity,
                    },
                    "quantity": item.quantity,
                    "total_price": float(item_total),
                }
            )
            total_items += item.quantity
            total_price += item_total

        cart_data = {
            "id": cart.id,
            "user": {
                "id": cart.user.id,
                "username": cart.user.username,
                "email": cart.user.email,
            },
            "items": items_data,
            "total_items": total_items,
            "total_price": f"{total_price:.2f}",
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
        }

        return Response(cart_data)


class AddToCartAPIView(generics.CreateAPIView):
    """
    API endpoint for adding products to cart.

    Allows authenticated users to add products
    to their shopping cart with quantity.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Add product to cart or update quantity.

        Args:
            request: HTTP request object with product_id and quantity

        Returns:
            Response: Cart item data
        """
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not product.is_in_stock:
            return Response(
                {"error": "Product is out of stock"}, status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > product.stock_quantity:
            return Response(
                {"error": f"Only {product.stock_quantity} items available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock_quantity:
                cart_item.quantity = product.stock_quantity
            cart_item.save()

        return Response(
            {
                "status": "success",
                "message": "Item added to cart",
                "cart_item": {
                    "id": cart_item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "total_price": float(cart_item.product.price * cart_item.quantity),
                },
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UpdateCartItemAPIView(generics.GenericAPIView):
    """
    API endpoint for updating cart item quantity.

    Allows authenticated users to update
    quantities of items in their cart.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Update cart item quantity.

        Args:
            request: HTTP request object with quantity

        Returns:
            Response: Updated cart item data
        """
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(
                cart__user=request.user, product_id=product_id
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if quantity <= 0:
            cart_item.delete()
            return Response({"message": "Item removed from cart", "deleted": True})

        if quantity > cart_item.product.stock_quantity:
            return Response(
                {"error": f"Only {cart_item.product.stock_quantity} items available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            {
                "status": "success",
                "message": "Cart item updated successfully",
                "cart_item": {
                    "id": cart_item.id,
                    "product_id": cart_item.product.id,
                    "product_name": cart_item.product.name,
                    "quantity": cart_item.quantity,
                    "total_price": float(cart_item.product.price * cart_item.quantity),
                },
            }
        )


class RemoveFromCartAPIView(generics.GenericAPIView):
    """
    API endpoint for removing items from cart.

    Allows authenticated users to remove
    specific items from their cart.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Remove item from cart.

        Args:
            request: HTTP request object

        Returns:
            Response: Success message
        """
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(
                cart__user=request.user, product_id=product_id
            )
            cart_item.delete()
            return Response({"status": "success", "message": "Item removed from cart successfully"})
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ClearCartAPIView(generics.GenericAPIView):
    """
    API endpoint for clearing entire cart.

    Allows authenticated users to remove
    all items from their cart.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Clear all items from cart.

        Args:
            request: HTTP request object

        Returns:
            Response: Success message
        """
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            return Response({"status": "success", "message": "Cart cleared successfully"})
        except Cart.DoesNotExist:
            return Response({"message": "Cart is already empty"})


class CartCountAPIView(generics.GenericAPIView):
    """
    API endpoint for getting cart item count.

    Provides quick access to cart item count
    for UI updates.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get cart item count.

        Returns:
            Response: Cart item count
        """
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.get_total_items()
            return Response({"count": count})
        except Cart.DoesNotExist:
            return Response({"count": 0})


# Order API Views
class OrderListAPIView(generics.ListCreateAPIView):
    """
    API endpoint for user's order history.

    Provides paginated list of user's orders
    with order details and status.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        Get user's orders.

        Returns:
            QuerySet: User's orders
        """
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("shipping_address", "billing_address", "payment_method")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        """
        List user's orders with detailed information.

        Returns:
            Response: List of orders with details
        """
        orders = self.get_queryset()
        page = self.paginate_queryset(orders)

        orders_data = []
        for order in page if page is not None else orders:
            order_items = []
            for item in order.items.all():
                order_items.append(
                    {
                        "id": item.id,
                        "product": {
                            "id": item.product.id,
                            "name": item.product.name,
                            "slug": item.product.slug,
                            "image": item.product.main_image.url
                            if item.product.main_image
                            else None,
                        },
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "total_price": float(item.total_price),
                    }
                )

            orders_data.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "subtotal": float(order.subtotal),
                    "tax_amount": float(order.tax_amount),
                    "shipping_amount": float(order.shipping_amount),
                    "discount_amount": float(order.discount_amount),
                    "total_amount": float(order.total_amount),
                    "shipping_address": {
                        "first_name": order.shipping_address.first_name,
                        "last_name": order.shipping_address.last_name,
                        "address_line_1": order.shipping_address.address_line_1,
                        "city": order.shipping_address.city,
                        "state": order.shipping_address.state,
                        "postal_code": order.shipping_address.postal_code,
                        "country": order.shipping_address.country,
                    }
                    if order.shipping_address
                    else None,
                    "payment_method": {
                        "payment_type": order.payment_method.payment_type,
                        "card_brand": order.payment_method.card_brand,
                        "card_last_four": order.payment_method.card_last_four,
                    }
                    if order.payment_method
                    else None,
                    "tracking_number": order.tracking_number,
                    "estimated_delivery": order.estimated_delivery,
                    "created_at": order.created_at,
                    "items": order_items,
                }
            )

        if page is not None:
            return self.get_paginated_response(orders_data)
        return Response(orders_data)

    def create(self, request, *args, **kwargs):
        """
        Create a new order.

        Args:
            request: HTTP request object with order data

        Returns:
            Response: Created order data
        """
        # Get required data from request
        shipping_address_id = request.data.get("shipping_address_id")
        billing_address_id = request.data.get("billing_address_id")
        payment_method_id = request.data.get("payment_method_id")
        notes = request.data.get("notes", "")

        if not all([shipping_address_id, billing_address_id, payment_method_id]):
            return Response(
                {"error": "shipping_address_id, billing_address_id, and payment_method_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get addresses and payment method
            shipping_address = Address.objects.get(id=shipping_address_id, user=request.user)
            billing_address = Address.objects.get(id=billing_address_id, user=request.user)
            payment_method = PaymentMethod.objects.get(id=payment_method_id, user=request.user)
        except (Address.DoesNotExist, PaymentMethod.DoesNotExist):
            return Response(
                {"error": "Invalid address or payment method"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate subtotal first
        subtotal = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
        
        # Create order with initial values
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment_method=payment_method,
            notes=notes,
            status="pending",
            payment_status="pending",
            subtotal=subtotal,
            tax_amount=0,
            shipping_amount=0,
            discount_amount=0,
            total_amount=subtotal
        )

        # Add cart items to order
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                total_price=cart_item.product.price * cart_item.quantity
            )

        # Save the order (totals are already calculated)
        order.save()

        # Clear cart
        cart.items.all().delete()

        return Response({
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "shipping_amount": float(order.shipping_amount),
            "discount_amount": float(order.discount_amount),
            "total_amount": str(order.total_amount),
            "notes": order.notes,
            "created_at": order.created_at
        }, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for detailed order information.

    Provides comprehensive order details including
    items, addresses, and payment information.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get detailed order information.

        Returns:
            Response: Detailed order data
        """
        order_id = kwargs.get("pk")

        try:
            order = (
                Order.objects.select_related(
                    "shipping_address", "billing_address", "payment_method"
                )
                .prefetch_related("items__product")
                .get(id=order_id, user=request.user)
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        order_items = []
        for item in order.items.all():
            order_items.append(
                {
                    "id": item.id,
                    "product": {
                        "id": item.product.id,
                        "name": item.product.name,
                        "slug": item.product.slug,
                        "image": item.product.main_image.url if item.product.main_image else None,
                        "current_price": float(item.product.price),
                    },
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                }
            )

        order_data = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "shipping_amount": float(order.shipping_amount),
            "discount_amount": float(order.discount_amount),
            "total_amount": str(order.total_amount),
            "shipping_address": {
                "first_name": order.shipping_address.first_name,
                "last_name": order.shipping_address.last_name,
                "company": order.shipping_address.company,
                "address_line_1": order.shipping_address.address_line_1,
                "address_line_2": order.shipping_address.address_line_2,
                "city": order.shipping_address.city,
                "state": order.shipping_address.state,
                "postal_code": order.shipping_address.postal_code,
                "country": order.shipping_address.country,
                "phone_number": order.shipping_address.phone_number,
            }
            if order.shipping_address
            else None,
            "billing_address": {
                "first_name": order.billing_address.first_name,
                "last_name": order.billing_address.last_name,
                "company": order.billing_address.company,
                "address_line_1": order.billing_address.address_line_1,
                "address_line_2": order.billing_address.address_line_2,
                "city": order.billing_address.city,
                "state": order.billing_address.state,
                "postal_code": order.billing_address.postal_code,
                "country": order.billing_address.country,
                "phone_number": order.billing_address.phone_number,
            }
            if order.billing_address
            else None,
            "payment_method": {
                "payment_type": order.payment_method.payment_type,
                "card_brand": order.payment_method.card_brand,
                "card_last_four": order.payment_method.card_last_four,
                "expiry_month": order.payment_method.expiry_month,
                "expiry_year": order.payment_method.expiry_year,
            }
            if order.payment_method
            else None,
            "payment_reference": order.payment_reference,
            "tracking_number": order.tracking_number,
            "estimated_delivery": order.estimated_delivery,
            "notes": order.notes,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": order_items,
        }

        return Response(order_data)


# Address API Views
class AddressListAPIView(generics.ListAPIView):
    """
    API endpoint for user's addresses.

    Provides list of user's saved addresses
    for shipping and billing.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get user's addresses.

        Returns:
            QuerySet: User's addresses
        """
        return Address.objects.filter(user=self.request.user).order_by(
            "-is_default", "-created_at"
        )

    def list(self, request, *args, **kwargs):
        """
        List user's addresses.

        Returns:
            Response: List of addresses
        """
        addresses = self.get_queryset()
        addresses_data = []

        for address in addresses:
            addresses_data.append(
                {
                    "id": address.id,
                    "address_type": address.address_type,
                    "first_name": address.first_name,
                    "last_name": address.last_name,
                    "company": address.company,
                    "address_line_1": address.address_line_1,
                    "address_line_2": address.address_line_2,
                    "city": address.city,
                    "state": address.state,
                    "postal_code": address.postal_code,
                    "country": address.country,
                    "phone_number": address.phone_number,
                    "is_default": address.is_default,
                    "created_at": address.created_at,
                }
            )

        return Response(addresses_data)


# Payment Method API Views
class PaymentMethodListAPIView(generics.ListAPIView):
    """
    API endpoint for user's payment methods.

    Provides list of user's saved payment methods
    for checkout.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get user's payment methods.

        Returns:
            QuerySet: User's payment methods
        """
        return PaymentMethod.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-is_default", "-created_at")

    def list(self, request, *args, **kwargs):
        """
        List user's payment methods.

        Returns:
            Response: List of payment methods
        """
        payment_methods = self.get_queryset()
        payment_methods_data = []

        for pm in payment_methods:
            payment_methods_data.append(
                {
                    "id": pm.id,
                    "payment_type": pm.payment_type,
                    "card_brand": pm.card_brand,
                    "card_last_four": pm.card_last_four,
                    "expiry_month": pm.expiry_month,
                    "expiry_year": pm.expiry_year,
                    "is_default": pm.is_default,
                    "created_at": pm.created_at,
                }
            )

        return Response(payment_methods_data)
