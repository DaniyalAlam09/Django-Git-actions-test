# 🧪 Testing Guide

This document provides comprehensive information about testing the Django e-commerce application, including unit tests, integration tests, and end-to-end tests.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Test Configuration](#test-configuration)
- [Writing Tests](#writing-tests)
- [Test Data](#test-data)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The testing suite includes:

- **Unit Tests**: Test individual components (models, views, forms, utilities)
- **Integration Tests**: Test component interactions and API endpoints
- **E2E Tests**: Test complete user journeys using Selenium
- **Performance Tests**: Test application performance under load
- **Security Tests**: Test security vulnerabilities and best practices

## 🏗️ Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_runner.py             # Custom test runner
├── unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_models.py         # Model tests
│   ├── test_views.py          # View tests
│   └── test_forms.py          # Form tests
├── integration/               # Integration tests
│   ├── __init__.py
│   ├── test_api_endpoints.py  # API endpoint tests
│   └── test_workflows.py      # Complete workflow tests
├── e2e/                       # End-to-end tests
│   ├── __init__.py
│   └── test_user_journeys.py  # User journey tests
├── fixtures/                  # Test fixtures
│   ├── __init__.py
│   ├── sample_data.json       # Sample test data
│   └── test_images.py         # Test image utilities
└── factories/                 # Factory Boy factories
    ├── __init__.py
    ├── user_factories.py      # User-related factories
    ├── product_factories.py   # Product-related factories
    ├── order_factories.py     # Order-related factories
    └── wishlist_factories.py  # Wishlist-related factories
```

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose

# Run in parallel
python run_tests.py --parallel
```

### Specific Test Types

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# E2E tests only
python run_tests.py --e2e

# Specific test file
python run_tests.py --test tests/unit/test_models.py
```

### Quality Checks

```bash
# Run all quality checks
python run_tests.py --quality

# Individual quality checks
python run_tests.py --lint        # Code linting
python run_tests.py --type-check  # Type checking
python run_tests.py --security    # Security check
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run with markers
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=store --cov=ecommerce

# Run in parallel
pytest -n auto
```

### Using Django Test Runner

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test store

# Run specific test
python manage.py test store.tests.test_models

# Run with parallel execution
python manage.py test --parallel=4
```

## 🔧 Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **Models**: Test model methods, validation, and business logic
- **Views**: Test view behavior, context data, and response handling
- **Forms**: Test form validation, field behavior, and save methods
- **Serializers**: Test API serialization and deserialization
- **Utilities**: Test helper functions and custom methods

**Example Unit Test:**
```python
@pytest.mark.django_db
def test_product_creation(category):
    """Test basic product creation."""
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="Test description",
        price=Decimal("99.99"),
        category=category,
    )
    assert product.name == "Test Product"
    assert product.price == Decimal("99.99")
    assert str(product) == "Test Product"
```

### Integration Tests

Integration tests focus on testing component interactions:

- **API Endpoints**: Test REST API functionality
- **Database Operations**: Test complex database queries and transactions
- **External Services**: Test integrations with external services
- **Complete Workflows**: Test end-to-end business processes

**Example Integration Test:**
```python
@pytest.mark.django_db
def test_cart_workflow(authenticated_client, test_user, product):
    """Test complete shopping cart workflow."""
    # Add product to cart
    url = reverse("store:add_to_cart")
    data = {"product_id": product.id, "quantity": 2}
    response = authenticated_client.post(url, data)
    assert response.status_code == 200
    
    # Verify cart was created
    cart = Cart.objects.get(user=test_user)
    assert cart.items.count() == 1
```

### E2E Tests

End-to-end tests simulate real user interactions:

- **User Journeys**: Test complete user workflows
- **Cross-browser Testing**: Test compatibility across browsers
- **Mobile Testing**: Test responsive design and mobile functionality
- **Performance Testing**: Test application performance under load

**Example E2E Test:**
```python
@pytest.mark.e2e
@pytest.mark.django_db
def test_new_user_journey(selenium_driver, live_server_url, category, product):
    """Test complete journey from registration to order completion."""
    driver = selenium_driver
    driver.get(f"{live_server_url}/")
    
    # Navigate to registration
    driver.find_element(By.LINK_TEXT, "Sign Up").click()
    
    # Fill registration form
    driver.find_element(By.NAME, "username").send_keys("newuser")
    # ... rest of the test
```

## ⚙️ Test Configuration

### Pytest Configuration

The `pytest.ini` file contains pytest configuration:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = ecommerce.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --verbose
    --cov=store
    --cov=ecommerce
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_model_method():
    """Unit test for model method."""
    pass

@pytest.mark.integration
def test_api_endpoint():
    """Integration test for API endpoint."""
    pass

@pytest.mark.e2e
def test_user_journey():
    """E2E test for user journey."""
    pass

@pytest.mark.slow
def test_performance():
    """Slow performance test."""
    pass
```

### Test Fixtures

Use fixtures for consistent test data:

```python
@pytest.fixture
def test_user():
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def product(category):
    """Create a test product."""
    return Product.objects.create(
        name="Test Product",
        description="Test description",
        price=Decimal("99.99"),
        category=category
    )
```

## ✍️ Writing Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use descriptive names that explain what is being tested

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_product_price_calculation(category):
    """Test product price calculation with sale price."""
    # Arrange
    product = Product.objects.create(
        name="Test Product",
        price=Decimal("100.00"),
        sale_price=Decimal("80.00"),
        category=category
    )
    
    # Act
    current_price = product.get_current_price()
    discount = product.get_discount_percentage()
    
    # Assert
    assert current_price == Decimal("80.00")
    assert discount == 20.0
```

### Test Data Management

Use Factory Boy for creating test data:

```python
from tests.factories import ProductFactory, CategoryFactory

def test_product_list():
    """Test product list view."""
    # Create test data
    category = CategoryFactory()
    products = ProductFactory.create_batch(5, category=category)
    
    # Test the view
    response = client.get('/products/')
    assert response.status_code == 200
    assert len(response.context['products']) == 5
```

### Mocking External Services

Mock external services to avoid dependencies:

```python
from unittest.mock import patch

@patch('store.services.payment_service.process_payment')
def test_checkout_with_payment(mock_payment):
    """Test checkout process with mocked payment."""
    mock_payment.return_value = {'success': True, 'transaction_id': '123'}
    
    # Test checkout
    response = client.post('/checkout/', checkout_data)
    assert response.status_code == 200
    mock_payment.assert_called_once()
```

## 📊 Test Data

### Sample Data

Use the provided sample data fixtures:

```python
# Load sample data
python manage.py loaddata tests/fixtures/sample_data.json
```

### Factory Boy

Use factories for dynamic test data:

```python
from tests.factories import ProductFactory, UserFactory

# Create single instance
product = ProductFactory()

# Create multiple instances
products = ProductFactory.create_batch(10)

# Create with specific attributes
product = ProductFactory(name="Custom Product", price=Decimal("50.00"))
```

### Test Images

Use the test image utilities:

```python
from tests.fixtures.test_images import create_test_image

# Create test image
image = create_test_image("test.jpg", (100, 100), "blue")

# Use in test
product = ProductFactory(main_image=image)
```

## 🔄 CI/CD Integration

### GitHub Actions

The CI/CD pipeline automatically runs tests on:

- Code push to main branch
- Pull request creation
- Manual workflow dispatch

### Test Stages

1. **Code Quality**: Linting, formatting, type checking
2. **Unit Tests**: Fast, isolated component tests
3. **Integration Tests**: Component interaction tests
4. **E2E Tests**: Complete user journey tests (optional)
5. **Security Tests**: Vulnerability scanning
6. **Performance Tests**: Load and performance testing

### Coverage Requirements

- Minimum coverage: 80%
- Coverage reports generated in HTML and XML formats
- Coverage uploaded as artifacts for review

## 📚 Best Practices

### Test Organization

- Group related tests in classes
- Use descriptive test names
- Keep tests focused and simple
- Avoid test interdependencies

### Test Data

- Use factories for dynamic data
- Use fixtures for static data
- Clean up test data after tests
- Use realistic test data

### Performance

- Use database transactions for fast tests
- Mock external services
- Use parallel execution when possible
- Avoid unnecessary database queries

### Maintenance

- Keep tests up to date with code changes
- Refactor tests when refactoring code
- Remove obsolete tests
- Document complex test scenarios

## 🐛 Troubleshooting

### Common Issues

**Test Database Issues:**
```bash
# Reset test database
python manage.py test --keepdb --debug-mode
```

**Import Errors:**
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Selenium Issues:**
```bash
# Install Chrome driver
sudo apt-get install chromium-chromedriver
```

**Coverage Issues:**
```bash
# Clear coverage data
coverage erase
coverage run --source='.' manage.py test
coverage report
```

### Debug Mode

Run tests in debug mode for detailed output:

```bash
python run_tests.py --verbose --debug
```

### Test Isolation

Ensure tests don't interfere with each other:

```python
@pytest.mark.django_db(transaction=True)
def test_database_transaction():
    """Test that requires database transaction."""
    pass
```

## 📈 Test Metrics

### Coverage Goals

- **Overall Coverage**: > 80%
- **Model Coverage**: > 90%
- **View Coverage**: > 85%
- **Form Coverage**: > 80%
- **API Coverage**: > 85%

### Performance Goals

- **Unit Tests**: < 1 second per test
- **Integration Tests**: < 5 seconds per test
- **E2E Tests**: < 30 seconds per test
- **Total Test Suite**: < 10 minutes

### Quality Goals

- **Zero Linting Errors**: All code passes linting
- **Zero Type Errors**: All code passes type checking
- **Zero Security Issues**: All security checks pass
- **Zero Test Failures**: All tests pass consistently

---

## 🎯 Quick Reference

### Running Tests
```bash
python run_tests.py                    # All tests
python run_tests.py --unit            # Unit tests
python run_tests.py --integration     # Integration tests
python run_tests.py --e2e             # E2E tests
python run_tests.py --coverage        # With coverage
python run_tests.py --verbose         # Verbose output
python run_tests.py --parallel        # Parallel execution
```

### Test Markers
```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e          # E2E tests
@pytest.mark.slow         # Slow tests
@pytest.mark.api          # API tests
@pytest.mark.auth         # Authentication tests
```

### Useful Commands
```bash
pytest -m unit            # Run unit tests
pytest -m integration     # Run integration tests
pytest -m e2e            # Run E2E tests
pytest -k "test_product"  # Run tests matching pattern
pytest --lf              # Run last failed tests
pytest --ff              # Run failed tests first
```

For more information, see the [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/) and [Pytest Documentation](https://docs.pytest.org/).
