from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from accounts.mixins import RoleRequiredMixin
from accounts.models import CustomUser
from listings.models import Listing

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_listings"] = (
            Listing.objects.filter(
                status=Listing.Status.PUBLISHED, seller__is_active=True
            )
            .select_related("seller")
            .prefetch_related("photos")[:6]
        )
        return context


class SellerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_role = Role.SELLER
    template_name = "dashboard/seller.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mine = Listing.objects.filter(seller=self.request.user)
        context["draft_count"] = mine.filter(status=Listing.Status.DRAFT).count()
        context["published_count"] = mine.filter(
            status=Listing.Status.PUBLISHED
        ).count()
        context["sold_count"] = mine.filter(status=Listing.Status.SOLD).count()
        context["recent_listings"] = mine.prefetch_related("photos")[:3]
        return context


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    allowed_role = Role.ADMIN
    template_name = "dashboard/admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = CustomUser.objects.count()
        context["buyer_count"] = CustomUser.objects.filter(role=Role.BUYER).count()
        context["seller_count"] = CustomUser.objects.filter(role=Role.SELLER).count()
        context["suspended_count"] = CustomUser.objects.filter(is_active=False).count()
        context["listing_count"] = Listing.objects.count()
        context["published_listing_count"] = Listing.objects.filter(
            status=Listing.Status.PUBLISHED
        ).count()
        return context