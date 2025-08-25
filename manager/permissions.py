from __future__ import annotations

MANAGER_POSITIONS: set[str] = {"Manager", "Project Manager", "Team Lead"}

def is_manager(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    pos = getattr(user, "position", None)
    name = getattr(pos, "name", None)
    return name in MANAGER_POSITIONS

def can_modify_task(user, task) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if is_manager(user):
        return True
    if getattr(task, "created_by_id", None) == getattr(user, "id", None):
        return True

    try:
        return task.assignees.filter(pk=user.pk).exists()
    except Exception:
        return False