from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    """
    Message model has a sender and recipient which will be the username of a recipient
    Each message has a timestamp when it is sent and the message text
    """
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name='received_messages')

    content = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
