from django.urls import reverse_lazy
from django.views import generic, View
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from manager.forms import TaskForm, TaskFilterForm
from manager.models import Task
from manager.services import (
    build_sticky_querystring,
    get_tasks_by_status_with_permissions,
    get_filtered_tasks_with_permissions,
    get_optimized_task_queryset,
    cache_user_permissions,
)
from manager.mixins import TaskPermissionMixin, TaskPermissionJSONMixin


class LandingPageView(generic.TemplateView):
    template_name = "landing/landing_page.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('manager:task-list')
        return super().dispatch(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_list.html"
    context_object_name = "tasks"
    paginate_by = 6

    def get_queryset(self):
        queryset, self._filter_form, self._search_value, self._user_permissions = (
            get_filtered_tasks_with_permissions(self.request.GET, self.request.user)
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "filter_form": getattr(
                    self, "_filter_form", TaskFilterForm(self.request.GET or None)
                ),
                "search_value": getattr(
                    self,
                    "_search_value",
                    (
                        self.request.GET.get("search")
                        or self.request.GET.get("q")
                        or ""
                    ).strip(),
                ),
                "current_query": build_sticky_querystring(self.request.GET),
                "user_permissions": getattr(self, "_user_permissions", {}),
            }
        )
        return context


class TaskKanbanView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "manager/task_kanban.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kanban_data = get_tasks_by_status_with_permissions(self.request.user)
        context.update(kanban_data)

        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = "manager/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return get_optimized_task_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_permissions = cache_user_permissions([self.object], self.request.user)
        context["user_permissions"] = user_permissions
        return context


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


class TaskUpdateView(LoginRequiredMixin, TaskPermissionMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"

    def get_queryset(self):
        return get_optimized_task_queryset()

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


class TaskDeleteView(LoginRequiredMixin, TaskPermissionMixin, generic.DeleteView):
    model = Task
    template_name = "manager/task_confirm_delete.html"
    success_url = reverse_lazy("manager:task-list")

    def get_queryset(self):
        return get_optimized_task_queryset()

    def delete(self, request, *args, **kwargs):
        task_name = self.get_object().name
        messages.success(request, f"Task '{task_name}' was deleted successfully!")
        return super().delete(request, *args, **kwargs)


@method_decorator(require_POST, name="dispatch")
class TaskToggleStatusView(LoginRequiredMixin, TaskPermissionJSONMixin, generic.View):
    model = Task

    def post(self, request, pk, *args, **kwargs):
        new_status = (request.POST.get("status") or "").strip()
        valid_values = {value for value, _ in Task._meta.get_field("status").choices}
        if new_status not in valid_values:
            return JsonResponse(
                {"success": False, "error": "Invalid status"}, status=400
            )

        self.object.status = new_status
        self.object.save(update_fields=["status"])

        return JsonResponse(
            {
                "success": True,
                "new_status": self.object.get_status_display(),
                "status_key": self.object.status,
            },
            status=200,
        )
