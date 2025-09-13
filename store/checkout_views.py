"""
Checkout views for the store application.

This module contains views for the complete checkout workflow including
shipping, payment, and order confirmation with beautiful UI.
"""

import logging
import uuid
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView

from .cart_views import get_or_create_cart
from .forms import AddressForm, CheckoutForm, PaymentMethodForm
from .models import (
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    UserProfile,
)

# Set up logging
logger = logging.getLogger(__name__)


def generate_order_number():
    """
    Generate a unique order number.

    Returns:
        str: Unique order number
    """
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


class CheckoutView(LoginRequiredMixin, CreateView):
    """
    Checkout view for completing purchases.

    This view handles the complete checkout process including
    address selection, payment method, and order creation.
    """

    template_name = "store/checkout/checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("store:order_confirmation")

    def get_form_kwargs(self):
        """
        Get form kwargs with user instance.

        Returns:
            dict: Form kwargs
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests and check for empty cart.

        Returns:
            HttpResponse: Response or redirect
        """
        # Check if cart is empty
        cart = get_or_create_cart(request)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect("store:cart_list")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        # Create a basic context dictionary
        context = {
            "form": self.get_form(),  # Create form with user
        }

        # Get user's cart
        cart = get_or_create_cart(self.request)
        cart_items = CartItem.objects.filter(cart=cart).select_related("product")

        # Calculate totals
        subtotal = sum(item.get_total_price() for item in cart_items)

        # Shipping calculation (free shipping over $50)
        shipping_threshold = Decimal("50.00")
        if subtotal >= shipping_threshold:
            shipping_cost = Decimal("0.00")
            free_shipping = True
        else:
            shipping_cost = Decimal("9.99")
            free_shipping = False
            shipping_remaining = shipping_threshold - subtotal

        # Tax calculation (8.5%)
        tax_rate = Decimal("0.085")
        tax_amount = subtotal * tax_rate

        # Total calculation
        total = subtotal + shipping_cost + tax_amount

        # Apply coupon discount if any
        applied_coupon = getattr(self.request, "session", {}).get("applied_coupon")
        coupon_discount = getattr(self.request, "session", {}).get(
            "coupon_discount", {}
        )
        discount_amount = Decimal("0.00")

        if applied_coupon and coupon_discount:
            if coupon_discount.get("type") == "percentage":
                discount_amount = subtotal * Decimal(
                    str(coupon_discount.get("discount", 0))
                )
            else:
                discount_amount = Decimal(str(coupon_discount.get("discount", 0)))

            total = max(Decimal("0.00"), total - discount_amount)

        context.update(
            {
                "cart": cart,
                "cart_items": cart_items,
                "cart_total_items": cart.get_total_items(),
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "tax_amount": tax_amount,
                "discount_amount": discount_amount,
                "total": total,
                "free_shipping": free_shipping,
                "shipping_remaining": shipping_remaining if not free_shipping else None,
                "applied_coupon": applied_coupon,
                "coupon_discount": coupon_discount,
                "breadcrumbs": [
                    {"name": "Home", "url": "/"},
                    {"name": "Cart", "url": reverse("store:cart_list")},
                    {"name": "Checkout", "url": reverse("store:checkout")},
                ],
            }
        )

        return context

    def form_valid(self, form):
        """
        Handle valid form submission and create order.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            with transaction.atomic():
                # Get user's cart
                cart = get_or_create_cart(self.request)
                cart_items = CartItem.objects.filter(cart=cart)

                if not cart_items.exists():
                    messages.error(self.request, "Your cart is empty.")
                    return redirect("store:cart_list")

                # Calculate totals
                subtotal = sum(item.get_total_price() for item in cart_items)

                # Shipping calculation
                shipping_threshold = Decimal("50.00")
                if subtotal >= shipping_threshold:
                    shipping_cost = Decimal("0.00")
                else:
                    shipping_cost = Decimal("9.99")

                # Tax calculation
                tax_rate = Decimal("0.085")
                tax_amount = subtotal * tax_rate

                # Apply coupon discount
                applied_coupon = self.request.session.get("applied_coupon")
                coupon_discount = self.request.session.get("coupon_discount", {})
                discount_amount = Decimal("0.00")

                if applied_coupon and coupon_discount:
                    if coupon_discount.get("type") == "percentage":
                        discount_amount = subtotal * Decimal(
                            str(coupon_discount.get("discount", 0))
                        )
                    else:
                        discount_amount = Decimal(
                            str(coupon_discount.get("discount", 0))
                        )

                # Calculate total
                total = subtotal + shipping_cost + tax_amount - discount_amount

                # Generate order number
                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

                # Get addresses
                use_billing_for_shipping = form.cleaned_data.get(
                    "use_billing_for_shipping", True
                )
                billing_address = form.cleaned_data["billing_address"]
                shipping_address = (
                    billing_address
                    if use_billing_for_shipping
                    else form.cleaned_data["shipping_address"]
                )

                # Create order
                order = Order.objects.create(
                    user=self.request.user,
                    order_number=order_number,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    shipping_amount=shipping_cost,
                    discount_amount=discount_amount,
                    total_amount=total,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    payment_method=form.cleaned_data["payment_method"],
                    notes=form.cleaned_data.get("order_notes", ""),
                    status="pending",
                    payment_status="pending",
                )

                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.product.get_display_price(),
                        total_price=cart_item.get_total_price(),
                    )

                    # Update product stock
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()

                # Clear cart
                cart_items.delete()

                # Clear applied coupon
                if "applied_coupon" in self.request.session:
                    del self.request.session["applied_coupon"]
                if "coupon_discount" in self.request.session:
                    del self.request.session["coupon_discount"]

                # Store order ID in session for confirmation page
                self.request.session["order_id"] = order.id

                messages.success(
                    self.request, f"Order {order.order_number} created successfully!"
                )

                logger.info(
                    f"Order created: {order.order_number} for user {self.request.user.username}"
                )

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            messages.error(
                self.request,
                "An error occurred while processing your order. Please try again.",
            )
            return self.form_invalid(form)

        # Process the checkout instead of calling super().form_valid()
        try:
            # Get the selected addresses and payment method
            shipping_address = form.cleaned_data.get("shipping_address")
            billing_address = form.cleaned_data.get("billing_address")
            payment_method = form.cleaned_data.get("payment_method")
            use_billing_for_shipping = form.cleaned_data.get(
                "use_billing_for_shipping", False
            )
            order_notes = form.cleaned_data.get("order_notes", "")

            # If using billing for shipping, use billing address for both
            if use_billing_for_shipping:
                shipping_address = billing_address

            # Get user's cart
            cart = get_or_create_cart(self.request)
            cart_items = CartItem.objects.filter(cart=cart).select_related("product")

            if not cart_items.exists():
                messages.error(self.request, "Your cart is empty.")
                return redirect("store:cart_list")

            # Calculate totals
            subtotal = sum(item.get_total_price() for item in cart_items)

            # Shipping calculation (free shipping over $50)
            shipping_threshold = Decimal("50.00")
            if subtotal >= shipping_threshold:
                shipping_cost = Decimal("0.00")
            else:
                shipping_cost = Decimal("9.99")

            # Tax calculation (8.5%)
            tax_rate = Decimal("0.085")
            tax_amount = subtotal * tax_rate

            # Total calculation
            total = subtotal + shipping_cost + tax_amount

            # Apply coupon discount if any
            applied_coupon = getattr(self.request, "session", {}).get("applied_coupon")
            coupon_discount = getattr(self.request, "session", {}).get(
                "coupon_discount", {}
            )
            discount_amount = Decimal("0.00")

            if applied_coupon and coupon_discount:
                if coupon_discount.get("type") == "percentage":
                    discount_amount = subtotal * Decimal(
                        str(coupon_discount.get("discount", 0))
                    )
                else:
                    discount_amount = Decimal(str(coupon_discount.get("discount", 0)))

                total = max(Decimal("0.00"), total - discount_amount)

            # Create order
            order = Order.objects.create(
                user=self.request.user,
                order_number=generate_order_number(),
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method=payment_method,
                subtotal=subtotal,
                shipping_amount=shipping_cost,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total,
                status="pending",
                notes=order_notes,
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                )

            # Clear the cart
            cart_items.delete()

            # Clear applied coupon
            if "applied_coupon" in self.request.session:
                del self.request.session["applied_coupon"]
            if "coupon_discount" in self.request.session:
                del self.request.session["coupon_discount"]

            # Log order creation
            logger.info(
                f"Order created: {order.order_number} for user {self.request.user.username}"
            )

            messages.success(
                self.request,
                f"Order {order.order_number} placed successfully! You will receive a confirmation email shortly.",
            )

            return redirect("store:order_detail", pk=order.pk)

        except Exception as e:
            logger.error(f"Error processing checkout: {str(e)}")
            messages.error(
                self.request,
                "An error occurred while processing your order. Please try again.",
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handle invalid form submission.

        Args:
            form: The invalid form instance

        Returns:
            HttpResponse: Form with errors
        """
        messages.error(self.request, "Please correct the errors below and try again.")
        return super().form_invalid(form)


