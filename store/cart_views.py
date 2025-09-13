"""
Shopping cart views for the store application.

This module contains views for managing shopping cart functionality
including adding, removing, and updating cart items with AJAX support.
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import CartItemForm
from .models import Cart, CartItem, Product, UserProfile

# Set up logging
logger = logging.getLogger(__name__)


def get_or_create_cart(request):
    """
    Get or create cart for the current user or session.

    Args:
        request: HTTP request object

    Returns:
        Cart: The user's or session's cart
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(session_key=session_key)

    return cart


@require_POST
def add_to_cart(request, product_id):
    """
    Add a product to the shopping cart.

    Args:
        request: HTTP request object
        product_id: ID of the product to add

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Check if product is in stock
        if not product.is_in_stock:
            return JsonResponse(
                {
                    "success": False,
                    "message": "This product is currently out of stock.",
                },
                status=400,
            )

        # Get or create cart
        cart = get_or_create_cart(request)

        # Get quantity from request
        quantity = int(request.POST.get("quantity", 1))

        if quantity <= 0:
            return JsonResponse(
                {"success": False, "message": "Quantity must be greater than 0."},
                status=400,
            )

        # Check if product already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()

        # Update cart timestamp
        cart.save()

        # Calculate cart totals
        cart_total_items = cart.get_total_items()
        cart_total_price = cart.get_total_price_with_currency()

        return JsonResponse(
            {
                "success": True,
                "message": f"{product.name} added to cart successfully!",
                "cart_total_items": cart_total_items,
                "cart_total_price": cart_total_price,
                "item_quantity": cart_item.quantity,
            }
        )

    except Exception as e:
        logger.error(f"Error adding product {product_id} to cart: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_POST
def update_cart_item(request, item_id):
    """
    Update quantity of a cart item.

    Args:
        request: HTTP request object
        item_id: ID of the cart item to update

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        # Get new quantity from request
        new_quantity = int(request.POST.get("quantity", 1))

        if new_quantity <= 0:
            # Remove item if quantity is 0 or negative
            cart_item.delete()
            message = f"{cart_item.product.name} removed from cart."
        else:
            # Check stock availability
            if new_quantity > cart_item.product.stock_quantity:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Only {cart_item.product.stock_quantity} items available in stock.",
                    },
                    status=400,
                )

            cart_item.quantity = new_quantity
            cart_item.save()
            message = f"{cart_item.product.name} quantity updated."

        # Update cart timestamp
        cart.save()

        # Calculate cart totals
        cart_total_items = cart.get_total_items()
        cart_total_price = cart.get_total_price_with_currency()
        item_total_price = (
            cart_item.get_total_price_with_currency()
            if cart_item.quantity > 0
            else "$0.00"
        )

        return JsonResponse(
            {
                "success": True,
                "message": message,
                "cart_total_items": cart_total_items,
                "cart_total_price": cart_total_price,
                "item_total_price": item_total_price,
                "item_quantity": cart_item.quantity if cart_item.quantity > 0 else 0,
            }
        )

    except Exception as e:
        logger.error(f"Error updating cart item {item_id}: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_POST
def remove_from_cart(request, item_id):
    """
    Remove a product from the shopping cart.

    Args:
        request: HTTP request object
        item_id: ID of the cart item to remove

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product_name = cart_item.product.name

        cart_item.delete()

        # Update cart timestamp
        cart.save()

        # Calculate cart totals
        cart_total_items = cart.get_total_items()
        cart_total_price = cart.get_total_price_with_currency()

        return JsonResponse(
            {
                "success": True,
                "message": f"{product_name} removed from cart.",
                "cart_total_items": cart_total_items,
                "cart_total_price": cart_total_price,
            }
        )

    except Exception as e:
        logger.error(f"Error removing cart item {item_id}: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_GET
def get_cart_count(request):
    """
    Get the current cart item count.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: Cart count
    """
    try:
        cart = get_or_create_cart(request)
        cart_count = cart.get_total_items()

        return JsonResponse({"success": True, "cart_count": cart_count})

    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
        return JsonResponse({"success": False, "cart_count": 0})


class CartListView(LoginRequiredMixin, ListView):
    """
    Shopping cart list view.

    This view displays all items in the user's shopping cart
    with options to update quantities and remove items.
    """

    model = CartItem
    template_name = "store/cart/cart_list.html"
    context_object_name = "cart_items"
    login_url = reverse_lazy("store:login")

    def get_queryset(self):
        """
        Get cart items for the current user or session.

        Returns:
            QuerySet: Cart items
        """
        cart = get_or_create_cart(self.request)
        return CartItem.objects.filter(cart=cart).select_related(
            "product", "product__category"
        )

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)

        context["cart"] = cart
        context["cart_total_items"] = cart.get_total_items()
        context["cart_total_price"] = cart.get_total_price_with_currency()
        context["cart_subtotal"] = cart.get_total_price()

        # Calculate shipping (free shipping over $50)
        from decimal import Decimal

        shipping_threshold = Decimal("50.00")
        if context["cart_subtotal"] >= shipping_threshold:
            context["shipping_cost"] = Decimal("0.00")
            context["free_shipping"] = True
        else:
            context["shipping_cost"] = Decimal("9.99")
            context["free_shipping"] = False
            context["shipping_remaining"] = (
                shipping_threshold - context["cart_subtotal"]
            )

        # Calculate tax (8.5%)
        tax_rate = Decimal("0.085")
        context["tax_amount"] = context["cart_subtotal"] * tax_rate

        # Calculate total
        context["order_total"] = (
            context["cart_subtotal"] + context["shipping_cost"] + context["tax_amount"]
        )

        # Add breadcrumb navigation
        context["breadcrumbs"] = [
            {"name": "Home", "url": "/"},
            {"name": "Shopping Cart", "url": reverse("store:cart_list")},
        ]

        return context


@method_decorator(csrf_exempt, name="dispatch")
class CartItemUpdateView(UpdateView):
    """
    Cart item update view for AJAX requests.

    This view handles updating cart item quantities via AJAX.
    """

    model = CartItem
    form_class = CartItemForm
    http_method_names = ["post"]

    def get_queryset(self):
        """
        Get cart items for the current user or session.

        Returns:
            QuerySet: Cart items
        """
        cart = get_or_create_cart(self.request)
        return CartItem.objects.filter(cart=cart)

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            JsonResponse: Success response
        """
        try:
            cart_item = form.save()
            cart = cart_item.cart
            cart.save()  # Update cart timestamp

            return JsonResponse(
                {
                    "success": True,
                    "message": "Cart updated successfully!",
                    "cart_total_items": cart.get_total_items(),
                    "cart_total_price": cart.get_total_price_with_currency(),
                    "item_total_price": cart_item.get_total_price_with_currency(),
                }
            )

        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            return JsonResponse(
                {"success": False, "message": "An error occurred. Please try again."},
                status=500,
            )

    def form_invalid(self, form):
        """
        Handle invalid form submission.

        Args:
            form: The invalid form instance

        Returns:
            JsonResponse: Error response
        """
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid quantity. Please try again.",
                "errors": form.errors,
            },
            status=400,
        )


