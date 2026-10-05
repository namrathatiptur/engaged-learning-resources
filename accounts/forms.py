from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    UserCreationForm,
)
from django.contrib.auth.models import User


def validate_faculty_email(email: str) -> str:
    """Normalize email or raise ValidationError if the domain suffix is not allowed."""
    normalized = (email or "").strip().lower()
    suffixes = getattr(settings, "ALLOWED_EMAIL_SUFFIXES", ("@syr.edu",))
    if not normalized or not any(normalized.endswith(s) for s in suffixes):
        raise forms.ValidationError(
            "Use your Syracuse University email address (ending in "
            + ", ".join(suffixes)
            + ")."
        )
    return normalized


class SignUpForm(UserCreationForm):
    """
    Register with university email as login. Username is set to the email address.
    """

    username = forms.EmailField(
        label="University email",
        help_text="Use your Syracuse University email (netid@syr.edu). This will be your login.",
        max_length=150,
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "inputmode": "email",
                "placeholder": "netid@syr.edu",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["username"]
        if commit:
            user.save()
        return user

    def clean_username(self):
        return validate_faculty_email(self.cleaned_data["username"])


class TeachOrangeAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = forms.EmailInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "inputmode": "email",
                "placeholder": "netid@syr.edu",
            }
        )

    def clean_username(self):
        return validate_faculty_email(self.cleaned_data["username"])


class EduPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        return validate_faculty_email(self.cleaned_data["email"])

    def send_mail(
        self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None
    ):
        """
        Same as Django's, but let delivery errors propagate. Django 4.2 logs and swallows
        them, which would tell the user "check your email" even though nothing was sent.
        """
        from django.core.mail import EmailMultiAlternatives
        from django.template import loader

        subject = "".join(loader.render_to_string(subject_template_name, context).splitlines())
        body = loader.render_to_string(email_template_name, context)
        message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name:
            message.attach_alternative(loader.render_to_string(html_email_template_name, context), "text/html")
        message.send()