class OrderConfirmationView(LoginRequiredMixin, DetailView):
    """
    Order confirmation view.

    This view displays the order confirmation with order details
    and next steps for the customer.
    """

    model = Order
    template_name = "store/checkout/order_confirmation.html"
    context_object_name = "order"

    def get_object(self):
        """
        Get the order from session or return 404.

        Returns:
            Order: The order object
        """
        order_id = self.request.session.get("order_id")
        if not order_id:
            raise Http404("Order not found")

        order = get_object_or_404(Order, id=order_id, user=self.request.user)

        # Clear order ID from session
        if "order_id" in self.request.session:
            del self.request.session["order_id"]

        return order

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        context.update(
            {
                "order_items": order.items.all(),
                "breadcrumbs": [
                    {"name": "Home", "url": "/"},
                    {
                        "name": "Order Confirmation",
                        "url": reverse("store:order_confirmation"),
                    },
                ],
            }
        )

        return context


class OrderListView(LoginRequiredMixin, ListView):
    """
    Order list view for user's order history.

    This view displays all orders for the authenticated user
    with pagination and filtering options.
    """

    model = Order
    template_name = "store/checkout/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        """
        Get user's orders.

        Returns:
            QuerySet: User's orders
        """
        return Order.objects.filter(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "Home", "url": "/"},
            {"name": "My Orders", "url": reverse("store:order_list")},
        ]
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Order detail view.

    This view displays detailed information about a specific order
    including items, addresses, and tracking information.
    """

    model = Order
    template_name = "store/checkout/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        """
        Get user's orders only.

        Returns:
            QuerySet: User's orders
        """
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        context.update(
            {
                "order_items": order.items.all(),
                "breadcrumbs": [
                    {"name": "Home", "url": "/"},
                    {"name": "My Orders", "url": reverse("store:order_list")},
                    {
                        "name": f"Order {order.order_number}",
                        "url": order.get_absolute_url(),
                    },
                ],
            }
        )

        return context


@login_required
def quick_checkout(request, product_id):
    """
    Quick checkout for single product purchases.

    Args:
        request: HTTP request object
        product_id: ID of the product to purchase

    Returns:
        HttpResponse: Redirect to checkout or product page
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        if not product.is_in_stock:
            messages.error(request, "This product is currently out of stock.")
            return redirect(product.get_absolute_url())

        # Get or create cart
        cart = get_or_create_cart(request)

        # Clear existing cart items
        cart.items.all().delete()

        # Add product to cart
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        messages.success(request, f"{product.name} added to cart for quick checkout.")
        return redirect("store:checkout")

    except Exception as e:
        logger.error(f"Error in quick checkout: {e}")
        messages.error(request, "An error occurred. Please try again.")
        return redirect("store:product_list")


