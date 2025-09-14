"""
Authentication views for the store application.

This module contains views for user registration, login, logout,
and profile management with beautiful UI components.
"""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    AddressForm,
    CustomAuthenticationForm,
    CustomUserCreationForm,
    PaymentMethodForm,
    UserProfileForm,
)
from .models import Address, Cart, CartItem, PaymentMethod, UserProfile

# Set up logging
logger = logging.getLogger(__name__)


class SignUpView(CreateView):
    """
    User registration view with beautiful UI.

    This view handles user registration with comprehensive
    form validation and user experience enhancements.
    """

    form_class = CustomUserCreationForm
    template_name = "store/auth/signup.html"
    success_url = reverse_lazy("store:profile_setup")

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Account"
        context["subtitle"] = "Join our community and start shopping"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            with transaction.atomic():
                user = form.save()

                # UserProfile is created automatically by signal
                # Create default cart for user
                Cart.objects.create(user=user)

                # Log the user in
                login(self.request, user)

                messages.success(
                    self.request,
                    f"Welcome {user.first_name or user.username}! Your account has been created successfully.",
                )

                logger.info(f"New user registered: {user.username}")

        except Exception as e:
            logger.error(f"Error during user registration: {e}")
            messages.error(
                self.request, "An error occurred during registration. Please try again."
            )
            return self.form_invalid(form)

        return super().form_valid(form)

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


@method_decorator([csrf_protect, never_cache], name="dispatch")
class LoginView(TemplateView):
    """
    User login view with beautiful UI.

    This view handles user authentication with enhanced
    security and user experience.
    """

    template_name = "store/auth/login.html"
    success_url = reverse_lazy("store:product_list")

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Welcome Back"
        context["subtitle"] = "Sign in to your account"
        context["next"] = self.request.GET.get("next", "")
        context["form"] = CustomAuthenticationForm()
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.

        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: Redirect or form with errors
        """
        form = CustomAuthenticationForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Merge session cart with user cart if exists
                    self._merge_session_cart(user)

                    messages.success(
                        request, f"Welcome back, {user.first_name or user.username}!"
                    )

                    logger.info(f"User logged in: {user.username}")

                    # Redirect to next page or default
                    next_url = request.POST.get("next") or self.success_url
                    return redirect(next_url)
                else:
                    messages.error(
                        request, "Your account is inactive. Please contact support."
                    )
            else:
                messages.error(
                    request, "Invalid username or password. Please try again."
                )

        # If form is invalid, return the form with errors
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return render(request, self.template_name, context)

    def _merge_session_cart(self, user):
        """
        Merge session cart with user cart.

        Args:
            user: The authenticated user
        """
        try:
            session_key = self.request.session.session_key
            if session_key:
                # Get or create user cart
                user_cart, created = Cart.objects.get_or_create(user=user)

                # Get session cart
                session_cart = Cart.objects.filter(session_key=session_key).first()

                if session_cart and session_cart.items.exists():
                    # Merge session cart items into user cart
                    for session_item in session_cart.items.all():
                        user_item, created = CartItem.objects.get_or_create(
                            cart=user_cart,
                            product=session_item.product,
                            defaults={"quantity": session_item.quantity},
                        )
                        if not created:
                            user_item.quantity += session_item.quantity
                            user_item.save()

                    # Delete session cart
                    session_cart.delete()

                    logger.info(f"Merged session cart for user: {user.username}")

        except Exception as e:
            logger.error(f"Error merging session cart: {e}")


@login_required(login_url="/login/")
def logout_view(request):
    """
    User logout view.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Redirect to home page
    """
    username = request.user.username
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    logger.info(f"User logged out: {username}")
    return redirect("store:product_list")


class ProfileSetupView(LoginRequiredMixin, CreateView):
    """
    Profile setup view for new users.

    This view allows new users to complete their profile
    information after registration.
    """

    form_class = UserProfileForm
    template_name = "store/auth/profile_setup.html"
    success_url = reverse_lazy("store:product_list")
    login_url = reverse_lazy("store:login")

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Complete Your Profile"
        context["subtitle"] = "Tell us a bit about yourself"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            profile = form.save(commit=False)
            profile.user = self.request.user
            profile.save()

            messages.success(
                self.request, "Your profile has been updated successfully!"
            )

            logger.info(
                f"Profile setup completed for user: {self.request.user.username}"
            )

            return super().form_valid(form)

        except Exception as e:
            logger.error(f"Error during profile setup: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            return self.form_invalid(form)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """
    User profile detail view.

    This view displays the user's profile information
    with options to edit and manage account settings.
    """

    model = UserProfile
    template_name = "store/auth/profile_detail.html"
    context_object_name = "profile"
    login_url = reverse_lazy("store:login")

    def get_object(self):
        """
        Get the user's profile object.

        Returns:
            UserProfile: The user's profile
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["addresses"] = self.request.user.addresses.all()
        context["payment_methods"] = self.request.user.payment_methods.filter(
            is_active=True
        )
        context["recent_orders"] = self.request.user.orders.all()[:5]
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    User profile update view.

    This view allows users to update their profile information.
    """

    model = UserProfile
    form_class = UserProfileForm
    template_name = "store/auth/profile_update.html"
    success_url = reverse_lazy("store:profile_detail")
    login_url = reverse_lazy("store:login")

    def get_object(self):
        """
        Get the user's profile object.

        Returns:
            UserProfile: The user's profile
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Profile"
        context["subtitle"] = "Keep your information up to date"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)


