from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from .forms import CustomUserCreationForm, ProfileForm


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Account created! You can now log in."

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("profile")
    success_message = "Profile updated."

    def get_object(self):
        return self.request.user

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)