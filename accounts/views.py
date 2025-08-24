from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from accounts.forms import WorkerCreationForm


Worker = get_user_model()


class SignUpView(generic.CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            "assigned_count": user.assigned_tasks.count(),
            "created_count": user.created_tasks.count(),
            "completed_count": user.assigned_tasks.filter(is_completed=True).count(),
        })
        return context