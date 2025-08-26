from django import template
from manager.permissions import is_manager, can_modify_task, can_edit_or_delete_task

register = template.Library()


@register.filter
def user_is_manager(user) -> bool:
    return is_manager(user)


@register.simple_tag
def can_modify(user, task) -> bool:
    return can_modify_task(user, task)


@register.simple_tag
def can_edit_delete(user, task) -> bool:
    return can_edit_or_delete_task(user, task)


@register.filter
def get_permission(user_permissions, task_id):
    return user_permissions.get(
        task_id, {"can_modify": False, "can_edit_delete": False}
    )


@register.filter
def can_modify_cached(permissions):
    return permissions.get("can_modify", False)


@register.filter
def can_edit_delete_cached(permissions):
    return permissions.get("can_edit_delete", False)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, {})


@register.simple_tag
def page_window(page_obj, paginator, window: int = 2):
    current = int(getattr(page_obj, "number", 1))
    last = int(getattr(paginator, "num_pages", 1))
    window = int(window)

    if last <= 1:
        return [1]

    left = max(1, current - window)
    right = min(last, current + window)

    pages = [1]

    if left > 2:
        pages.append(None)

    for p in range(left, right + 1):
        if p not in (1, last):
            pages.append(p)

    if right < last - 1:
        pages.append(None)

    if last > 1:
        pages.append(last)

    return pages


@register.filter
def task_status_badge(status):
    status_classes = {
        "todo": "bg-warning",
        "in_progress": "bg-info",
        "review": "bg-primary",
        "done": "bg-success",
    }
    return status_classes.get(status, "bg-secondary")


@register.filter
def task_priority_badge(priority):
    priority_classes = {
        "urgent": "bg-danger",
        "high": "bg-warning",
        "medium": "bg-info",
        "low": "bg-success",
    }
    return priority_classes.get(priority, "bg-secondary")
