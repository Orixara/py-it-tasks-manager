from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from manager.forms import TaskForm, TaskFilterForm
from manager.models import TaskType, Task
from accounts.models import Position

Worker = get_user_model()


class TaskFormTests(TestCase):

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser", password="testpass123", position=self.position
        )
        self.assignee = Worker.objects.create_user(
            username="assignee", password="testpass123"
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.future_date = timezone.now() + timedelta(days=7)

    def test_task_form_valid_data(self):
        form_data = {
            "name": "Fix critical bug",
            "description": "This is a critical bug that needs fixing",
            "deadline": self.future_date.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": Task.PriorityChoices.HIGH,
            "task_type": self.task_type.id,
            "assignees": [self.assignee.id],
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_form_save(self):
        form_data = {
            "name": "New task",
            "description": "Task description",
            "deadline": self.future_date.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": Task.PriorityChoices.MEDIUM,
            "task_type": self.task_type.id,
            "assignees": [self.assignee.id],
        }
        form = TaskForm(data=form_data)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = self.user
            task.save()
            form.save_m2m()

            self.assertEqual(task.name, "New task")
            self.assertEqual(task.priority, Task.PriorityChoices.MEDIUM)
            self.assertIn(self.assignee, task.assignees.all())

    def test_task_form_missing_required_fields(self):
        form_data = {"description": "Task description"}
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("deadline", form.errors)
        self.assertIn("task_type", form.errors)

    def test_task_form_empty_name(self):
        form_data = {
            "name": "",
            "deadline": self.future_date.strftime("%Y-%m-%d %H:%M:%S"),
            "task_type": self.task_type.id,
        }
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_task_form_invalid_task_type(self):
        form_data = {
            "name": "Test task",
            "deadline": self.future_date.strftime("%Y-%m-%d %H:%M:%S"),
            "task_type": 999,
        }
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("task_type", form.errors)

    def test_task_form_without_assignees(self):
        form_data = {
            "name": "Test task",
            "description": "Task description",
            "deadline": self.future_date,
            "priority": Task.PriorityChoices.MEDIUM,
            "task_type": self.task_type.id,
        }
        form = TaskForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())


class TaskFilterFormTests(TestCase):

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser", password="testpass123", position=self.position
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")

    def test_task_filter_form_valid_search(self):
        form_data = {"search": "bug fix"}
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_valid_status_filter(self):
        form_data = {"status": Task.StatusChoices.TODO}
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_valid_priority_filter(self):
        form_data = {"priority": Task.PriorityChoices.HIGH}
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_valid_task_type_filter(self):
        form_data = {"task_type": self.task_type.id}
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_valid_assignee_filter(self):
        form_data = {"assignee": self.user.id}
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_all_filters_combined(self):
        form_data = {
            "search": "test",
            "status": Task.StatusChoices.IN_PROGRESS,
            "priority": Task.PriorityChoices.HIGH,
            "task_type": self.task_type.id,
            "assignee": self.user.id,
        }
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_empty_data(self):
        form = TaskFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_task_filter_form_invalid_task_type(self):
        form_data = {"task_type": 999}
        form = TaskFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("task_type", form.errors)

    def test_task_filter_form_invalid_assignee(self):
        form_data = {"assignee": 999}
        form = TaskFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("assignee", form.errors)
