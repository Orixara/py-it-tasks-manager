from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.forms import WorkerCreationForm
from accounts.models import Position

Worker = get_user_model()


class WorkerCreationFormTests(TestCase):

    def setUp(self):
        self.position = Position.objects.create(name="Developer")

    def test_worker_creation_form_valid_data(self):
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "position": self.position.id,
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_worker_creation_form_save(self):
        form_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.com",
            "position": self.position.id,
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        if form.is_valid():
            user = form.save()
            self.assertEqual(user.username, "newuser")
            self.assertEqual(user.position, self.position)
            self.assertEqual(user.email, "new@example.com")

    def test_worker_creation_form_no_username(self):
        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_worker_creation_form_password_mismatch(self):
        form_data = {
            "username": "testuser",
            "password1": "ComplexPass123!",
            "password2": "DifferentPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_worker_creation_form_without_position(self):
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_worker_creation_form_invalid_email(self):
        form_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = WorkerCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
