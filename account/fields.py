from django.forms import RegexField


class PhoneField(RegexField):
    """A form field that accepts a phone number."""

    def __init__(self, *args, **kwargs):
        error_messages = kwargs.get('error_messages') or {}
        error_messages['invalid'] = 'Please enter a valid phone number.'
        kwargs['error_messages'] = error_messages
        super(PhoneField, self).__init__(r'^([0-9]+)$', 10, 10, *args, **kwargs)
