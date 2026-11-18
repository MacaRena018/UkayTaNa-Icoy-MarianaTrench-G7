from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountRegistrationTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "username": "samplebuyer",
            "email": "buyer@example.com",
            "first_name": "Sample",
            "last_name": "Buyer",
            "contact_number": "09171234567",
            "barangay": "Lahug",
            "city": "Cebu City",
            "role": User.Role.BUYER,
            "shop_name": "",
            "password1": "UkaySecure!2030",
            "password2": "UkaySecure!2030",
        }
        data.update(overrides)
        return data

    def test_registration_creates_user_with_hashed_password(self):
        response = self.client.post(
            reverse("signup"), self.registration_data(), follow=True
        )

        user = User.objects.get(username="samplebuyer")
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(user.check_password("UkaySecure!2030"))
        self.assertNotEqual(user.password, "UkaySecure!2030")
        self.assertContains(response, "Account created!")

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("signup"),
            self.registration_data(password2="DifferentPassword!2030"),
        )

        self.assertFormError(
            response.context["form"],
            "password2",
            "The two password fields didn’t match.",
        )
        self.assertFalse(User.objects.filter(username="samplebuyer").exists())

    def test_registration_rejects_duplicate_username_and_email(self):
        User.objects.create_user(
            username="existinguser",
            email="Existing@Example.com",
            password="UkaySecure!2030",
        )

        duplicate_username = self.client.post(
            reverse("signup"),
            self.registration_data(username="existinguser"),
        )
        duplicate_email = self.client.post(
            reverse("signup"),
            self.registration_data(
                username="anotheruser", email="existing@example.com"
            ),
        )

        self.assertFormError(
            duplicate_username.context["form"],
            "username",
            "That username is already taken. Choose another.",
        )
        self.assertFormError(
            duplicate_email.context["form"],
            "email",
            "An account with this email already exists.",
        )
        self.assertFalse(User.objects.filter(username="anotheruser").exists())

    def test_registration_rejects_invalid_email(self):
        response = self.client.post(
            reverse("signup"), self.registration_data(email="not-an-email")
        )

        self.assertFormError(
            response.context["form"], "email", "Enter a valid email address."
        )
        self.assertFalse(User.objects.filter(username="samplebuyer").exists())


class AccountAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="UkaySecure!2030",
            role=User.Role.BUYER,
        )

    def test_login_redirects_to_role_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": "buyer", "password": "UkaySecure!2030"},
        )

        self.assertRedirects(
            response, reverse("dashboard"), fetch_redirect_response=False
        )
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("buyer_dashboard"))

    def test_invalid_login_shows_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": "buyer", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_profile_requires_login_and_user_can_update_own_profile(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('profile')}"
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Updated",
                "last_name": "Buyer",
                "email": "updated@example.com",
                "contact_number": "09171234567",
                "barangay": "",
                "city": "Cebu City",
                "bio": "",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.first_name, "Updated")
