from django.db import models
from django.contrib.auth import get_user_model

Worker = get_user_model()


class TaskType(models.Model):
    name = models.CharField(max_length=63, unique=True)

    class Meta:
        verbose_name = "Task Type"
        verbose_name_plural = "Task Types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class PriorityChoices(models.TextChoices):
        URGENT = "urgent", "Urgent"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    name = models.CharField(max_length=163)
    description = models.TextField(max_length=512, blank=True, null=True)
    deadline = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM
    )
    task_type = models.ForeignKey(
        TaskType,
        related_name="tasks",
        on_delete=models.CASCADE
    )
    assignees = models.ManyToManyField(
        Worker,
        related_name="assigned_tasks",
        blank=True
    )
    created_by = models.ForeignKey(
        Worker,
        related_name="created_tasks",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})"
