"""
Forms for the store application.

This module contains Django forms for user interactions including:
- Product search and filtering
- Product reviews and ratings
- Wishlist management
"""

from datetime import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    PaymentMethod,
    Product,
    ProductReview,
    ProductTag,
    UserProfile,
)


class ProductSearchForm(forms.Form):
    """
    Form for product search and filtering.

    This form provides comprehensive search and filtering options
    for the product catalog.
    """

    # Search field
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search products...",
                "aria-label": "Search products",
            }
        ),
        help_text=_("Search by product name, description, or category"),
    )

    # Category filter
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(
            attrs={"class": "form-select", "aria-label": "Filter by category"}
        ),
    )

    # Tag filter
    tag = forms.ModelChoiceField(
        queryset=ProductTag.objects.filter(is_active=True),
        required=False,
        empty_label=_("All Tags"),
        widget=forms.Select(
            attrs={"class": "form-select", "aria-label": "Filter by tag"}
        ),
    )

    # Price range filters
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Min price",
                "aria-label": "Minimum price",
            }
        ),
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Max price",
                "aria-label": "Maximum price",
            }
        ),
    )

    # Stock filter
    in_stock = forms.ChoiceField(
        choices=[
            ("", _("All Products")),
            ("true", _("In Stock Only")),
            ("false", _("Out of Stock Only")),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "aria-label": "Stock availability filter"}
        ),
    )

    # Sorting options
    SORT_CHOICES = [
        ("created_at", _("Newest First")),
        ("name", _("Name A-Z")),
        ("price_low", _("Price: Low to High")),
        ("price_high", _("Price: High to Low")),
        ("popularity", _("Most Popular")),
        ("rating", _("Highest Rated")),
    ]

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial="created_at",
        widget=forms.Select(
            attrs={"class": "form-select", "aria-label": "Sort products by"}
        ),
    )

    def clean(self):
        """
        Validate form data and ensure logical consistency.

        Returns:
            dict: Cleaned form data

        Raises:
            forms.ValidationError: If validation fails
        """
        cleaned_data = super().clean()

        # Validate price range
        min_price = cleaned_data.get("min_price")
        max_price = cleaned_data.get("max_price")

        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(
                _("Minimum price cannot be greater than maximum price.")
            )

        # Ensure at least one filter is applied if search is empty
        search = cleaned_data.get("search", "").strip()
        if not search:
            has_filters = any(
                [
                    cleaned_data.get("category"),
                    cleaned_data.get("tag"),
                    cleaned_data.get("min_price"),
                    cleaned_data.get("max_price"),
                    cleaned_data.get("in_stock"),
                ]
            )
            if not has_filters:
                # No filters applied, this is fine for showing all products
                pass

        return cleaned_data

    def get_search_query(self):
        """
        Get the search query for database filtering.

        Returns:
            str: Cleaned search query
        """
        return self.cleaned_data.get("search", "").strip()

    def get_filters(self):
        """
        Get all applied filters as a dictionary.

        Returns:
            dict: Dictionary of applied filters
        """
        filters = {}

        if self.cleaned_data.get("category"):
            filters["category"] = self.cleaned_data["category"]

        if self.cleaned_data.get("tag"):
            filters["tag"] = self.cleaned_data["tag"]

        if self.cleaned_data.get("min_price"):
            filters["min_price"] = self.cleaned_data["min_price"]

        if self.cleaned_data.get("max_price"):
            filters["max_price"] = self.cleaned_data["max_price"]

        if self.cleaned_data.get("in_stock"):
            filters["in_stock"] = self.cleaned_data["in_stock"]

        if self.cleaned_data.get("sort"):
            filters["sort"] = self.cleaned_data["sort"]

        return filters


