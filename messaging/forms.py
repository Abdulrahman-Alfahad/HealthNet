from django import forms
from .models import Message
from django.contrib.auth.models import User


class MessageForm(forms.ModelForm):
    sender = None

    recipient_username = forms.CharField(
        label='Recipient',
        help_text='The username of the recipient.',
        required=True
    )

    def clean_recipient_username(self):
        recipient_username = self.cleaned_data.get('recipient_username')
        if recipient_username:
            try:
                recipient = User.objects.get(username=recipient_username)
                if recipient == self.sender:
                    raise forms.ValidationError("The recipient cannot be yourself. "
                                                "We just, you know, don't like that.")
                return recipient
            except User.DoesNotExist:
                raise forms.ValidationError('User with this username does not exist.')

    def save(self, commit=False):
        message = super(MessageForm, self).save(commit=False)
        message.sender = self.sender
        message.recipient = self.cleaned_data['recipient_username']
        message.save()

        return message

    class Meta:
        model = Message
        fields = ['recipient_username', 'content']
