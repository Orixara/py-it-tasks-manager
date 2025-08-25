from django.contrib import admin
from manager.models import TaskType, Task


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", )
    search_fields = ("name", )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "task_type",
        "priority",
        "deadline",
        "status",
        "created_by"
    )
    list_filter = (
        "task_type",
        "priority",
        "status",
        "created_at"
    )
    search_fields = ("name", "description")
    filter_horizontal = ("assignees",)

