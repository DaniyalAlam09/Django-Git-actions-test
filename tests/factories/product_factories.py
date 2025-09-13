"""
Factory Boy factories for product-related models.
"""

import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from store.models import Category, Product, ProductTag, ProductReview


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances."""
    
    class Meta:
        model = Category
    
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True
    sort_order = factory.Sequence(lambda n: n)
    
    @factory.post_generation
    def children(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for child in extracted:
            self.children.add(child)


class ProductTagFactory(DjangoModelFactory):
    """Factory for creating ProductTag instances."""
    
    class Meta:
        model = ProductTag
    
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=100)
    color = factory.Faker("hex_color")
    is_active = True


class ProductFactory(DjangoModelFactory):
    """Factory for creating Product instances."""
    
    class Meta:
        model = Product
    
    name = factory.Faker("sentence", nb_words=3)
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=500)
    short_description = factory.Faker("text", max_nb_chars=100)
    price = factory.LazyFunction(lambda: Decimal(f"{factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate()['pydecimal']:.2f}"))
    sale_price = factory.LazyFunction(lambda: Decimal(f"{factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate()['pydecimal']:.2f}"))
    stock_quantity = factory.Faker("random_int", min=0, max=100)
    is_in_stock = factory.LazyAttribute(lambda obj: obj.stock_quantity > 0)
    low_stock_threshold = factory.Faker("random_int", min=1, max=10)
    category = factory.SubFactory(CategoryFactory)
    main_image = factory.django.ImageField(color="red")
    is_active = True
    is_featured = factory.Faker("boolean", chance_of_getting_true=20)
    is_bestseller = factory.Faker("boolean", chance_of_getting_true=15)
    view_count = factory.Faker("random_int", min=0, max=1000)
    weight = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    dimensions_length = factory.Faker("pydecimal", left_digits=2, right_digits=1, positive=True)
    dimensions_width = factory.Faker("pydecimal", left_digits=2, right_digits=1, positive=True)
    dimensions_height = factory.Faker("pydecimal", left_digits=2, right_digits=1, positive=True)
    sku = factory.Faker("bothify", text="SKU-####-???")
    meta_title = factory.LazyAttribute(lambda obj: f"{obj.name} - E-commerce Store")
    meta_description = factory.LazyAttribute(lambda obj: f"Buy {obj.name} online. {obj.short_description}")
    meta_keywords = factory.LazyAttribute(lambda obj: f"{obj.name}, {obj.category.name}, online shopping")
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add 1-3 random tags
            num_tags = factory.Faker("random_int", min=1, max=3).generate()
            for _ in range(num_tags):
                tag = ProductTagFactory()
                self.tags.add(tag)


class FeaturedProductFactory(ProductFactory):
    """Factory for creating featured products."""
    
    is_featured = True
    is_bestseller = factory.Faker("boolean", chance_of_getting_true=50)


class BestsellerProductFactory(ProductFactory):
    """Factory for creating bestseller products."""
    
    is_bestseller = True
    is_featured = factory.Faker("boolean", chance_of_getting_true=30)


class OutOfStockProductFactory(ProductFactory):
    """Factory for creating out-of-stock products."""
    
    stock_quantity = 0
    is_in_stock = False


class ProductReviewFactory(DjangoModelFactory):
    """Factory for creating ProductReview instances."""
    
    class Meta:
        model = ProductReview
    
    user = factory.SubFactory("tests.factories.user_factories.UserFactory")
    product = factory.SubFactory(ProductFactory)
    rating = factory.Faker("random_int", min=1, max=5)
    title = factory.Faker("sentence", nb_words=4)
    comment = factory.Faker("text", max_nb_chars=300)
    is_approved = factory.Faker("boolean", chance_of_getting_true=90)
    helpful_votes = factory.Faker("random_int", min=0, max=50)
    
    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for image in extracted:
            self.images.add(image)