class AddressListView(LoginRequiredMixin, ListView):
    """
    Address list view for managing user addresses.

    This view displays all user addresses with options
    to add, edit, and delete addresses.
    """

    model = Address
    template_name = "store/auth/address_list.html"
    context_object_name = "addresses"
    login_url = reverse_lazy("store:login")

    def get_queryset(self):
        """
        Get user's addresses.

        Returns:
            QuerySet: User's addresses
        """
        return Address.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "My Addresses"
        context["subtitle"] = "Manage your shipping and billing addresses"
        return context


class AddressCreateView(LoginRequiredMixin, CreateView):
    """
    Address creation view.

    This view allows users to add new addresses.
    """

    model = Address
    form_class = AddressForm
    template_name = "store/auth/address_form.html"
    success_url = reverse_lazy("store:address_list")
    login_url = reverse_lazy("store:login")

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Address"
        context["subtitle"] = "Add a new shipping or billing address"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            address = form.save(commit=False)
            address.user = self.request.user

            # If this is set as default, unset other defaults of the same type
            if address.is_default:
                Address.objects.filter(
                    user=self.request.user, address_type=address.address_type
                ).update(is_default=False)

            address.save()

            messages.success(self.request, "Address added successfully!")

        except Exception as e:
            logger.error(f"Error creating address: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """
    Address update view.

    This view allows users to edit their addresses.
    """

    model = Address
    form_class = AddressForm
    template_name = "store/auth/address_form.html"
    success_url = reverse_lazy("store:address_list")
    login_url = reverse_lazy("store:login")

    def get_queryset(self):
        """
        Get user's addresses only.

        Returns:
            QuerySet: User's addresses
        """
        return Address.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Address"
        context["subtitle"] = "Update your address information"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            address = form.save(commit=False)

            # If this is set as default, unset other defaults of the same type
            if address.is_default:
                Address.objects.filter(
                    user=self.request.user, address_type=address.address_type
                ).exclude(id=address.id).update(is_default=False)

            address.save()

            messages.success(self.request, "Address updated successfully!")

        except Exception as e:
            logger.error(f"Error updating address: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)


@login_required(login_url="/login/")
def address_delete(request, pk):
    """
    Delete address view.

    Args:
        request: HTTP request object
        pk: Address primary key

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()

        messages.success(request, "Address deleted successfully!")

        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"success": True})

        return redirect("store:address_list")

    except Exception as e:
        logger.error(f"Error deleting address: {e}")
        messages.error(request, "An error occurred. Please try again.")

        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"success": False, "error": str(e)})

        return redirect("store:address_list")


class PaymentMethodListView(LoginRequiredMixin, ListView):
    """
    Payment method list view.

    This view displays all user payment methods.
    """

    model = PaymentMethod
    template_name = "store/auth/payment_method_list.html"
    context_object_name = "payment_methods"
    login_url = reverse_lazy("store:login")

    def get_queryset(self):
        """
        Get user's payment methods.

        Returns:
            QuerySet: User's payment methods
        """
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Payment Methods"
        context["subtitle"] = "Manage your payment information"
        return context


class PaymentMethodCreateView(LoginRequiredMixin, CreateView):
    """
    Payment method creation view.

    This view allows users to add new payment methods.
    """

    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = "store/auth/payment_method_form.html"
    success_url = reverse_lazy("store:payment_method_list")
    login_url = reverse_lazy("store:login")

    def get_form_kwargs(self):
        """
        Get form kwargs with user instance.

        Returns:
            dict: Form kwargs
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.

        Returns:
            dict: Enhanced context data
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Payment Method"
        context["subtitle"] = "Add a new payment method"
        return context

    def form_valid(self, form):
        """
        Handle valid form submission.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Redirect response
        """
        try:
            payment_method = form.save(commit=False)
            payment_method.user = self.request.user

            # If this is set as default, unset other defaults
            if payment_method.is_default:
                PaymentMethod.objects.filter(user=self.request.user).update(
                    is_default=False
                )

            payment_method.save()

            messages.success(self.request, "Payment method added successfully!")

        except Exception as e:
            logger.error(f"Error creating payment method: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)


@login_required(login_url="/login/")
def payment_method_delete(request, pk):
    """
    Delete payment method view.

    Args:
        request: HTTP request object
        pk: Payment method primary key

    Returns:
        JsonResponse: Success/failure response
    """
    try:
        payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
        payment_method.is_active = False
        payment_method.save()

        messages.success(request, "Payment method removed successfully!")

        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"success": True})

        return redirect("store:payment_method_list")

    except Exception as e:
        logger.error(f"Error deleting payment method: {e}")
        messages.error(request, "An error occurred. Please try again.")

        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"success": False, "error": str(e)})

        return redirect("store:payment_method_list")
