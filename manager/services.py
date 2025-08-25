from django.db.models import Q, QuerySet
from django.http import QueryDict

from manager.models import Task
from manager.forms import TaskFilterForm


def apply_task_filters(params: QueryDict) -> tuple[QuerySet, TaskFilterForm, str]:
    form = TaskFilterForm(params or None)

    queryset = Task.objects.select_related(
        "task_type"
    ).prefetch_related(
        "assignees"
    ).order_by("-created_at")

    if not form.is_valid():
        legacy_search = (params.get("q") or "").strip()
        search_value = (params.get("search") or legacy_search or "").strip()
        return queryset, form, search_value

    cleaned_data = form.cleaned_data
    search_value = (cleaned_data.get("search") or (params.get("q") or "").strip()).strip()

    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) | Q(description__icontains=search_value)
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