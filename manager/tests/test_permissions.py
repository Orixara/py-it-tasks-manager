from django.test import TestCase
from django.contrib.auth import get_user_model

from manager.permissions import (
    is_manager,
    can_modify_task,
    can_edit_or_delete_task
)
from manager.models import TaskType, Task
from accounts.models import Position
from datetime import timedelta
from django.utils import timezone

Worker = get_user_model()


class PermissionsTests(TestCase):

    def setUp(self):
        self.manager_position = Position.objects.create(name="Manager")
        self.developer_position = Position.objects.create(name="Developer")

        self.manager = Worker.objects.create_user(
            username="manager",
            password="testpass123",
            position=self.manager_position
        )
        self.developer = Worker.objects.create_user(
            username="developer",
            password="testpass123",
            position=self.developer_position,
        )

        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.deadline = timezone.now() + timedelta(days=7)
        self.task = Task.objects.create(
            name="Test task",
            deadline=self.deadline,
            task_type=self.task_type,
            created_by=self.developer,
        )

    def test_manager_permissions(self):
        self.assertTrue(is_manager(self.manager))
        self.assertTrue(can_modify_task(self.manager, self.task))
        self.assertTrue(can_edit_or_delete_task(self.manager, self.task))

    def test_developer_permissions(self):
        self.assertFalse(is_manager(self.developer))

    def test_task_creator_permissions(self):
        self.assertTrue(can_modify_task(self.developer, self.task))
        self.assertTrue(can_edit_or_delete_task(self.developer, self.task))

    def test_task_assignee_permissions(self):
        assignee = Worker.objects.create_user(
            username="assignee", password="testpass123"
        )
        self.task.assignees.add(assignee)

        self.assertTrue(can_modify_task(assignee, self.task))
        self.assertFalse(can_edit_or_delete_task(assignee, self.task))

    def test_unrelated_user_permissions(self):
        unrelated_user = Worker.objects.create_user(
            username="unrelated", password="testpass123"
        )

        self.assertFalse(can_modify_task(unrelated_user, self.task))
        self.assertFalse(can_edit_or_delete_task(unrelated_user, self.task))
