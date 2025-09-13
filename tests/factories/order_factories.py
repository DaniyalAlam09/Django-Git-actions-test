"""
Factory Boy factories for order-related models.
"""

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from store.models import Address, Cart, CartItem, Order, OrderItem, PaymentMethod


class AddressFactory(DjangoModelFactory):
    """Factory for creating Address instances."""

    class Meta:
        model = Address

    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    address_type = factory.Iterator(["shipping", "billing"])
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    company = factory.Faker("company")
    address_line_1 = factory.Faker("street_address")
    address_line_2 = factory.Faker("secondary_address")
    city = factory.Faker("city")
    state = factory.Faker("state_abbr")
    postal_code = factory.Faker("postcode")
    country = factory.Faker("country_code")
    phone_number = factory.Faker("phone_number")
    is_default = factory.Faker("boolean", chance_of_getting_true=30)
    instructions = factory.Faker("text", max_nb_chars=100)


class PaymentMethodFactory(DjangoModelFactory):
    """Factory for creating PaymentMethod instances."""

    class Meta:
        model = PaymentMethod

    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    payment_type = factory.Iterator(
        ["credit_card", "debit_card", "paypal", "bank_transfer"]
    )
    card_number = factory.Faker("credit_card_number")
    cardholder_name = factory.Faker("name")
    expiry_month = factory.Faker("random_int", min=1, max=12)
    expiry_year = factory.Faker("random_int", min=2024, max=2030)
    cvv = factory.Faker("random_int", min=100, max=999)
    billing_address = factory.SubFactory(AddressFactory)
    is_default = factory.Faker("boolean", chance_of_getting_true=20)
    is_verified = factory.Faker("boolean", chance_of_getting_true=90)


class CartFactory(DjangoModelFactory):
    """Factory for creating Cart instances."""

    class Meta:
        model = Cart

    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    session_key = factory.Faker("uuid4")
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class CartItemFactory(DjangoModelFactory):
    """Factory for creating CartItem instances."""

    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory("tests.factories.product_factories.ProductFactory")
    quantity = factory.Faker("random_int", min=1, max=10)
    added_at = factory.Faker("date_time_this_year")

    @factory.post_generation
    def price_at_time(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            self.price_at_time = extracted
        else:
            self.price_at_time = self.product.price


class OrderFactory(DjangoModelFactory):
    """Factory for creating Order instances."""

    class Meta:
        model = Order

    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    order_number = factory.Faker("bothify", text="ORD-########")
    status = factory.Iterator(
        ["pending", "processing", "shipped", "delivered", "cancelled"]
    )
    payment_status = factory.Iterator(["pending", "paid", "failed", "refunded"])
    subtotal = factory.LazyFunction(
        lambda: Decimal(
            f"{factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate()['pydecimal']:.2f}"
        )
    )
    tax_amount = factory.LazyFunction(
        lambda: Decimal(
            f"{factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True).generate()['pydecimal']:.2f}"
        )
    )
    shipping_amount = factory.LazyFunction(
        lambda: Decimal(
            f"{factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True).generate()['pydecimal']:.2f}"
        )
    )
    discount_amount = factory.LazyFunction(
        lambda: Decimal(
            f"{factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True).generate()['pydecimal']:.2f}"
        )
    )
    total_amount = factory.LazyAttribute(
        lambda obj: obj.subtotal
        + obj.tax_amount
        + obj.shipping_amount
        - obj.discount_amount
    )
    shipping_address = factory.SubFactory(AddressFactory, address_type="shipping")
    billing_address = factory.SubFactory(AddressFactory, address_type="billing")
    payment_method = factory.SubFactory(PaymentMethodFactory)
    payment_reference = factory.Faker("bothify", text="PAY-########")
    tracking_number = factory.Faker("bothify", text="TRK-########")
    estimated_delivery = factory.Faker("future_date", end_date="+30d")
    notes = factory.Faker("text", max_nb_chars=200)
    created_at = factory.Faker("date_time_this_year")


class OrderItemFactory(DjangoModelFactory):
    """Factory for creating OrderItem instances."""

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory("tests.factories.product_factories.ProductFactory")
    quantity = factory.Faker("random_int", min=1, max=5)
    unit_price = factory.LazyFunction(
        lambda: Decimal(
            f"{factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate()['pydecimal']:.2f}"
        )
    )
    total_price = factory.LazyAttribute(lambda obj: obj.unit_price * obj.quantity)


class PendingOrderFactory(OrderFactory):
    """Factory for creating pending orders."""

    status = "pending"
    payment_status = "pending"


class CompletedOrderFactory(OrderFactory):
    """Factory for creating completed orders."""

    status = "delivered"
    payment_status = "paid"


class CancelledOrderFactory(OrderFactory):
    """Factory for creating cancelled orders."""

    status = "cancelled"
    payment_status = "refunded"