@method_decorator(csrf_exempt, name="dispatch")
class CartItemDeleteView(DeleteView):
    """
    Cart item delete view for AJAX requests.

    This view handles removing cart items via AJAX.
    """

    model = CartItem
    http_method_names = ["post"]

    def get_queryset(self):
        """
        Get cart items for the current user or session.

        Returns:
            QuerySet: Cart items
        """
        cart = get_or_create_cart(self.request)
        return CartItem.objects.filter(cart=cart)

    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            JsonResponse: Success response
        """
        try:
            cart_item = self.get_object()
            product_name = cart_item.product.name
            cart = cart_item.cart

            cart_item.delete()
            cart.save()  # Update cart timestamp

            return JsonResponse(
                {
                    "success": True,
                    "message": f"{product_name} removed from cart.",
                    "cart_total_items": cart.get_total_items(),
                    "cart_total_price": cart.get_total_price_with_currency(),
                }
            )

        except Exception as e:
            logger.error(f"Error deleting cart item: {e}")
            return JsonResponse(
                {"success": False, "message": "An error occurred. Please try again."},
                status=500,
            )


@require_POST
def clear_cart(request):
    """
    Clear all items from the shopping cart.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        cart.save()  # Update cart timestamp

        return JsonResponse(
            {
                "success": True,
                "message": "Cart cleared successfully!",
                "cart_total_items": 0,
                "cart_total_price": "$0.00",
            }
        )

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_POST
def apply_coupon(request):
    """
    Apply a coupon code to the cart.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        coupon_code = request.POST.get("coupon_code", "").strip().upper()

        if not coupon_code:
            return JsonResponse(
                {"success": False, "message": "Please enter a coupon code."}, status=400
            )

        # Simple coupon validation (in a real app, this would be more sophisticated)
        valid_coupons = {
            "WELCOME10": {"discount": 0.10, "type": "percentage"},
            "SAVE20": {"discount": 0.20, "type": "percentage"},
            "FREESHIP": {"discount": 9.99, "type": "fixed"},
        }

        if coupon_code not in valid_coupons:
            return JsonResponse(
                {"success": False, "message": "Invalid coupon code."}, status=400
            )

        # Store coupon in session
        request.session["applied_coupon"] = coupon_code
        request.session["coupon_discount"] = valid_coupons[coupon_code]

        cart = get_or_create_cart(request)
        cart_total = cart.get_total_price()

        # Calculate discount
        coupon = valid_coupons[coupon_code]
        if coupon["type"] == "percentage":
            discount_amount = cart_total * coupon["discount"]
        else:
            discount_amount = coupon["discount"]

        return JsonResponse(
            {
                "success": True,
                "message": f'Coupon "{coupon_code}" applied successfully!',
                "discount_amount": f"${discount_amount:.2f}",
                "cart_total_items": cart.get_total_items(),
                "cart_total_price": cart.get_total_price_with_currency(),
            }
        )

    except Exception as e:
        logger.error(f"Error applying coupon: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_POST
def remove_coupon(request):
    """
    Remove applied coupon from the cart.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        if "applied_coupon" in request.session:
            coupon_code = request.session.pop("applied_coupon")
            request.session.pop("coupon_discount", None)

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Coupon "{coupon_code}" removed.',
                    "cart_total_items": get_or_create_cart(request).get_total_items(),
                    "cart_total_price": get_or_create_cart(
                        request
                    ).get_total_price_with_currency(),
                }
            )
        else:
            return JsonResponse(
                {"success": False, "message": "No coupon applied."}, status=400
            )

    except Exception as e:
        logger.error(f"Error removing coupon: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )
