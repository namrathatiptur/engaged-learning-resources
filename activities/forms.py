from django import forms


class ContactForm(forms.Form):
    """Public contact form; submissions are emailed to CONTACT_EMAIL."""

    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "you@university.edu",
                "inputmode": "email",
                "autocomplete": "email",
            }
        ),
    )
    subject = forms.CharField(
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Subject (optional)"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "How can we help?", "rows": 6}),
    )
    # Honeypot: real users never see or fill this; bots often do.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get("website"))
