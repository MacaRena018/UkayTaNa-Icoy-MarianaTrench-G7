from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class RoleDashboardTests(TestCase):
    def create_user(self, role):
        return User.objects.create_user(
            username=role.lower(),
            email=f"{role.lower()}@example.com",
            password="UkaySecure!2030",
            role=role,
        )

    def test_logged_out_user_is_sent_to_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_buyer_cannot_open_seller_dashboard(self):
        buyer = self.create_user(User.Role.BUYER)
        self.client.force_login(buyer)

        response = self.client.get(reverse("seller_dashboard"))

        self.assertRedirects(
            response, reverse("dashboard"), fetch_redirect_response=False
        )
        self.assertRedirects(
            self.client.get(response.url), reverse("buyer_dashboard")
        )

    def test_seller_and_admin_are_redirected_to_their_dashboards(self):
        for role, dashboard in (
            (User.Role.SELLER, "seller_dashboard"),
            (User.Role.ADMIN, "admin_dashboard"),
        ):
            with self.subTest(role=role):
                user = self.create_user(role)
                self.client.force_login(user)

                response = self.client.get(reverse("dashboard"))

                self.assertRedirects(response, reverse(dashboard))
