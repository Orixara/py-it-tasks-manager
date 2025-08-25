from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from accounts.forms import WorkerCreationForm
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
        user = self.request.user

        # Statistics by status
        assigned_tasks = user.assigned_tasks.all()
        status_stats = {
            'todo': assigned_tasks.filter(status=Task.StatusChoices.TODO).count(),
            'in_progress': assigned_tasks.filter(status=Task.StatusChoices.IN_PROGRESS).count(),
            'review': assigned_tasks.filter(status=Task.StatusChoices.REVIEW).count(),
            'done': assigned_tasks.filter(status=Task.StatusChoices.DONE).count(),
        }
        
        # Active tasks (not done)
        active_tasks = assigned_tasks.exclude(status=Task.StatusChoices.DONE)[:10]
        
        # Weekly statistics (last 4 weeks)
        today = timezone.now().date()
        weekly_stats = []
        for i in range(4):
            week_start = today - timedelta(weeks=i+1)
            week_end = today - timedelta(weeks=i)
            week_completed = assigned_tasks.filter(
                status=Task.StatusChoices.DONE,
                created_at__date__gte=week_start,
                created_at__date__lt=week_end
            ).count()
            weekly_stats.append({
                'week': f"Week {i+1}",
                'completed': week_completed,
                'week_start': week_start.strftime('%m/%d'),
                'week_end': week_end.strftime('%m/%d')
            })
        
        context.update({
            "assigned_count": assigned_tasks.count(),
            "created_count": user.created_tasks.count(),
            "completed_count": status_stats['done'],
            "status_stats": status_stats,
            "active_tasks": active_tasks,
            "weekly_stats": list(reversed(weekly_stats)),  # Show chronologically
        })
        return context