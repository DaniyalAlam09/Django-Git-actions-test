"""
URL configuration for ecommerce project.

This file contains the main URL patterns for the e-commerce application,
including admin interface, store app, and monitoring endpoints.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # Store application URLs
    path("", include("store.urls")),
    # Health check endpoint for monitoring (simple view)
    path("health/", lambda request: HttpResponse("OK"), name="health_check"),
    # Prometheus metrics endpoint
    path("", include("django_prometheus.urls")),
    # API endpoints
    path("api/", include("store.api_urls", namespace="api")),
    # Redirect root to store
    path("", RedirectView.as_view(pattern_name="store:product_list"), name="home"),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site configuration
admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Admin Portal"
admin.site.index_title = "Welcome to E-Commerce Administration"
