from django import forms

from .models import MAX_PHOTOS, Listing, ListingPhoto

MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB per photo


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """An ImageField that accepts several files at once."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one(item, initial) for item in data if item]
        return [clean_one(data, initial)] if data else []


class ListingForm(forms.ModelForm):
    photos = MultipleImageField(
        required=False,
        label="Add photos",
        help_text=f"Up to {MAX_PHOTOS} photos per listing, 5 MB each (JPG or PNG).",
    )
    remove_photos = forms.ModelMultipleChoiceField(
        queryset=ListingPhoto.objects.none(), required=False
    )

    class Meta:
        model = Listing
        fields = ("title", "category", "description", "size", "condition", "price")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }
        labels = {"price": "Price (₱)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "Select a category")] + list(
            Listing.Category.choices
        )
        self.fields["size"].choices = [("", "Select a size")] + list(
            Listing.Size.choices
        )
        self.fields["condition"].choices = [("", "Select a condition")] + list(
            Listing.Condition.choices
        )
        self.fields["price"].error_messages["min_value"] = (
            "Price must be greater than ₱0."
        )
        if self.instance.pk:
            self.fields["remove_photos"].queryset = self.instance.photos.all()
        else:
            del self.fields["remove_photos"]

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters.")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 10:
            raise forms.ValidationError(
                "Please describe the item in at least 10 characters."
            )
        return description

    def clean_photos(self):
        files = self.cleaned_data.get("photos") or []
        for photo in files:
            if photo.size > MAX_PHOTO_BYTES:
                raise forms.ValidationError(
                    f"“{photo.name}” is larger than 5 MB."
                )
        return files

    def clean(self):
        cleaned = super().clean()
        new_files = cleaned.get("photos") or []
        existing = self.instance.photos.count() if self.instance.pk else 0
        removed = len(cleaned.get("remove_photos") or [])
        if existing - removed + len(new_files) > MAX_PHOTOS:
            self.add_error(
                "photos", f"A listing can have at most {MAX_PHOTOS} photos."
            )
        return cleaned

    def save_photos(self, listing):
        """Delete ticked photos and store newly uploaded ones."""
        for photo in self.cleaned_data.get("remove_photos") or []:
            photo.image.delete(save=False)
            photo.delete()
        for image in self.cleaned_data.get("photos") or []:
            ListingPhoto.objects.create(listing=listing, image=image)

class ListingFilterForm(forms.Form):
    SORT_CHOICES = [
        ("newest", "Newest first"),
        ("oldest", "Oldest first"),
        ("price_low", "Price: low to high"),
        ("price_high", "Price: high to low"),
    ]

    q = forms.CharField(required=False, label="Search")
    category = forms.ChoiceField(
        required=False, choices=[("", "All categories")] + Listing.Category.choices
    )
    size = forms.ChoiceField(
        required=False, choices=[("", "All sizes")] + Listing.Size.choices
    )
    condition = forms.ChoiceField(
        required=False, choices=[("", "Any condition")] + Listing.Condition.choices
    )
    min_price = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label="Min ₱"
    )
    max_price = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label="Max ₱"
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)

    def clean(self):
        cleaned = super().clean()
        low, high = cleaned.get("min_price"), cleaned.get("max_price")
        if low is not None and high is not None and low > high:
            self.add_error(
                "max_price", "Maximum price cannot be lower than the minimum."
            )
        return cleaned