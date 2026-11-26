from django.urls import path

from . import views

urlpatterns = [
    path("listings/mine/", views.SellerListingListView.as_view(), name="my_listings"),
    path("listings/new/", views.ListingCreateView.as_view(), name="listing_create"),
    path("listings/<int:pk>/", views.ListingDetailView.as_view(), name="listing_detail"),
    path("listings/<int:pk>/edit/", views.ListingUpdateView.as_view(), name="listing_edit"),
    path("listings/<int:pk>/delete/", views.ListingDeleteView.as_view(), name="listing_delete"),
    path(
        "listings/<int:pk>/<str:action>/",
        views.ListingStatusView.as_view(),
        name="listing_status",
    ),
]