from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from manager.models import TaskType, Task
from accounts.models import Position


Worker = get_user_model()


class TaskModelTests(TestCase):

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser", password="testpass123", position=self.position
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.deadline = timezone.now() + timedelta(days=7)

    def test_task_creation_and_string_representation(self):
        task = Task.objects.create(
            name="Fix login bug",
            description="Users cannot login",
            deadline=self.deadline,
            priority=Task.PriorityChoices.HIGH,
            task_type=self.task_type,
            created_by=self.user,
        )
        expected = "Fix login bug (High)"
        self.assertEqual(str(task), expected)

    def test_task_default_values(self):
        task = Task.objects.create(
            name="Test task",
            deadline=self.deadline,
            task_type=self.task_type,
            created_by=self.user,
        )
        self.assertEqual(task.status, Task.StatusChoices.TODO)
        self.assertEqual(task.priority, Task.PriorityChoices.MEDIUM)

    def test_task_assignees_relationship(self):
        assignee = Worker.objects.create_user(
            username="assignee", password="testpass123"
        )
        task = Task.objects.create(
            name="Test task",
            deadline=self.deadline,
            task_type=self.task_type,
            created_by=self.user,
        )
        task.assignees.add(assignee)

        self.assertIn(assignee, task.assignees.all())
        self.assertIn(task, assignee.assigned_tasks.all())

    def test_task_status_and_priority_choices(self):
        task = Task.objects.create(
            name="Test task",
            deadline=self.deadline,
            task_type=self.task_type,
            created_by=self.user,
            status=Task.StatusChoices.IN_PROGRESS,
            priority=Task.PriorityChoices.URGENT,
        )
        self.assertEqual(task.get_status_display(), "In Progress")
        self.assertEqual(task.get_priority_display(), "Urgent")


class TaskTypeModelTests(TestCase):

    def test_task_type_creation(self):
        task_type = TaskType.objects.create(name="Bug Fix")
        self.assertEqual(str(task_type), "Bug Fix")

    def test_task_type_uniqueness(self):
        TaskType.objects.create(name="Feature")
        with self.assertRaises(Exception):
            TaskType.objects.create(name="Feature")
