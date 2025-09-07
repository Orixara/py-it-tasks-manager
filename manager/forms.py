from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.cache import cache

from manager.models import Task, TaskType


Worker = get_user_model()


class TaskForm(forms.ModelForm):
    assignees = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select team members to assign this task to.",
    )

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "deadline",
            "priority",
            "task_type",
            "assignees",
        ]
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise ValidationError(
                "Deadline cannot be in the past. Please select a future date and time."
            )
        return deadline


class TaskFilterForm(forms.Form):
    search = forms.CharField(
        label="Search",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by name, description, task type, or assignee"
            }
        ),
    )
    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[],
        widget=forms.Select(),
    )
    priority = forms.ChoiceField(
        label="Priority",
        required=False,
        choices=[],
        widget=forms.Select(),
    )
    task_type = forms.ModelChoiceField(
        label="Task Type",
        required=False,
        queryset=TaskType.objects.all(),
        empty_label="All types",
        widget=forms.Select(),
    )
    assignee = forms.ChoiceField(
        label="Assignee",
        required=False,
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        status_choices = [("", "All statuses")] + list(
            Task._meta.get_field("status").choices
        )
        self.fields["status"].choices = status_choices

        priority_choices = [("", "All priorities")] + list(
            Task._meta.get_field("priority").choices
        )
        self.fields["priority"].choices = priority_choices

        self.fields["assignee"].choices = self.get_cached_assignee_choices()
        
    def get_cached_assignee_choices(self):
        cache_key = "task_filter_assignee_choices"
        choices = cache.get(cache_key)
        
        if choices is None:
            choices = [
                ("", "Anyone"),
                ("no_assignee", "No Assignee"),
            ]

            workers = Worker.objects.values_list(
                'id', 'username'
            ).order_by('username')
            for worker_id, username in workers:
                choices.append((str(worker_id), username))
            cache.set(cache_key, choices, 15 * 60)
            
        return choices
