from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[("BUYER", "Buyer (I want to shop)"),
                 ("SELLER", "Seller (I sell ukay-ukay)")]
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name",
                  "contact_number", "barangay", "city", "role", "shop_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("email", "first_name", "last_name"):
            self.fields[name].required = True
        self.fields["username"].help_text = (
            "Use letters, numbers, and @ . + - _ only. No spaces."
        )
        self.fields["username"].error_messages["unique"] = (
            "That username is already taken. Choose another."
        )
        self.fields["email"].error_messages["unique"] = (
            "An account with this email already exists."
        )
        self.fields["shop_name"].label = "Shop name (sellers only)"

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == "SELLER" and not cleaned.get("shop_name"):
            self.add_error("shop_name", "Sellers must enter a shop name.")
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "contact_number",
                  "barangay", "city", "shop_name", "bio", "profile_photo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].error_messages["unique"] = (
            "An account with this email already exists."
        )
        if self.instance.role != CustomUser.Role.SELLER:
            del self.fields["shop_name"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if CustomUser.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email