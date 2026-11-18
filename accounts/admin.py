from django.contrib import admin

fieldsets = UserAdmin.fieldsets + (
    ("UkayTaNa", {"fields": ("role", "contact_number", "barangay",
                             "city", "shop_name", "bio", "profile_photo")}),
)
