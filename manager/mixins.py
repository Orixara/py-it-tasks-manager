from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from django.views.generic.detail import SingleObjectMixin

from .permissions import can_modify_task


class TaskPermissionMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        task = self.get_object()
        return can_modify_task(self.request.user, task)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You have no permission to modify this task.")
        return super().handle_no_permission()


class TaskPermissionJSONMixin(SingleObjectMixin):
    permission_error_message = "You have no permission to change this task."

    def dispatch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return JsonResponse({"success": False, "error": "Task not found"}, status=404)

        if not can_modify_task(request.user, self.object):
            return JsonResponse({"success": False, "error": self.permission_error_message}, status=403)

        return super().dispatch(request, *args, **kwargs)
