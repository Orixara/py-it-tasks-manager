from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import Position


Worker = get_user_model()


class PositionModelTests(TestCase):

    def test_position_creation_and_string_representation(self):
        position = Position.objects.create(name="Developer")
        self.assertEqual(str(position), "Developer")

    def test_position_name_uniqueness(self):
        Position.objects.create(name="Developer")
        with self.assertRaises(Exception):
            Position.objects.create(name="Developer")


class WorkerModelTests(TestCase):

    def test_worker_creation_with_position(self):
        position = Position.objects.create(name="Senior Developer")
        user = Worker.objects.create_user(
            username="john_dev",
            email="john@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=position,
        )

        self.assertEqual(str(user), "john_dev (John Doe)")
        self.assertEqual(user.position, position)

    def test_worker_creation_without_position(self):
        user = Worker.objects.create_user(
            username="jane_dev", email="jane@example.com", password="testpass123"
        )
        self.assertEqual(str(user), "jane_dev")
        self.assertIsNone(user.position)
