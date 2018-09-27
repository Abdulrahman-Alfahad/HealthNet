from django.conf.urls import url
from . import views

app_name = 'index'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^patient/$', views.patient, name='patient'),
    url(r'^doctor/$', views.doctor, name='doctor'),
    url(r'^nurse/$', views.nurse, name='nurse'),
    url(r'^administrator/$', views.administrator, name='administrator'),
    url(r'^administrator/log/$', views.log, name='log'),
    url(r'^administrator/log/activity.log$', views.log, name='log'),
    url(r'^system_administrator/$', views.system_administrator, name='system_administrator'),
    url(r'^stephen$', views.stephen, name='stephen'),
]
