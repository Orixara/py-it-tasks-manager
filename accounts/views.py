from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from accounts.forms import WorkerCreationForm
from accounts.services import get_full_user_profile_data
from manager.models import Task


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
        profile_data = get_full_user_profile_data(self.request.user)
        context.update(profile_data)

        return context
