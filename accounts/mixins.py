from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_role = None

    def test_func(self):
        return self.request.user.role == self.allowed_role

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You are not allowed to open that page.")
            return redirect("dashboard")
        return super().handle_no_permission()