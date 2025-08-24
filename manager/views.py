from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from manager.models import Task


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_list.html"
    context_object_name = "tasks"