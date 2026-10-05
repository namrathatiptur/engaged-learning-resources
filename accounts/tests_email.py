from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings

CONSOLE = "django.core.mail.backends.console.EmailBackend"
LOCMEM = "django.core.mail.backends.locmem.EmailBackend"


class PasswordResetEmailAvailabilityTests(TestCase):
    def setUp(self):
        User.objects.create_user("faculty@syr.edu", "faculty@syr.edu", "pw-12345678")

    @override_settings(DEBUG=False, EMAIL_BACKEND=CONSOLE)
    def test_production_without_mail_backend_returns_503(self):
        resp = self.client.post("/accounts/password-reset/", {"email": "faculty@syr.edu"})
        self.assertEqual(resp.status_code, 503)
        self.assertContains(resp, "isn’t available right now", status_code=503)
        self.assertNotContains(resp, "Check your email", status_code=503)

    @override_settings(DEBUG=False, EMAIL_BACKEND=LOCMEM)
    def test_configured_mail_backend_sends_and_redirects(self):
        resp = self.client.post("/accounts/password-reset/", {"email": "faculty@syr.edu"})
        self.assertRedirects(resp, "/accounts/password-reset/done/")
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(DEBUG=False, EMAIL_BACKEND=LOCMEM)
    def test_send_failure_returns_503(self):
        with mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("smtp down")):
            resp = self.client.post("/accounts/password-reset/", {"email": "faculty@syr.edu"})
        self.assertEqual(resp.status_code, 503)

    @override_settings(DEBUG=False, EMAIL_BACKEND=LOCMEM)
    def test_unknown_address_still_redirects_without_revealing_accounts(self):
        resp = self.client.post("/accounts/password-reset/", {"email": "nobody@syr.edu"})
        self.assertRedirects(resp, "/accounts/password-reset/done/")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEBUG=True, EMAIL_BACKEND=CONSOLE)
    def test_console_hint_shown_only_in_local_development(self):
        resp = self.client.get("/accounts/password-reset/done/")
        self.assertContains(resp, "Console email mode")
        with override_settings(DEBUG=False):
            resp = self.client.get("/accounts/password-reset/done/")
        self.assertNotContains(resp, "Console email mode")


class ContactEmailAvailabilityTests(TestCase):
    valid = {
        "request_type": "consultation",
        "name": "Ada Lovelace",
        "email": "ada@university.edu",
        "subject": "Syllabus redesign",
        "message": "We would like help redesigning a syllabus.",
    }

    @override_settings(DEBUG=False, EMAIL_BACKEND=CONSOLE)
    def test_production_without_mail_backend_returns_503_and_keeps_message(self):
        resp = self.client.post("/contact/", self.valid)
        self.assertEqual(resp.status_code, 503)
        self.assertContains(resp, "nothing was sent", status_code=503)
        self.assertContains(resp, "We would like help redesigning a syllabus.", status_code=503)

    @override_settings(DEBUG=False, EMAIL_BACKEND=LOCMEM)
    def test_send_failure_returns_503(self):
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("smtp down")):
            resp = self.client.post("/contact/", self.valid)
        self.assertEqual(resp.status_code, 503)

    @override_settings(DEBUG=False, EMAIL_BACKEND=LOCMEM)
    def test_configured_mail_backend_sends(self):
        resp = self.client.post("/contact/", self.valid)
        self.assertRedirects(resp, "/contact/")
        self.assertEqual(len(mail.outbox), 1)
