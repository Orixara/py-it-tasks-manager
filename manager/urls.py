from django.urls import path

from manager.views import TaskListView

app_name = "manager"

urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
]