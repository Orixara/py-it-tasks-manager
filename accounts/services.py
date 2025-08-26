from django.db.models import Count, Q, When, Prefetch
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any
from django.contrib.auth import get_user_model

from manager.models import Task


def get_user_profile_stats(user) -> Dict[str, Any]:

    if not getattr(user, "is_authenticated", False):
        return {}

    user_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assignees=user)
    ).distinct()

    status_stats = user_tasks.aggregate(
        total_assigned=Count("id", filter=Q(assignees=user)),
        total_created=Count("id", filter=Q(created_by=user)),
        todo_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.TODO)
        ),
        in_progress_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.IN_PROGRESS)
        ),
        review_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.REVIEW)
        ),
        done_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.DONE)
        ),
    )

    return {
        "assigned_count": status_stats["total_assigned"],
        "created_count": status_stats["total_created"],
        "completed_count": status_stats["done_count"],
        "status_stats": {
            "todo": status_stats["todo_count"],
            "in_progress": status_stats["in_progress_count"],
            "review": status_stats["review_count"],
            "done": status_stats["done_count"],
        },
    }


def get_user_active_tasks(user, limit: int = 10):
    if not getattr(user, "is_authenticated", False):
        return Task.objects.none()

    return (
        Task.objects.select_related(
            "task_type",
            "created_by",
            "created_by__position"
        )
        .prefetch_related(
            Prefetch(
                "assignees",
                queryset=get_user_model().objects.select_related("position"),
                to_attr="prefetched_assignees",
            )
        )
        .filter(
            Q(created_by=user) | Q(assignees=user),
            status__in=[
                Task.StatusChoices.TODO,
                Task.StatusChoices.IN_PROGRESS,
                Task.StatusChoices.REVIEW,
            ],
        )
        .distinct()
        .order_by("-created_at")[:limit]
    )


def get_user_weekly_stats(
        user,
        weeks: int = 4
) -> List[Dict[str, Any]]:
    if not getattr(user, "is_authenticated", False):
        return []

    today = timezone.now().date()
    weekly_conditions = []

    for i in range(weeks):
        week_start = today - timedelta(weeks=i + 1)
        week_end = today - timedelta(weeks=i)
        weekly_conditions.append(
            When(
                Q(assignees=user)
                & Q(status=Task.StatusChoices.DONE)
                & Q(created_at__date__gte=week_start)
                & Q(created_at__date__lt=week_end),
                then=1,
            )
        )

    weekly_data = (
        Task.objects.filter(
            Q(assignees=user) & Q(status=Task.StatusChoices.DONE)
        )
        .distinct()
        .aggregate(
            week_0=Count(
                "id",
                filter=Q(
                    created_at__date__gte=today - timedelta(weeks=1),
                    created_at__date__lt=today,
                ),
            ),
            week_1=Count(
                "id",
                filter=Q(
                    created_at__date__gte=today - timedelta(weeks=2),
                    created_at__date__lt=today - timedelta(weeks=1),
                ),
            ),
            week_2=Count(
                "id",
                filter=Q(
                    created_at__date__gte=today - timedelta(weeks=3),
                    created_at__date__lt=today - timedelta(weeks=2),
                ),
            ),
            week_3=Count(
                "id",
                filter=Q(
                    created_at__date__gte=today - timedelta(weeks=4),
                    created_at__date__lt=today - timedelta(weeks=3),
                ),
            ),
        )
    )

    weekly_stats = []
    for i in range(weeks):
        week_start = today - timedelta(weeks=i + 1)
        week_end = today - timedelta(weeks=i)
        completed = weekly_data.get(f"week_{i}", 0)

        weekly_stats.append(
            {
                "week": f"Week {weeks-i}",
                "completed": completed,
                "week_start": week_start.strftime("%m/%d"),
                "week_end": week_end.strftime("%m/%d"),
            }
        )

    return list(reversed(weekly_stats))


def get_full_user_profile_data(user) -> Dict[str, Any]:
    if not getattr(user, "is_authenticated", False):
        return {
            "assigned_count": 0,
            "created_count": 0,
            "completed_count": 0,
            "status_stats": {
                "todo": 0,
                "in_progress": 0,
                "review": 0,
                "done": 0
            },
            "active_tasks": Task.objects.none(),
            "weekly_stats": [],
        }
    today = timezone.now().date()
    user_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assignees=user)
    ).distinct()

    combined_stats = user_tasks.aggregate(
        total_assigned=Count("id", filter=Q(assignees=user)),
        total_created=Count("id", filter=Q(created_by=user)),
        todo_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.TODO)
        ),
        in_progress_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.IN_PROGRESS)
        ),
        review_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.REVIEW)
        ),
        done_count=Count(
            "id",
            filter=Q(assignees=user, status=Task.StatusChoices.DONE)
        ),
        week_0=Count(
            "id",
            filter=Q(
                assignees=user,
                status=Task.StatusChoices.DONE,
                created_at__date__gte=today - timedelta(weeks=1),
                created_at__date__lt=today,
            ),
        ),
        week_1=Count(
            "id",
            filter=Q(
                assignees=user,
                status=Task.StatusChoices.DONE,
                created_at__date__gte=today - timedelta(weeks=2),
                created_at__date__lt=today - timedelta(weeks=1),
            ),
        ),
        week_2=Count(
            "id",
            filter=Q(
                assignees=user,
                status=Task.StatusChoices.DONE,
                created_at__date__gte=today - timedelta(weeks=3),
                created_at__date__lt=today - timedelta(weeks=2),
            ),
        ),
        week_3=Count(
            "id",
            filter=Q(
                assignees=user,
                status=Task.StatusChoices.DONE,
                created_at__date__gte=today - timedelta(weeks=4),
                created_at__date__lt=today - timedelta(weeks=3),
            ),
        ),
    )

    active_tasks = get_user_active_tasks(user, limit=10)

    weekly_stats = []
    for i in range(4):
        week_start = today - timedelta(weeks=i + 1)
        week_end = today - timedelta(weeks=i)
        completed = combined_stats.get(f"week_{i}", 0)

        weekly_stats.append(
            {
                "week": f"Week {4-i}",
                "completed": completed,
                "week_start": week_start.strftime("%m/%d"),
                "week_end": week_end.strftime("%m/%d"),
            }
        )

    return {
        "assigned_count": combined_stats["total_assigned"],
        "created_count": combined_stats["total_created"],
        "completed_count": combined_stats["done_count"],
        "status_stats": {
            "todo": combined_stats["todo_count"],
            "in_progress": combined_stats["in_progress_count"],
            "review": combined_stats["review_count"],
            "done": combined_stats["done_count"],
        },
        "active_tasks": active_tasks,
        "weekly_stats": list(reversed(weekly_stats)),
    }
