from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import QueryDict
from datetime import timedelta
from django.utils import timezone

from manager.services import (
    get_optimized_task_queryset,
    cache_user_permissions,
    get_tasks_by_status_with_permissions,
    get_filtered_tasks_with_permissions,
    apply_task_filters,
    build_sticky_querystring
)
from manager.models import TaskType, Task
from accounts.models import Position


Worker = get_user_model()


class ServicesTests(TestCase):

    def setUp(self):
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
        self.assignee = Worker.objects.create_user(
            username='assignee',
            password='testpass123'
        )
        
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.deadline = timezone.now() + timedelta(days=7)
        
        self.task1 = Task.objects.create(
            name="Task 1",
            description="First task",
            deadline=self.deadline,
            status=Task.StatusChoices.TODO,
            priority=Task.PriorityChoices.HIGH,
            task_type=self.task_type,
            created_by=self.developer
        )
        self.task1.assignees.add(self.assignee)
        
        self.task2 = Task.objects.create(
            name="Task 2", 
            description="Second task",
            deadline=self.deadline,
            status=Task.StatusChoices.IN_PROGRESS,
            priority=Task.PriorityChoices.MEDIUM,
            task_type=self.task_type,
            created_by=self.manager
        )

    def test_get_optimized_task_queryset(self):
        queryset = get_optimized_task_queryset()

        self.assertEqual(queryset.model, Task)

        tasks = list(queryset)
        self.assertEqual(tasks[0], self.task2)
        self.assertEqual(tasks[1], self.task1)

    def test_cache_user_permissions_manager(self):
        tasks = [self.task1, self.task2]
        permissions = cache_user_permissions(tasks, self.manager)

        self.assertTrue(permissions[self.task1.id]['can_modify'])
        self.assertTrue(permissions[self.task1.id]['can_edit_delete'])
        self.assertTrue(permissions[self.task2.id]['can_modify'])
        self.assertTrue(permissions[self.task2.id]['can_edit_delete'])

    def test_cache_user_permissions_creator(self):
        tasks = [self.task1, self.task2]
        permissions = cache_user_permissions(tasks, self.developer)

        self.assertTrue(permissions[self.task1.id]['can_modify'])
        self.assertTrue(permissions[self.task1.id]['can_edit_delete'])

        self.assertFalse(permissions[self.task2.id]['can_modify'])
        self.assertFalse(permissions[self.task2.id]['can_edit_delete'])

    def test_cache_user_permissions_assignee(self):
        optimized_tasks = list(get_optimized_task_queryset().filter(id__in=[self.task1.id, self.task2.id]))
        
        permissions = cache_user_permissions(optimized_tasks, self.assignee)

        self.assertTrue(permissions[self.task1.id]['can_modify'])
        self.assertFalse(permissions[self.task1.id]['can_edit_delete'])

        self.assertFalse(permissions[self.task2.id]['can_modify'])
        self.assertFalse(permissions[self.task2.id]['can_edit_delete'])

    def test_cache_user_permissions_unauthenticated(self):
        class MockUser:
            is_authenticated = False
        
        tasks = [self.task1]
        permissions = cache_user_permissions(tasks, MockUser())
        
        self.assertFalse(permissions[self.task1.id]['can_modify'])
        self.assertFalse(permissions[self.task1.id]['can_edit_delete'])

    def test_get_tasks_by_status_with_permissions(self):
        result = get_tasks_by_status_with_permissions(self.manager)

        self.assertIn('todo_tasks', result)
        self.assertIn('in_progress_tasks', result)
        self.assertIn('review_tasks', result)
        self.assertIn('done_tasks', result)
        self.assertIn('user_permissions', result)

        self.assertIn(self.task1, result['todo_tasks'])
        self.assertIn(self.task2, result['in_progress_tasks'])

        permissions = result['user_permissions']
        self.assertTrue(permissions[self.task1.id]['can_modify'])

    def test_apply_task_filters_no_filters(self):
        query_dict = QueryDict()
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(search_value, "")

    def test_apply_task_filters_with_search(self):
        query_dict = QueryDict('search=Task%201')
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)
        self.assertEqual(search_value, "Task 1")

    def test_apply_task_filters_with_status(self):
        query_dict = QueryDict('status=todo')
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)

    def test_apply_task_filters_with_priority(self):
        query_dict = QueryDict('priority=high')
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)

    def test_apply_task_filters_with_task_type(self):
        query_dict = QueryDict(f'task_type={self.task_type.id}')
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 2)

    def test_apply_task_filters_with_assignee(self):
        query_dict = QueryDict(f'assignee={self.assignee.id}')
        queryset, form, search_value = apply_task_filters(query_dict)
        
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)

    def test_build_sticky_querystring(self):
        query_dict = QueryDict('search=test&status=todo&page=2')
        result = build_sticky_querystring(query_dict)

        self.assertNotIn('page=2', result)
        self.assertIn('search', result)
        self.assertIn('status', result)

    def test_build_sticky_querystring_with_q_param(self):
        query_dict = QueryDict('q=test&status=todo')
        result = build_sticky_querystring(query_dict)

        self.assertNotIn('q=test', result)
        self.assertIn('search', result)
        self.assertIn('status', result)

    def test_get_filtered_tasks_with_permissions(self):
        query_dict = QueryDict('status=todo')
        queryset, form, search_value, permissions = get_filtered_tasks_with_permissions(
            query_dict, self.manager
        )

        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)
        self.assertIn(self.task1.id, permissions)
        self.assertTrue(permissions[self.task1.id]['can_modify'])

    def test_get_filtered_tasks_with_permissions_invalid_form(self):
        query_dict = QueryDict('task_type=999')
        queryset, form, search_value, permissions = get_filtered_tasks_with_permissions(
            query_dict, self.manager
        )

        self.assertEqual(queryset.count(), 2)
        self.assertFalse(form.is_valid())

        self.assertIn(self.task1.id, permissions)
        self.assertIn(self.task2.id, permissions)
