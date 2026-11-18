from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from accounts.mixins import RoleRequiredMixin
from accounts.models import CustomUser

Role = CustomUser.Role


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        target = {
            Role.ADMIN: "admin_dashboard",
            Role.SELLER: "seller_dashboard",
            Role.BUYER: "buyer_dashboard",
        }[request.user.role]
        return redirect(target)


class BuyerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_role = Role.BUYER
    template_name = "dashboard/buyer.html"


class SellerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_role = Role.SELLER
    template_name = "dashboard/seller.html"


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    allowed_role = Role.ADMIN
    template_name = "dashboard/admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = CustomUser.objects.count()
        context["buyer_count"] = CustomUser.objects.filter(role=Role.BUYER).count()
        context["seller_count"] = CustomUser.objects.filter(role=Role.SELLER).count()
        context["suspended_count"] = CustomUser.objects.filter(is_active=False).count()
        return context