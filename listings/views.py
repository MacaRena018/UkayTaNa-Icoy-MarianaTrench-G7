from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import CustomUser

from .forms import ListingFilterForm, ListingForm
from .models import Listing

Role = CustomUser.Role
Status = Listing.Status


def _with_photos(queryset):
    return queryset.select_related("seller").prefetch_related("photos")


class ListingDetailView(LoginRequiredMixin, DetailView):
    template_name = "listings/listing_detail.html"
    context_object_name = "listing"

    def get_queryset(self):
        return _with_photos(Listing.objects.all())

    def get_object(self, queryset=None):
        listing = super().get_object(queryset)
        user = self.request.user
        is_public = listing.is_published and listing.seller.is_active
        if not (is_public or listing.seller_id == user.pk or user.role == Role.ADMIN):
            raise Http404("Listing not found.")
        return listing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = self.object.seller_id == self.request.user.pk
        return context


class SellerListingListView(RoleRequiredMixin, ListView):
    """Read: a seller's own listings, filterable by status."""

    allowed_role = Role.SELLER
    template_name = "listings/my_listings.html"
    context_object_name = "listings"
    paginate_by = 12

    def get_queryset(self):
        queryset = _with_photos(Listing.objects.filter(seller=self.request.user))
        self.current_status = self.request.GET.get("status", "")
        if self.current_status in Status.values:
            queryset = queryset.filter(status=self.current_status)
        else:
            self.current_status = ""
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = dict(
            Listing.objects.filter(seller=self.request.user)
            .order_by()
            .values_list("status")
            .annotate(total=Count("pk"))
        )
        context["current_status"] = self.current_status
        context["status_tabs"] = [
            ("", "All", sum(counts.values())),
            (Status.DRAFT, "Drafts", counts.get(Status.DRAFT, 0)),
            (Status.PUBLISHED, "Published", counts.get(Status.PUBLISHED, 0)),
            (Status.SOLD, "Sold", counts.get(Status.SOLD, 0)),
        ]
        return context


class ListingSaveMixin:
    """Shared save logic for create and update (listing + photos together)."""

    form_class = ListingForm
    template_name = "listings/listing_form.html"
    success_url = reverse_lazy("my_listings")

    def form_valid(self, form):
        form.instance.seller = self.request.user
        with transaction.atomic():
            self.object = form.save()
            form.save_photos(self.object)

        listing = self.object
        wants_publish = self.request.POST.get("action") == "publish"
        if wants_publish and listing.is_draft:
            if listing.photos.exists():
                listing.status = Status.PUBLISHED
                listing.save(update_fields=["status", "updated_at"])
                messages.success(
                    self.request, f"“{listing.title}” is now published."
                )
            else:
                messages.warning(
                    self.request,
                    "Saved as a draft. Add at least one photo before publishing.",
                )
        else:
            messages.success(self.request, f"“{listing.title}” was saved.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)


class ListingCreateView(ListingSaveMixin, RoleRequiredMixin, CreateView):
    allowed_role = Role.SELLER


class ListingUpdateView(ListingSaveMixin, RoleRequiredMixin, UpdateView):
    allowed_role = Role.SELLER

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == Role.SELLER:
            listing = Listing.objects.filter(
                pk=kwargs["pk"], seller=request.user
            ).first()
            if listing and listing.is_sold:
                messages.error(request, "Sold listings can no longer be edited.")
                return redirect("my_listings")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Sellers can only ever reach their own listings (others -> 404).
        return Listing.objects.filter(seller=self.request.user).prefetch_related(
            "photos"
        )


class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete: the owner, or an administrator."""

    template_name = "listings/listing_confirm_delete.html"
    context_object_name = "listing"

    def test_func(self):
        return self.request.user.role in (Role.SELLER, Role.ADMIN)

    def get_queryset(self):
        if self.request.user.role == Role.ADMIN:
            return Listing.objects.select_related("seller")
        return Listing.objects.filter(seller=self.request.user)

    def get_success_url(self):
        if self.request.user.role == Role.ADMIN:
            return reverse("admin_listings")
        return reverse("my_listings")

    def form_valid(self, form):
        listing = self.object
        title = listing.title
        for photo in listing.photos.all():
            photo.image.delete(save=False)
        listing.delete()
        messages.success(self.request, f"“{title}” was deleted.")
        return redirect(self.get_success_url())


class ListingStatusView(LoginRequiredMixin, View):
    """Update status: publish / unpublish / mark sold (POST only)."""

    http_method_names = ["post"]
    SELLER_ACTIONS = {"publish", "unpublish", "sold"}
    ADMIN_ACTIONS = {"unpublish"}

    def post(self, request, pk, action):
        listing = get_object_or_404(Listing, pk=pk)
        user = request.user
        is_owner = listing.seller_id == user.pk
        is_admin = user.role == Role.ADMIN

        if is_owner and user.role == Role.SELLER:
            allowed = self.SELLER_ACTIONS
        elif is_admin:
            allowed = self.ADMIN_ACTIONS
        else:
            raise Http404("Listing not found.")
        if action not in allowed:
            raise PermissionDenied

        self.apply(request, listing, action)
        return redirect(self.next_url(request, is_admin and not is_owner))

    def apply(self, request, listing, action):
        if listing.is_sold:
            messages.error(request, "Sold listings can no longer be changed.")
        elif action == "publish":
            if not listing.is_draft:
                messages.error(request, "Only draft listings can be published.")
            elif not listing.photos.exists():
                messages.error(
                    request, "Add at least one photo before publishing this listing."
                )
            else:
                listing.status = Status.PUBLISHED
                listing.save(update_fields=["status", "updated_at"])
                messages.success(request, f"“{listing.title}” is now published.")
        elif action == "unpublish":
            if not listing.is_published:
                messages.error(request, "Only published listings can be unpublished.")
            else:
                listing.status = Status.DRAFT
                listing.save(update_fields=["status", "updated_at"])
                messages.success(request, f"“{listing.title}” was unpublished.")
        elif action == "sold":
            if not listing.is_published:
                messages.error(
                    request, "Only published listings can be marked as sold."
                )
            else:
                listing.status = Status.SOLD
                listing.save(update_fields=["status", "updated_at"])
                messages.success(request, f"“{listing.title}” was marked as sold.")

    def next_url(self, request, as_admin):
        target = request.POST.get("next", "")
        if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}
        ):
            return target
        return reverse("admin_listings" if as_admin else "my_listings")

class ListingBrowseView(LoginRequiredMixin, ListView):
    """Read: browse, search, filter and sort published listings."""

    template_name = "listings/listing_list.html"
    context_object_name = "listings"
    paginate_by = 12

    def get_queryset(self):
        queryset = _with_photos(
            Listing.objects.filter(status=Status.PUBLISHED, seller__is_active=True)
        )
        self.filter_form = ListingFilterForm(self.request.GET)
        self.filter_form.is_valid()
        data = getattr(self.filter_form, "cleaned_data", {})

        if data.get("q"):
            term = data["q"].strip()
            queryset = queryset.filter(
                Q(title__icontains=term) | Q(description__icontains=term)
            )
        for field in ("category", "size", "condition"):
            if data.get(field):
                queryset = queryset.filter(**{field: data[field]})
        if data.get("min_price") is not None:
            queryset = queryset.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(price__lte=data["max_price"])

        ordering = {
            "oldest": "created_at",
            "price_low": "price",
            "price_high": "-price",
        }.get(data.get("sort"), "-created_at")
        return queryset.order_by(ordering, "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filter_form"] = self.filter_form
        context["querystring"] = params.urlencode()
        return context