from django import forms
from django.utils.translation import gettext_lazy as _


class EmailChangeForm(forms.Form):
    """Form for user email address"""

    email = forms.EmailField(help_text=_("Enter a new email address"))