@require_POST
def update_order_status(request, order_id):
    """
    Update order status (admin only).

    Args:
        request: HTTP request object
        order_id: ID of the order to update

    Returns:
        JsonResponse: Success/failure response
    """
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "message": "Permission denied"}, status=403
        )

    try:
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get("status")

        if new_status not in dict(Order.ORDER_STATUS_CHOICES):
            return JsonResponse(
                {"success": False, "message": "Invalid status"}, status=400
            )

        order.status = new_status
        order.save()

        logger.info(
            f"Order {order.order_number} status updated to {new_status} by {request.user.username}"
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Order status updated to {order.get_status_display()}",
            }
        )

    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )


@require_POST
def add_tracking_number(request, order_id):
    """
    Add tracking number to order (admin only).

    Args:
        request: HTTP request object
        order_id: ID of the order to update

    Returns:
        JsonResponse: Success/failure response
    """
    if not request.user.is_staff:
        return JsonResponse(
            {"success": False, "message": "Permission denied"}, status=403
        )

    try:
        order = get_object_or_404(Order, id=order_id)
        tracking_number = request.POST.get("tracking_number", "").strip()

        if not tracking_number:
            return JsonResponse(
                {"success": False, "message": "Tracking number is required"}, status=400
            )

        order.tracking_number = tracking_number
        order.status = "shipped"
        order.save()

        logger.info(
            f"Tracking number {tracking_number} added to order {order.order_number}"
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Tracking number {tracking_number} added successfully",
            }
        )

    except Exception as e:
        logger.error(f"Error adding tracking number: {e}")
        return JsonResponse(
            {"success": False, "message": "An error occurred. Please try again."},
            status=500,
        )
