from django.urls import path

from manager.views import (
    TaskListView,
    TaskDetailView,
    TaskCreateView,
)

app_name = "manager"

urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
    path("task/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("task/create/", TaskCreateView.as_view(), name="task-create"),
]