from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from manager.forms import TaskForm, TaskFilterForm
from manager.models import Task
from manager.services import apply_task_filters, build_sticky_querystring


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_list.html"
    context_object_name = "tasks"
    paginate_by = 6

    def get_queryset(self):
        queryset, self._filter_form, self._search_value = apply_task_filters(self.request.GET)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = getattr(self, "_filter_form", TaskFilterForm(self.request.GET or None))
        context["search_value"] = getattr(
            self,
            "_search_value",
            (self.request.GET.get("search") or self.request.GET.get("q") or "").strip(),
        )
        context["current_query"] = build_sticky_querystring(self.request.GET)
        return context


class TaskKanbanView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_kanban.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.all()
        context.update(
            {
                "todo_tasks": tasks.filter(status=Task.StatusChoices.TODO),
                "in_progress_tasks": tasks.filter(
                    status=Task.StatusChoices.IN_PROGRESS
                ),
                "review_tasks": tasks.filter(status=Task.StatusChoices.REVIEW),
                "done_tasks": tasks.filter(status=Task.StatusChoices.DONE),
            }
        )

        return context


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
        messages.success(
            self.request, f"Task '{form.instance.name}' was created successfully!"
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Create New Task",
                "button_text": "Create Task",
                "cancel_url": reverse_lazy("manager:task-list"),
            }
        )
        return context


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"

    def get_success_url(self):
        return reverse_lazy("manager:task-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request, f"Task '{form.instance.name}' was updated successfully!"
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Edit Task",
                "button_text": "Update Task",
                "cancel_url": reverse_lazy(
                    "manager:task-detail", kwargs={"pk": self.object.pk}
                ),
            }
        )
        return context


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    template_name = "manager/task_confirm_delete.html"
    success_url = reverse_lazy("manager:task-list")

    def delete(self, request, *args, **kwargs):
        task_name = self.get_object().name
        messages.success(request, f"Task '{task_name}' was deleted successfully!")
        return super().delete(request, *args, **kwargs)


@method_decorator(require_POST, name="dispatch")
class TaskToggleStatusView(LoginRequiredMixin, generic.View):
    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
            new_status = request.POST.get("status")

            if new_status in [choice[0] for choice in Task.StatusChoices.choices]:
                task.status = new_status
                task.save()

                return JsonResponse(
                    {
                        "success": True,
                        "new_status": task.get_status_display(),
                        "status_key": task.status
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid status"
                    }
                )
        except Task.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Task not found"
                }
            )