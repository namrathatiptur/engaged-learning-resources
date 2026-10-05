"""Whether outgoing email can actually reach an inbox in this environment."""
from django.conf import settings

# Backends that never deliver mail. Fine for local development, a misconfiguration in production.
NON_DELIVERING_BACKENDS = (
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
)


def is_console_backend() -> bool:
    return getattr(settings, "EMAIL_BACKEND", "") in NON_DELIVERING_BACKENDS


def email_delivery_available() -> bool:
    """
    True when emails will be delivered (or, while DEBUG is on, printed to the terminal
    for the developer). False in production when no real mail backend is configured.
    """
    return settings.DEBUG or not is_console_backend()


def email_unavailable_response(request, *, heading=None, message=None, back_url=None, back_label=None):
    """503 page used when a feature needs email but none can be sent."""
    from django.shortcuts import render

    return render(
        request,
        "email_unavailable.html",
        {"heading": heading, "message": message, "back_url": back_url, "back_label": back_label},
        status=503,
    )
