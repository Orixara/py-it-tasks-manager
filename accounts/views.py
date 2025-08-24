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