from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

MAX_PHOTOS = 5


class Listing(models.Model):
    """A women's secondhand clothing item posted by a seller."""

    class Category(models.TextChoices):
        TOPS = "TOPS", "Tops"
        DRESSES = "DRESSES", "Dresses"
        BOTTOMS = "BOTTOMS", "Bottoms (pants, skirts, shorts)"
        OUTERWEAR = "OUTERWEAR", "Outerwear"
        ACTIVEWEAR = "ACTIVEWEAR", "Activewear"
        SLEEPWEAR = "SLEEPWEAR", "Sleepwear"
        OTHER = "OTHER", "Other"

    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        FREE = "FREE", "Free size"

    class Condition(models.TextChoices):
        NEW = "NEW", "Brand new (with tags)"
        LIKE_NEW = "LIKE_NEW", "Like new"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair (visible wear)"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        SOLD = "SOLD", "Sold"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=12, choices=Category.choices)
    description = models.TextField()
    size = models.CharField(max_length=5, choices=Size.choices)
    condition = models.CharField(max_length=10, choices=Condition.choices)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("listing_detail", args=[self.pk])

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_sold(self):
        return self.status == self.Status.SOLD

    @property
    def cover_photo(self):
        return self.photos.first()


class ListingPhoto(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="listings/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "pk"]

    def __str__(self):
        return f"Photo of {self.listing.title}"