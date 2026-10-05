"""Template context processors."""
from .email_status import is_console_backend


def email_backend(request):
    """Expose the console-email developer hint (local development only, never in production)."""
    from django.conf import settings

    return {
        "email_is_console": settings.DEBUG and is_console_backend(),
    }
