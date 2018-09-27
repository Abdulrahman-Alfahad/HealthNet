from django import forms
from hnet.logger import CreateLogEntry


class StephenLoginForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(max_length=254)
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    error_messages = {
        'invalid_login': "Please enter a correct %(username)s and password. "
                         "Note that both fields may be case-sensitive."
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            if username != 'stephen' or password != 'stephen1':
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
            else:
                CreateLogEntry("STEPHEN", " HAS LOGGED IN.")
        return self.cleaned_data
