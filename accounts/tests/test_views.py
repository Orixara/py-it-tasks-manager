from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Position

Worker = get_user_model()


class ProfileViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            position=self.position,
        )

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated_user(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_profile_view_has_required_context(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))

        required_context = [
            "assigned_count",
            "created_count",
            "status_stats",
            "active_tasks",
        ]
        for key in required_context:
            self.assertIn(key, response.context)


class SignUpViewTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_signup_view_get(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_view_creates_user(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Worker.objects.filter(username="newuser").exists())
