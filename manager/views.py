from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from manager.forms import TaskForm
from manager.models import Task


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_list.html"
    context_object_name = "tasks"


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = "manager/task_detail.html"
    context_object_name = "task"


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"
    success_url = reverse_lazy("manager:task-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)