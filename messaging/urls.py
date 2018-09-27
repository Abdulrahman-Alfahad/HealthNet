from django.conf.urls import url
from . import views

app_name = 'messaging'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^send/$', views.send_message, name='send'),
    url(r'^inbox/$', views.view_received_messages, name='inbox'),
    url(r'^outbox/$', views.view_sent_messages, name='outbox'),
]
