from django import forms
from django.contrib.auth import get_user_model

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


class TaskFilterForm(forms.Form):
    search = forms.CharField(
        label="Search",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by name or description"
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
    assignee = forms.ModelChoiceField(
        label="Assignee",
        required=False,
        queryset=Worker.objects.all(),
        empty_label="Anyone",
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status_choices = [("", "All statuses")] + list(Task._meta.get_field("status").choices)
        priority_choices = [("", "All priorities")] + list(Task._meta.get_field("priority").choices)
        self.fields["status"].choices = status_choices
        self.fields["priority"].choices = priority_choices