"""
Django management command to download and save product images.
"""

import io
import os

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from store.models import Product


class Command(BaseCommand):
    help = "Download and save product images from URLs"

    def handle(self, *args, **options):
        self.stdout.write("Downloading product images...")

        # Image URLs for each product
        image_mapping = {
            "Sony WH-1000XM4 Wireless Headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop",
            "Apple Watch Series 9": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=500&h=500&fit=crop",
            "Patagonia Organic Cotton T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop",
            "Nike Air Zoom Pegasus 40": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
            "Succulent Garden Starter Kit": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&h=500&fit=crop",
            "Python Programming Complete Guide": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop",
            "Lululemon Reversible Yoga Mat": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop",
            "Amazon Echo Dot (5th Gen)": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop",
            "Levi's 501 Original Jeans": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500&h=500&fit=crop",
            "Fiskars Garden Tool Set": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&h=500&fit=crop",
            "MacBook Air M2": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&h=500&fit=crop",
            "Dyson V15 Detect Cordless Vacuum": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop",
        }

        for product_name, image_url in image_mapping.items():
            try:
                product = Product.objects.get(name=product_name)

                # Skip if product already has an image
                if product.main_image:
                    self.stdout.write(
                        f"Product {product_name} already has an image, skipping..."
                    )
                    continue

                # Download image
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()

                # Process image
                image = Image.open(io.BytesIO(response.content))

                # Convert to RGB if necessary
                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGB")

                # Resize to 500x500
                image = image.resize((500, 500), Image.Resampling.LANCZOS)

                # Save to BytesIO
                img_io = io.BytesIO()
                image.save(img_io, format="JPEG", quality=85)
                img_io.seek(0)

                # Create filename
                filename = f"{product.slug}.jpg"

                # Save to product
                product.main_image.save(
                    filename, ContentFile(img_io.getvalue()), save=True
                )

                self.stdout.write(f"Downloaded and saved image for: {product_name}")

            except Product.DoesNotExist:
                self.stdout.write(f"Product {product_name} not found, skipping...")
            except Exception as e:
                self.stdout.write(
                    f"Error downloading image for {product_name}: {str(e)}"
                )

        self.stdout.write(
            self.style.SUCCESS("Successfully downloaded all product images!")
        )
