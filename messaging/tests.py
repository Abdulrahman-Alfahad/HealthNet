from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from .models import Message
from . import views

SENDER_USERNAME = 'sender'
RECIPIENT_USERNAME = 'recipient'
NON_EXISTENT_USERNAME = 'nonexistent'
PASSWORD = '$teamname'


class SendMessageTestCase(TestCase):
    VALID_MESSAGE = 'A valid message'
    VIEW_NAME = 'messaging:send'

    @classmethod
    def setUpTestData(cls):
        cls.sender = User.objects.create_user(SENDER_USERNAME, 'e@mail.com', PASSWORD)
        cls.recipient = User.objects.create_user(RECIPIENT_USERNAME, 'e@mail.com', PASSWORD)

    def setUp(self):
        self.factory = RequestFactory()

    def test_successful(self):
        request = self.factory.post(reverse(self.VIEW_NAME), {
            'recipient_username': RECIPIENT_USERNAME,
            'content': self.VALID_MESSAGE
        })
        request.user = self.sender
        response = views.send_message(request)

        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        self.assertTrue(Message.objects.exists(), 'Expected a new message record to be created.')
        message = Message.objects.first()
        self.assertEqual(message.sender, self.sender, 'Expected the currently logged-in user to be the sender.')
        self.assertEqual(message.recipient, self.recipient,
                         'Expected the user with the given username to be the recipient.')
        self.assertEqual(message.content, self.VALID_MESSAGE)

    def test_failed_with_non_existent_username(self):
        request = self.factory.post(reverse(self.VIEW_NAME), {
            'recipient_username': NON_EXISTENT_USERNAME,
            'content': self.VALID_MESSAGE
        })
        request.user = self.sender
        response = views.send_message(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.exists())

    def test_failed_with_sender_username(self):
        request = self.factory.post(reverse(self.VIEW_NAME), {
            'recipient_username': SENDER_USERNAME,
            'content': self.VALID_MESSAGE
        })
        request.user = self.sender
        response = views.send_message(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.exists())

    def test_failed_with_empty_message(self):
        request = self.factory.post(reverse(self.VIEW_NAME), {
            'recipient_username': RECIPIENT_USERNAME,
            'content': ''
        })
        request.user = self.sender
        response = views.send_message(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.exists())

    def test_failed_not_logged_in(self):
        request = self.factory.post(reverse(self.VIEW_NAME), {
            'recipient_username': RECIPIENT_USERNAME,
            'content': self.VALID_MESSAGE
        })
        request.user = AnonymousUser()
        response = views.send_message(request)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.exists())
