"""
Views for the store application.

This module contains all the view logic for the e-commerce store,
including product listing, detail views, search, and category views.
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import DetailView, ListView, TemplateView

from .forms import ProductSearchForm
from .models import Category, Product, ProductReview, ProductTag, Wishlist

# Set up logging
logger = logging.getLogger(__name__)


class ProductListView(ListView):
    """
    Product listing view with pagination, filtering, and search.

    This view provides a comprehensive product catalog with:
    - Pagination for large product catalogs
    - Category and tag filtering
    - Search functionality
    - Sorting options
    - Performance optimization
    """

    model = Product
    template_name = "store/product_list.html"
    context_object_name = "products"
    paginate_by = settings.PRODUCTS_PER_PAGE

    def get_queryset(self):
        """
        Build optimized queryset with filtering and search.

        Returns:
            QuerySet: Filtered and optimized product queryset
        """
        queryset = Product.objects.filter(is_active=True).select_related("category")

        # Apply search filter
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(short_description__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()
            logger.info(
                f"Search query '{search_query}' returned {queryset.count()} products"
            )

            # Add search query to context for display
            self.search_query = search_query

        # Apply category filter
        category_slug = self.request.GET.get("category")
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                queryset = queryset.filter(category=category)
                logger.info(f"Category filter '{category.name}' applied")
            except Category.DoesNotExist:
                logger.warning(f"Category with slug '{category_slug}' not found")

        # Apply tag filter
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            try:
                tag = ProductTag.objects.get(slug=tag_slug, is_active=True)
                queryset = queryset.filter(tags=tag)
                logger.info(f"Tag filter '{tag.name}' applied")
            except ProductTag.DoesNotExist:
                logger.warning(f"Tag with slug '{tag_slug}' not found")

        # Apply price filter
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
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

        # Apply stock filter
        in_stock = self.request.GET.get("in_stock")
        if in_stock == "true":
            queryset = queryset.filter(is_in_stock=True)
        elif in_stock == "false":
            queryset = queryset.filter(is_in_stock=False)

        # Apply sorting
        sort_by = self.request.GET.get("sort", "created_at")
        if sort_by == "name":
            queryset = queryset.order_by("name")
        elif sort_by == "price_low":
            queryset = queryset.order_by("price")
        elif sort_by == "price_high":
            queryset = queryset.order_by("-price")
        elif sort_by == "popularity":
            queryset = queryset.order_by("-view_count")
        elif sort_by == "rating":
            queryset = queryset.annotate(avg_rating=Avg("reviews__rating")).order_by(
                "-avg_rating"
            )
        else:  # Default: newest first
            queryset = queryset.order_by("-created_at")

        # Prefetch related data for performance
        queryset = queryset.prefetch_related("tags", "additional_images")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)

        # Add search form
        context["search_form"] = ProductSearchForm(self.request.GET)

        # Add categories for filtering
        context["categories"] = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
        )

        # Add popular tags
        context["popular_tags"] = (
            ProductTag.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
            .order_by("-product_count")[:10]
        )

        # Add featured products
        context["featured_products"] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related("category")[:6]

        # Add bestseller products
        context["bestseller_products"] = Product.objects.filter(
            is_active=True, is_bestseller=True
        ).select_related("category")[:6]

        # Add current filters for display
        context["current_filters"] = {
            "search": self.request.GET.get("search", ""),
            "category": self.request.GET.get("category", ""),
            "tag": self.request.GET.get("tag", ""),
            "min_price": self.request.GET.get("min_price", ""),
            "max_price": self.request.GET.get("max_price", ""),
            "in_stock": self.request.GET.get("in_stock", ""),
            "sort": self.request.GET.get("sort", "created_at"),
        }

        # Add search query for display
        context["search_query"] = getattr(self, "search_query", "")

        return context


class ProductDetailView(DetailView):
    """
    Product detail view with comprehensive product information.

    This view provides detailed product information including:
    - Product details and images
    - Related products
    - Customer reviews
    - Wishlist functionality
    - View count tracking
    """

    model = Product
    template_name = "store/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

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

    def get_object(self, queryset=None):
        """
        Get product object and increment view count.

        Returns:
            Product: The product object
        """
        product = super().get_object(queryset)

        # Increment view count (async to avoid blocking)
        try:
            product.increment_view_count()
        except Exception as e:
            logger.error(
                f"Failed to increment view count for product {product.id}: {e}"
            )

        return product

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # Add related products
        context["related_products"] = (
            Product.objects.filter(category=product.category, is_active=True)
            .exclude(id=product.id)
            .select_related("category")[:4]
        )

        # Add products with same tags
        if product.tags.exists():
            context["tagged_products"] = (
                Product.objects.filter(tags__in=product.tags.all(), is_active=True)
                .exclude(id=product.id)
                .select_related("category")[:4]
            )

        # Add customer reviews
        context["reviews"] = (
            ProductReview.objects.filter(product=product, is_approved=True)
            .select_related("user")
            .order_by("-created_at")[:10]
        )

        # Add review statistics
        reviews = product.reviews.filter(is_approved=True)
        if reviews.exists():
            context["review_stats"] = {
                "total_reviews": reviews.count(),
                "average_rating": round(
                    reviews.aggregate(Avg("rating"))["rating__avg"], 1
                ),
                "rating_distribution": reviews.values("rating")
                .annotate(count=Count("id"))
                .order_by("rating"),
            }

        # Check if user has this product in wishlist
        if self.request.user.is_authenticated:
            context["in_wishlist"] = Wishlist.objects.filter(
                user=self.request.user, product=product
            ).exists()

        # Add breadcrumb navigation
        context["breadcrumbs"] = [
            {"name": "Home", "url": "/"},
            {"name": "Products", "url": reverse("store:product_list")},
            {"name": product.category.name, "url": product.category.get_absolute_url()},
            {"name": product.name, "url": product.get_absolute_url()},
        ]

        return context


class CategoryDetailView(DetailView):
    """
    Category detail view showing products in a specific category.

    This view provides category-specific product listings with:
    - Category information
    - Paginated product listings
    - Subcategory navigation
    """

    model = Category
    template_name = "store/category_detail.html"
    context_object_name = "category"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Get category with optimized queryset.

        Returns:
            QuerySet: Optimized category queryset
        """
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        category = self.get_object()

        # Get products in this category
        products = (
            Product.objects.filter(category=category, is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )

        # Apply pagination
        paginator = Paginator(products, settings.PRODUCTS_PER_PAGE)
        page = self.request.GET.get("page")
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        context["products"] = products_page
        context["subcategories"] = category.children.filter(is_active=True)

        # Add breadcrumb navigation
        context["breadcrumbs"] = [
            {"name": "Home", "url": "/"},
            {"name": "Products", "url": reverse("store:product_list")},
            {"name": category.name, "url": category.get_absolute_url()},
        ]

        return context


class TagDetailView(DetailView):
    """
    Tag detail view showing products with a specific tag.

    This view provides tag-specific product listings with:
    - Tag information
    - Paginated product listings
    - Related tags
    """

    model = ProductTag
    template_name = "store/tag_detail.html"
    context_object_name = "tag"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Get tag with optimized queryset.

        Returns:
            QuerySet: Optimized tag queryset
        """
        return ProductTag.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        tag = self.get_object()

        # Get products with this tag
        products = (
            Product.objects.filter(tags=tag, is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )

        # Apply pagination
        paginator = Paginator(products, settings.PRODUCTS_PER_PAGE)
        page = self.request.GET.get("page")
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        context["products"] = products_page

        # Add related tags
        context["related_tags"] = (
            ProductTag.objects.filter(is_active=True)
            .exclude(id=tag.id)
            .annotate(common_products=Count("products", filter=Q(products__tags=tag)))
            .filter(common_products__gt=0)
            .order_by("-common_products")[:5]
        )

        # Add breadcrumb navigation
        context["breadcrumbs"] = [
            {"name": "Home", "url": "/"},
            {"name": "Products", "url": reverse("store:product_list")},
            {"name": f"Tag: {tag.name}", "url": tag.get_absolute_url()},
        ]

        return context


@login_required(login_url="/login/")
def add_to_wishlist(request, product_id):
    """
    Add a product to user's wishlist.

    Args:
        request: HTTP request object
        product_id: ID of the product to add

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )

        if created:
            message = f"'{product.name}' added to wishlist"
            status = "success"
        else:
            message = f"'{product.name}' is already in your wishlist"
            status = "info"

        return JsonResponse({"status": status, "message": message, "in_wishlist": True})

    except Exception as e:
        logger.error(f"Error adding product {product_id} to wishlist: {e}")
        return JsonResponse(
            {"status": "error", "message": "Failed to add product to wishlist"},
            status=500,
        )