class ProductReviewForm(forms.ModelForm):
    """
    Form for submitting product reviews.

    This form allows customers to submit reviews with ratings,
    titles, and comments.
    """

    class Meta:
        model = ProductReview
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.Select(
                attrs={"class": "form-select", "aria-label": "Product rating"}
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Review title",
                    "aria-label": "Review title",
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Share your experience with this product...",
                    "aria-label": "Review comment",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with custom rating choices."""
        super().__init__(*args, **kwargs)

        # Customize rating choices with better labels
        self.fields["rating"].choices = [
            (5, "⭐⭐⭐⭐⭐ Excellent"),
            (4, "⭐⭐⭐⭐ Very Good"),
            (3, "⭐⭐⭐ Good"),
            (2, "⭐⭐ Fair"),
            (1, "⭐ Poor"),
        ]

        # Add help text
        self.fields["title"].help_text = _("Brief summary of your review")
        self.fields["comment"].help_text = _("Detailed feedback about the product")

    def clean_title(self):
        """
        Validate review title.

        Returns:
            str: Cleaned title

        Raises:
            forms.ValidationError: If title is too short
        """
        title = self.cleaned_data.get("title", "").strip()
        if len(title) < 5:
            raise forms.ValidationError(
                _("Review title must be at least 5 characters long.")
            )
        return title

    def clean_comment(self):
        """
        Validate review comment.

        Returns:
            str: Cleaned comment

        Raises:
            forms.ValidationError: If comment is too short or too long
        """
        comment = self.cleaned_data.get("comment", "").strip()
        if len(comment) < 20:
            raise forms.ValidationError(
                _("Review comment must be at least 20 characters long.")
            )
        if len(comment) > 1000:
            raise forms.ValidationError(
                _("Review comment must be no more than 1000 characters long.")
            )
        return comment


class AdvancedSearchForm(ProductSearchForm):
    """
    Advanced search form with additional filtering options.

    This form extends the basic search form with advanced features
    like date ranges, product status, and more.
    """

    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "aria-label": "Products added from date",
            }
        ),
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "aria-label": "Products added until date",
            }
        ),
    )

    # Product status filters
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "aria-label": "Featured products only"}
        ),
    )

    is_bestseller = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "aria-label": "Bestseller products only",
            }
        ),
    )

    # Rating filter
    min_rating = forms.ChoiceField(
        choices=[
            ("", _("Any Rating")),
            ("4", _("4+ Stars")),
            ("3", _("3+ Stars")),
            ("2", _("2+ Stars")),
            ("1", _("1+ Stars")),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "aria-label": "Minimum rating filter"}
        ),
    )

    def clean(self):
        """
        Validate advanced search form data.

        Returns:
            dict: Cleaned form data

        Raises:
            forms.ValidationError: If validation fails
        """
        cleaned_data = super().clean()

        # Validate date range
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_("Start date cannot be after end date."))

        return cleaned_data


class WishlistForm(forms.Form):
    """
    Form for wishlist operations.

    This form handles adding/removing products from wishlists
    and wishlist management.
    """

    ACTION_CHOICES = [
        ("add", _("Add to Wishlist")),
        ("remove", _("Remove from Wishlist")),
        ("move_to_cart", _("Move to Cart")),
        ("share", _("Share Wishlist")),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.HiddenInput())

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_product_id(self):
        """
        Validate that the product exists and is active.

        Returns:
            int: Valid product ID

        Raises:
            forms.ValidationError: If product doesn't exist or is inactive
        """
        product_id = self.cleaned_data.get("product_id")
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            return product_id
        except Product.DoesNotExist:
            raise forms.ValidationError(_("Product not found or no longer available."))


class ProductFilterForm(forms.Form):
    """
    Form for advanced product filtering.

    This form provides a comprehensive interface for filtering
    products by various criteria.
    """

    # Price range slider
    price_range = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text=_("Price range in format: min-max"),
    )

    # Multiple category selection
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    # Multiple tag selection
    tags = forms.ModelMultipleChoiceField(
        queryset=ProductTag.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    # Availability filters
    availability = forms.MultipleChoiceField(
        choices=[
            ("in_stock", _("In Stock")),
            ("low_stock", _("Low Stock")),
            ("out_of_stock", _("Out of Stock")),
            ("pre_order", _("Pre-Order Available")),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    # Product features
    features = forms.MultipleChoiceField(
        choices=[
            ("featured", _("Featured Products")),
            ("bestseller", _("Bestsellers")),
            ("new_arrival", _("New Arrivals")),
            ("on_sale", _("On Sale")),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    def clean_price_range(self):
        """
        Validate and parse price range.

        Returns:
            tuple: (min_price, max_price) or None

        Raises:
            forms.ValidationError: If price range format is invalid
        """
        price_range = self.cleaned_data.get("price_range")
        if not price_range:
            return None

        try:
            min_price, max_price = map(float, price_range.split("-"))
            if min_price < 0 or max_price < 0 or min_price > max_price:
                raise ValueError
            return (min_price, max_price)
        except (ValueError, AttributeError):
            raise forms.ValidationError(
                _("Invalid price range format. Use format: min-max")
            )


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form with additional fields.

    This form extends Django's default UserCreationForm to include
    additional user information and improved styling.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email address",
                "aria-label": "Email address",
            }
        ),
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First name",
                "aria-label": "First name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last name",
                "aria-label": "Last name",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username",
                    "aria-label": "Username",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom styling for password fields.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Password",
                "aria-label": "Password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm password",
                "aria-label": "Confirm password",
            }
        )

    def clean_email(self):
        """
        Validate email uniqueness.

        Returns:
            str: Cleaned email address
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "A user with this email address already exists."
            )
        return email

    def save(self, commit=True):
        """
        Save user with additional information.

        Args:
            commit: Whether to commit the user to database

        Returns:
            User: The created user instance
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form with improved styling.

    This form extends Django's default AuthenticationForm with
    better styling and user experience.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom styling.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Username or Email",
                "aria-label": "Username or Email",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Password",
                "aria-label": "Password",
            }
        )


class UserProfileForm(forms.ModelForm):
    """
    User profile form for updating profile information.

    This form allows users to update their profile information
    including personal details and preferences.
    """

    class Meta:
        model = UserProfile
        fields = ["phone_number", "date_of_birth", "gender", "bio", "newsletter_subscription"]
        widgets = {
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                    "aria-label": "Phone number",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "aria-label": "Date of birth",
                }
            ),
            "gender": forms.Select(
                attrs={"class": "form-select", "aria-label": "Gender"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us about yourself...",
                    "rows": 4,
                    "maxlength": "500",
                    "aria-label": "Bio",
                }
            ),
            "newsletter_subscription": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "aria-label": "Newsletter subscription",
                }
            ),
        }


class AddressForm(forms.ModelForm):
    """
    Address form for shipping and billing addresses.

    This form allows users to add and edit their addresses
    for shipping and billing purposes.
    """

    class Meta:
        model = Address
        fields = [
            "address_type",
            "first_name",
            "last_name",
            "company",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "phone_number",
            "is_default",
        ]
        widgets = {
            "address_type": forms.Select(
                attrs={"class": "form-select", "aria-label": "Address type"}
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                    "aria-label": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                    "aria-label": "Last name",
                }
            ),
            "company": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company (optional)",
                    "aria-label": "Company",
                }
            ),
            "address_line_1": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Address line 1",
                    "aria-label": "Address line 1",
                }
            ),
            "address_line_2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Address line 2 (optional)",
                    "aria-label": "Address line 2",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                    "aria-label": "City",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State",
                    "aria-label": "State",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Postal code",
                    "aria-label": "Postal code",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Country",
                    "aria-label": "Country",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                    "aria-label": "Phone number",
                }
            ),
            "is_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "aria-label": "Set as default address",
                }
            ),
        }

    def clean_phone_number(self):
        """Validate phone number format."""
        phone_number = self.cleaned_data.get("phone_number")
        if phone_number:
            # Basic phone number validation - should contain only digits, spaces, hyphens, parentheses, and +
            import re
            phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
            if not re.match(phone_pattern, phone_number):
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone_number


class PaymentMethodForm(forms.ModelForm):
    """
    Payment method form for adding payment information.

    This form allows users to add and manage their payment methods
    for checkout and repeat purchases.
    """

    class Meta:
        model = PaymentMethod
        fields = [
            "payment_type",
            "card_brand",
            "card_last_four",
            "expiry_month",
            "expiry_year",
            "is_default",
        ]
        widgets = {
            "payment_type": forms.Select(
                attrs={"class": "form-select", "aria-label": "Payment type"}
            ),
            "card_brand": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Card brand (e.g., Visa, MasterCard)",
                    "aria-label": "Card brand",
                }
            ),
            "card_last_four": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last 4 digits",
                    "maxlength": "4",
                    "aria-label": "Last 4 digits",
                }
            ),
            "expiry_month": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "MM",
                    "maxlength": "2",
                    "aria-label": "Expiry month",
                }
            ),
            "expiry_year": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "YYYY",
                    "maxlength": "4",
                    "aria-label": "Expiry year",
                }
            ),
            "is_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "aria-label": "Set as default payment method",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Make payment_type required
        self.fields["payment_type"].required = True
        self.fields["card_brand"].required = True
        self.fields["card_last_four"].required = True
        self.fields["expiry_month"].required = True
        self.fields["expiry_year"].required = True

    def clean_card_last_four(self):
        """Validate card last four digits."""
        card_last_four = self.cleaned_data.get("card_last_four")
        if card_last_four:
            if not card_last_four.isdigit():
                raise forms.ValidationError(
                    "Card last four digits must contain only numbers."
                )
            if len(card_last_four) != 4:
                raise forms.ValidationError(
                    "Card last four digits must be exactly 4 digits."
                )
        return card_last_four

    def clean_expiry_month(self):
        """Validate expiry month."""
        expiry_month = self.cleaned_data.get("expiry_month")
        if expiry_month:
            if not expiry_month.isdigit():
                raise forms.ValidationError("Expiry month must contain only numbers.")
            month = int(expiry_month)
            if month < 1 or month > 12:
                raise forms.ValidationError("Expiry month must be between 01 and 12.")
        return expiry_month

    def clean_expiry_year(self):
        """Validate expiry year."""
        expiry_year = self.cleaned_data.get("expiry_year")
        if expiry_year:
            if not expiry_year.isdigit():
                raise forms.ValidationError("Expiry year must contain only numbers.")
            year = int(expiry_year)
            current_year = datetime.now().year
            if year < current_year or year > current_year + 20:
                raise forms.ValidationError(
                    f"Expiry year must be between {current_year} and {current_year + 20}."
                )
        return expiry_year

    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()

        # Check if this is a default payment method
        is_default = cleaned_data.get("is_default")

        if is_default and self.user:
            # If setting as default, unset other default payment methods
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(
                is_default=False
            )

        return cleaned_data

    def save(self, commit=True):
        """Save the payment method."""
        payment_method = super().save(commit=False)
        if self.user:
            payment_method.user = self.user

        if commit:
            payment_method.save()

        return payment_method


class CheckoutForm(forms.Form):
    """
    Checkout form for completing purchases.

    This form handles the checkout process including
    address selection, payment method, and order confirmation.
    """

    # Address selection
    shipping_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    billing_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    # Payment method
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.none(),
        required=True,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    # Order options
    use_billing_for_shipping = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "use_billing_for_shipping"}
        ),
    )

    # Additional information
    order_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Special instructions for your order...",
                "rows": 3,
                "maxlength": "500",
            }
        ),
    )

    # Terms and conditions
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "accept_terms"}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        """
        Initialize form with user-specific querysets.

        Args:
            user: The authenticated user
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        # Remove 'instance' from kwargs if present (CreateView passes this)
        kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)

        # Set querysets for user's addresses and payment methods
        self.fields["shipping_address"].queryset = user.addresses.filter(
            address_type__in=["shipping", "both"]
        )
        self.fields["billing_address"].queryset = user.addresses.filter(
            address_type__in=["billing", "both"]
        )
        self.fields["payment_method"].queryset = user.payment_methods.filter(
            is_active=True
        )

    def clean(self):
        """
        Validate form data and ensure proper address selection.

        Returns:
            dict: Cleaned form data
        """
        cleaned_data = super().clean()
        use_billing_for_shipping = cleaned_data.get("use_billing_for_shipping")
        shipping_address = cleaned_data.get("shipping_address")
        billing_address = cleaned_data.get("billing_address")

        # If using billing address for shipping, ensure billing address is selected
        if use_billing_for_shipping and not billing_address:
            raise forms.ValidationError(
                "Please select a billing address to use for shipping."
            )

        # If not using billing for shipping, ensure shipping address is selected
        if not use_billing_for_shipping and not shipping_address:
            raise forms.ValidationError("Please select a shipping address.")

        # Ensure at least one address is selected
        if not shipping_address and not billing_address:
            raise forms.ValidationError("Please select at least one address.")

        return cleaned_data


class CartItemForm(forms.ModelForm):
    """
    Cart item form for updating quantities.

    This form allows users to update quantities of items in their cart.
    """

    class Meta:
        model = CartItem
        fields = ["quantity"]
        widgets = {
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "99",
                    "aria-label": "Quantity",
                }
            )
        }

    def clean_quantity(self):
        """
        Validate quantity is within acceptable range.

        Returns:
            int: Cleaned quantity
        """
        quantity = self.cleaned_data.get("quantity")
        if quantity and (quantity < 1 or quantity > 99):
            raise forms.ValidationError("Quantity must be between 1 and 99.")
        return quantity
