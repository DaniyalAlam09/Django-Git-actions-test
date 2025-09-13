"""
Locust performance test file for the e-commerce application.

This file defines the load testing scenarios for the e-commerce application
including user journeys, API endpoints, and performance benchmarks.
"""

import random

from locust import HttpUser, between, task
from locust.exception import StopUser


class ECommerceUser(HttpUser):
    """Simulates a typical e-commerce user behavior."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts."""
        self.login()

    def login(self):
        """Simulate user login."""
        # This would need to be implemented based on your auth system
        # For now, we'll just simulate a successful login
        pass

    @task(3)
    def view_homepage(self):
        """View the homepage - most common action."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage returned {response.status_code}")

    @task(2)
    def view_products(self):
        """View product listing page."""
        with self.client.get("/products/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Products page returned {response.status_code}")

    @task(2)
    def search_products(self):
        """Search for products."""
        search_terms = ["laptop", "phone", "book", "shirt", "shoes", "watch"]
        search_term = random.choice(search_terms)

        with self.client.get(
            f"/search/?search={search_term}", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search returned {response.status_code}")

    @task(1)
    def view_product_detail(self):
        """View a specific product detail page."""
        # This would need to be implemented with actual product IDs
        # For now, we'll simulate with a random product ID
        product_id = random.randint(1, 100)

        with self.client.get(
            f"/product/{product_id}/", catch_response=True
        ) as response:
            if response.status_code in [
                200,
                404,
            ]:  # 404 is acceptable for non-existent products
                response.success()
            else:
                response.failure(f"Product detail returned {response.status_code}")

    @task(1)
    def view_categories(self):
        """View category pages."""
        categories = ["electronics", "clothing", "books", "home", "sports"]
        category = random.choice(categories)

        with self.client.get(f"/category/{category}/", catch_response=True) as response:
            if response.status_code in [
                200,
                404,
            ]:  # 404 is acceptable for non-existent categories
                response.success()
            else:
                response.failure(f"Category page returned {response.status_code}")

    @task(1)
    def api_health_check(self):
        """Check API health endpoint."""
        with self.client.get("/api/health/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API health check returned {response.status_code}")

    @task(1)
    def api_products(self):
        """Test API products endpoint."""
        with self.client.get("/api/products/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API products returned {response.status_code}")


class APIUser(HttpUser):
    """Simulates API-only usage patterns."""

    wait_time = between(0.5, 2)

    @task(5)
    def get_products(self):
        """Get products via API."""
        with self.client.get("/api/products/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API products returned {response.status_code}")

    @task(3)
    def get_categories(self):
        """Get categories via API."""
        with self.client.get("/api/categories/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API categories returned {response.status_code}")

    @task(2)
    def search_products(self):
        """Search products via API."""
        search_terms = ["laptop", "phone", "book", "shirt", "shoes"]
        search_term = random.choice(search_terms)

        with self.client.get(
            f"/api/products/?search={search_term}", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API search returned {response.status_code}")

    @task(1)
    def get_product_detail(self):
        """Get product detail via API."""
        product_id = random.randint(1, 100)

        with self.client.get(
            f"/api/products/{product_id}/", catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"API product detail returned {response.status_code}")


class HeavyLoadUser(HttpUser):
    """Simulates heavy load scenarios."""

    wait_time = between(0.1, 0.5)  # Very fast requests

    @task(10)
    def rapid_requests(self):
        """Make rapid requests to test system stability."""
        endpoints = ["/", "/products/", "/api/products/", "/api/health/"]
        endpoint = random.choice(endpoints)

        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Rapid request to {endpoint} returned {response.status_code}"
                )

    @task(5)
    def concurrent_searches(self):
        """Simulate concurrent search operations."""
        search_terms = [
            "laptop",
            "phone",
            "book",
            "shirt",
            "shoes",
            "watch",
            "bag",
            "hat",
        ]
        search_term = random.choice(search_terms)

        with self.client.get(
            f"/search/?search={search_term}", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Concurrent search returned {response.status_code}")


# Configuration for different test scenarios
class ECommerceUserScenario(ECommerceUser):
    """Standard e-commerce user scenario."""

    weight = 70  # 70% of users


class APIUserScenario(APIUser):
    """API-focused user scenario."""

    weight = 20  # 20% of users


class HeavyLoadScenario(HeavyLoadUser):
    """Heavy load scenario."""

    weight = 10  # 10% of users