@login_required(login_url="/login/")
def remove_from_wishlist(request, product_id):
    """
    Remove a product from user's wishlist.

    Args:
        request: HTTP request object
        product_id: ID of the product to remove

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        wishlist_item = get_object_or_404(
            Wishlist, user=request.user, product_id=product_id
        )
        product_name = wishlist_item.product.name
        wishlist_item.delete()

        return JsonResponse(
            {
                "status": "success",
                "message": f"'{product_name}' removed from wishlist",
                "in_wishlist": False,
            }
        )

    except Exception as e:
        logger.error(f"Error removing product {product_id} from wishlist: {e}")
        return JsonResponse(
            {"status": "error", "message": "Failed to remove product from wishlist"},
            status=500,
        )


@login_required(login_url="/login/")
def wishlist_view(request):
    """
    Display user's wishlist.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered wishlist template
    """
    wishlist_items = (
        Wishlist.objects.filter(user=request.user)
        .select_related("product", "product__category")
        .prefetch_related("product__tags")
    )

    context = {
        "wishlist_items": wishlist_items,
        "breadcrumbs": [
            {"name": "Home", "url": "/"},
            {"name": "Wishlist", "url": reverse("store:wishlist")},
        ],
    }

    return render(request, "store/wishlist.html", context)


def search_suggestions(request):
    """
    Provide search suggestions for autocomplete.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: List of search suggestions
    """
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"suggestions": []})

    try:
        # Search in product names and categories
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            is_active=True,
        ).select_related("category")[:5]

        suggestions = []
        for product in products:
            suggestions.append(
                {
                    "type": "product",
                    "name": product.name,
                    "url": product.get_absolute_url(),
                    "category": product.category.name,
                }
            )

        # Search in categories
        categories = Category.objects.filter(name__icontains=query, is_active=True)[:3]

        for category in categories:
            suggestions.append(
                {
                    "type": "category",
                    "name": category.name,
                    "url": category.get_absolute_url(),
                    "category": "Category",
                }
            )

        return JsonResponse({"suggestions": suggestions})

    except Exception as e:
        logger.error(f"Error generating search suggestions: {e}")
        return JsonResponse({"suggestions": []})


@login_required(login_url="/login/")
def add_review(request, product_id):
    """
    Add a product review.

    Args:
        request: HTTP request object
        product_id: ID of the product to review

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        if request.method == "POST":
            from .forms import ProductReviewForm

            form = ProductReviewForm(request.POST)
            if form.is_valid():
                # Check if user already reviewed this product
                existing_review = ProductReview.objects.filter(
                    user=request.user, product=product
                ).first()

                if existing_review:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "You have already reviewed this product",
                        },
                        status=400,
                    )

                # Create new review
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.is_verified_purchase = (
                    False  # Could be enhanced to check actual purchases
                )
                review.save()

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Thank you for your review! It has been submitted for approval.",
                        "review_id": review.id,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Please correct the errors below.",
                        "errors": form.errors,
                    },
                    status=400,
                )
        else:
            return JsonResponse(
                {"status": "error", "message": "Invalid request method"}, status=405
            )

    except Exception as e:
        logger.error(f"Error adding review for product {product_id}: {e}")
        return JsonResponse(
            {"status": "error", "message": "Failed to submit review"},
            status=500,
        )


