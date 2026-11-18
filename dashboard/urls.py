from django.urls import path
from .views import (DashboardRedirectView, BuyerDashboardView,
                    SellerDashboardView, AdminDashboardView)

urlpatterns = [
    path("", DashboardRedirectView.as_view(), name="dashboard"),
    path("buyer/", BuyerDashboardView.as_view(), name="buyer_dashboard"),
    path("seller/", SellerDashboardView.as_view(), name="seller_dashboard"),
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
]