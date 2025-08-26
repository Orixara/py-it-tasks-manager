from django.db.models import Q, QuerySet, Prefetch
from django.http import QueryDict
from django.contrib.auth import get_user_model
from collections import defaultdict
from typing import Dict, List, Tuple, Any

from manager.models import Task
from manager.forms import TaskFilterForm
from manager.permissions import is_manager

Worker = get_user_model()


def get_optimized_task_queryset() -> QuerySet[Task]:
    return (
        Task.objects.select_related(
            "task_type",
            "created_by",
            "created_by__position"
        )
        .prefetch_related(
            Prefetch(
                "assignees",
                queryset=Worker.objects.select_related("position"),
                to_attr="prefetched_assignees",
            )
        )
        .order_by("-created_at")
    )


def cache_user_permissions(
        tasks: List[Task],
        user
) -> Dict[int, Dict[str, bool]]:
    if not getattr(user, "is_authenticated", False):
        return {
            task.id: {
                "can_modify": False,
                "can_edit_delete": False
            } for task in tasks
        }

    user_is_manager = is_manager(user)
    user_id = user.id
    user_permissions = {}

    for task in tasks:
        can_modify = (
            user_is_manager
            or task.created_by_id == user_id
            or any(
                assignee.id == user_id
                for assignee in getattr(task, "prefetched_assignees", [])
            )
        )

        can_edit_delete = user_is_manager or task.created_by_id == user_id

        user_permissions[task.id] = {
            "can_modify": can_modify,
            "can_edit_delete": can_edit_delete,
        }

    return user_permissions


def get_tasks_by_status_with_permissions(user) -> Dict[str, Any]:
    queryset = get_optimized_task_queryset()
    tasks_by_status = defaultdict(list)
    all_tasks = []

    for task in queryset:
        tasks_by_status[task.status].append(task)
        all_tasks.append(task)

    user_permissions = cache_user_permissions(all_tasks, user)

    return {
        "todo_tasks": tasks_by_status[Task.StatusChoices.TODO],
        "in_progress_tasks": tasks_by_status[Task.StatusChoices.IN_PROGRESS],
        "review_tasks": tasks_by_status[Task.StatusChoices.REVIEW],
        "done_tasks": tasks_by_status[Task.StatusChoices.DONE],
        "user_permissions": user_permissions,
    }


def get_filtered_tasks_with_permissions(
    params: QueryDict, user
) -> Tuple[QuerySet, TaskFilterForm, str, Dict[int, Dict[str, bool]]]:
    form = TaskFilterForm(params or None)

    queryset = get_optimized_task_queryset()

    if not form.is_valid():
        legacy_search = (params.get("q") or "").strip()
        search_value = (params.get("search") or legacy_search or "").strip()
        tasks_list = list(queryset)
        user_permissions = cache_user_permissions(tasks_list, user)

        return queryset, form, search_value, user_permissions

    cleaned_data = form.cleaned_data
    search_value = (
        cleaned_data.get("search") or (params.get("q") or "").strip()
    ).strip()

    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value)
            | Q(description__icontains=search_value)
            | Q(task_type__name__icontains=search_value)
            | Q(assignees__username__icontains=search_value)
        )
    if cleaned_data.get("status"):
        queryset = queryset.filter(status=cleaned_data["status"])
    if cleaned_data.get("priority"):
        queryset = queryset.filter(priority=cleaned_data["priority"])
    if cleaned_data.get("task_type"):
        queryset = queryset.filter(task_type=cleaned_data["task_type"])
    if cleaned_data.get("assignee"):
        queryset = queryset.filter(assignees=cleaned_data["assignee"])

    filtered_queryset = queryset.distinct()
    tasks_list = list(filtered_queryset)
    user_permissions = cache_user_permissions(tasks_list, user)

    return filtered_queryset, form, search_value, user_permissions


def apply_task_filters(params: QueryDict) -> tuple[QuerySet, TaskFilterForm, str]:
    form = TaskFilterForm(params or None)

    queryset = get_optimized_task_queryset()

    if not form.is_valid():
        legacy_search = (params.get("q") or "").strip()
        search_value = (params.get("search") or legacy_search or "").strip()
        return queryset, form, search_value

    cleaned_data = form.cleaned_data
    search_value = (
        cleaned_data.get("search") or (params.get("q") or "").strip()
    ).strip()

    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value)
            | Q(description__icontains=search_value)
            | Q(task_type__name__icontains=search_value)
            | Q(assignees__username__icontains=search_value)
        )
    if cleaned_data.get("status"):
        queryset = queryset.filter(status=cleaned_data["status"])
    if cleaned_data.get("priority"):
        queryset = queryset.filter(priority=cleaned_data["priority"])
    if cleaned_data.get("task_type"):
        queryset = queryset.filter(task_type=cleaned_data["task_type"])
    if cleaned_data.get("assignee"):
        queryset = queryset.filter(assignees=cleaned_data["assignee"])

    return queryset.distinct(), form, search_value


def build_sticky_querystring(params: QueryDict) -> str:
    query_dict = params.copy()
    query_dict.pop("page", None)
    if "q" in query_dict and "search" not in query_dict:
        query_dict["search"] = query_dict.pop("q")
    return query_dict.urlencode()
