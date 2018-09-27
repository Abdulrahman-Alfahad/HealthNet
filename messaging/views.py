from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm


@login_required
def index(request):
    return render(request, 'messaging/index.html')


@login_required
def send_message(request):
    """ Send a message from one user to another through the use of the form"""
    if request.method == 'POST':
        form = MessageForm(request.POST)
        form.sender = request.user
        if form.is_valid():
            form.save()
            return render(request, 'messaging/index.html')
    else:
        form = MessageForm()

    return render(request, 'messaging/send.html', {'form': form})


@login_required
def view_received_messages(request):
    """"Get all the messages corresponding to the user"""
    messages = Message.objects.filter(recipient=request.user)
    return render(request, 'messaging/inbox.html', {'message_list': messages})


@login_required
def view_sent_messages(request):
    """ filter and view all sent messages from a given user"""
    messages = Message.objects.filter(sender=request.user)
    return render(request, 'messaging/outbox.html', {'message_list': messages})
