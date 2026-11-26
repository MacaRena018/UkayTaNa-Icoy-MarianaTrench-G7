from django.contrib import admin

from .models import Listing, ListingPhoto


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "category", "size", "price", "status", "created_at")
    list_filter = ("status", "category", "condition")
    search_fields = ("title", "seller__username")
    inlines = [ListingPhotoInline]