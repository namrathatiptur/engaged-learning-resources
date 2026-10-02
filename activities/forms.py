from django import forms


class ContactForm(forms.Form):
    """Public contact form; submissions are emailed to CONTACT_EMAIL."""

    REQUEST_TYPES = [
        ("consultation", "Consultation request"),
        ("activity", "Question about an activity"),
        ("access", "Account or materials access"),
        ("contribute", "Contribute an activity"),
        ("feedback", "Website feedback"),
        ("other", "Something else"),
    ]

    request_type = forms.ChoiceField(
        label="Type of request",
        choices=[("", "Choose a request type")] + REQUEST_TYPES,
        widget=forms.Select(attrs={"aria-describedby": "request_type-hint"}),
    )
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
    institution = forms.CharField(
        max_length=160,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "University, department, or school", "autocomplete": "organization"}
        ),
    )
    subject = forms.CharField(
        max_length=160,
        widget=forms.TextInput(attrs={"placeholder": "A short summary"}),
    )
    message = forms.CharField(
        min_length=10,
        max_length=5000,
        widget=forms.Textarea(attrs={"placeholder": "How can we help?", "rows": 6}),
    )
    # Honeypot: real users never see or fill this; bots often do.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get("website"))

    def request_type_label(self) -> str:
        return dict(self.REQUEST_TYPES).get(self.cleaned_data.get("request_type"), "")