# Cache decorators for performance optimization
@method_decorator(cache_page(60 * 15), name="dispatch")  # Cache for 15 minutes
@method_decorator(vary_on_cookie, name="dispatch")
class CachedProductListView(ProductListView):
    """Cached version of ProductListView for better performance."""

    pass


@method_decorator(cache_page(60 * 30), name="dispatch")  # Cache for 30 minutes
@method_decorator(vary_on_cookie, name="dispatch")
class CachedCategoryDetailView(CategoryDetailView):
    """Cached version of CategoryDetailView for better performance."""

    pass


class HomePageView(TemplateView):
    """
    Homepage view with featured products, categories, and statistics.

    Provides a beautiful landing page with:
    - Hero section
    - Featured products
    - Popular categories
    - Statistics
    - Call-to-action sections
    """

    template_name = "store/home.html"

    def get_context_data(self, **kwargs):
        """
        Get context data for the homepage.

        Returns:
            dict: Context data for the template
        """
        context = super().get_context_data(**kwargs)

        # Get featured products
        featured_products = (
            Product.objects.filter(is_active=True, is_featured=True)
            .select_related("category")
            .prefetch_related("tags")[:8]
        )

        # Get bestseller products
        bestseller_products = (
            Product.objects.filter(is_active=True, is_bestseller=True)
            .select_related("category")
            .prefetch_related("tags")[:8]
        )

        # Get popular categories
        popular_categories = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count("products", filter=Q(products__is_active=True))
            )
            .filter(product_count__gt=0)
            .order_by("-product_count")[:6]
        )

        # Get recent products
        recent_products = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags")
            .order_by("-created_at")[:6]
        )

        # Get statistics
        total_products = Product.objects.filter(is_active=True).count()
        total_categories = Category.objects.filter(is_active=True).count()
        total_reviews = ProductReview.objects.filter(is_approved=True).count()

        context.update(
            {
                "featured_products": featured_products,
                "bestseller_products": bestseller_products,
                "popular_categories": popular_categories,
                "recent_products": recent_products,
                "total_products": total_products,
                "total_categories": total_categories,
                "total_reviews": total_reviews,
            }
        )

        return context
