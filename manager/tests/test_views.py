from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
import json

from manager.models import TaskType, Task
from accounts.models import Position

Worker = get_user_model()


class TaskViewsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager_position = Position.objects.create(name="Manager")
        self.dev_position = Position.objects.create(name="Developer")
        
        self.manager = Worker.objects.create_user(
            username='manager',
            password='testpass123',
            position=self.manager_position
        )
        self.developer = Worker.objects.create_user(
            username='developer',
            password='testpass123',
            position=self.dev_position
        )
        
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.deadline = timezone.now() + timedelta(days=7)
        
        self.task = Task.objects.create(
            name="Test task",
            description="Test description",
            deadline=self.deadline,
            task_type=self.task_type,
            created_by=self.developer
        )

    def test_task_list_view_requires_login(self):
        response = self.client.get(reverse('manager:task-list'))
        self.assertEqual(response.status_code, 302)

    def test_task_list_view_authenticated(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.get(reverse('manager:task-list'))
        self.assertEqual(response.status_code, 200)

    def test_task_kanban_view_authenticated(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.get(reverse('manager:task-kanban'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kanban Board')

    def test_task_detail_view(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.get(reverse('manager:task-detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.name)

    def test_task_create_view_post(self):
        self.client.login(username='developer', password='testpass123')
        data = {
            'name': 'New Task',
            'description': 'New task description',
            'deadline': self.deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'priority': Task.PriorityChoices.HIGH,
            'task_type': self.task_type.id,
        }
        response = self.client.post(reverse('manager:task-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(name='New Task').exists())

    def test_task_update_view_creator_access(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.get(reverse('manager:task-update', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_unauthorized_access(self):
        unauthorized_user = Worker.objects.create_user(
            username='unauthorized',
            password='testpass123'
        )
        self.client.login(username='unauthorized', password='testpass123')
        response = self.client.get(reverse('manager:task-update', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 403)

    def test_task_delete_view_post(self):
        self.client.login(username='developer', password='testpass123')
        task_pk = self.task.pk
        response = self.client.post(reverse('manager:task-delete', kwargs={'pk': task_pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task_pk).exists())

    def test_task_toggle_status_view(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.post(
            reverse('manager:task-toggle-status', kwargs={'pk': self.task.pk}),
            {'status': 'in_progress'}
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')

    def test_task_toggle_status_invalid_status(self):
        self.client.login(username='developer', password='testpass123')
        response = self.client.post(
            reverse('manager:task-toggle-status', kwargs={'pk': self.task.pk}),
            {'status': 'invalid_status'}
        )
        self.assertEqual(response.status_code, 400)
