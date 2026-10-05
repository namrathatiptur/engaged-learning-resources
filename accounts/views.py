import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from config.email_status import email_delivery_available, email_unavailable_response

from .forms import SignUpForm, TeachOrangeAuthenticationForm

logger = logging.getLogger(__name__)


class TeachOrangeLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    authentication_form = TeachOrangeAuthenticationForm


class TeachOrangeLogoutView(LogoutView):
    next_page = reverse_lazy("home")


def register(request):
    if request.user.is_authenticated:
        return redirect("activities:list")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(
                request,
                "Your account was created successfully. Welcome to TeachOrange.",
            )
            return redirect("activities:list")
    else:
        form = SignUpForm()
    return render(request, "accounts/register.html", {"form": form})


class TeachOrangePasswordResetView(PasswordResetView):
    """
    Password reset that never claims an email was sent when it can't be:
    503 if production has no mail backend configured, or if sending fails.
    """

    def _unavailable(self):
        return email_unavailable_response(
            self.request,
            heading="Password reset email isn’t available right now",
            message="We couldn’t send the reset email, so nothing was sent. Please try again later.",
            back_url=reverse("accounts:login"),
            back_label="Back to log in",
        )

    def post(self, request, *args, **kwargs):
        if not email_delivery_available():
            logger.error("Password reset requested but no email backend is configured (console backend with DEBUG off).")
            return self._unavailable()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            logger.exception("Password reset email could not be sent")
            return self._unavailable()
