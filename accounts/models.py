from django.contrib.auth.models import AbstractUser
from django.db import models


class Position(models.Model):
    name = models.CharField(max_length=63, unique=True)

    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    position = models.ForeignKey(
        Position,
        related_name="workers",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Worker"
        verbose_name_plural = "Workers"

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.username} ({self.first_name} {self.last_name})"
        return self.username