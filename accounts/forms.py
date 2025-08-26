from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Position

Worker = get_user_model()


class WorkerCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        empty_label="Select your position (optional)",
    )

    class Meta(UserCreationForm.Meta):
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "email",
            "first_name",
            "last_name",
            "position",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = None
        self.fields["password2"].help_text = None

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Worker.objects.filter(email=email).exists():
            raise forms.ValidationError("User with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            if self.cleaned_data["position"]:
                user.position = self.cleaned_data["position"]
                user.save()
        return user
