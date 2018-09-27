from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views
from . import forms

app_name = 'account'
urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'account/common/login.html', 'authentication_form': forms.UserAuthenticationForm}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'account/common/logout.html'}, name='logout'),
    url(r'^patient/register/$', views.register_patient, name='register_patient'),
    url(r'^administrator/create/$', views.create_administrator, name='create_administrator'),
    url(r'^doctor/create/$', views.register_doctor, name='create_doctor'),
    url(r'^nurse/create/$', views.create_nurse, name='create_nurse'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^add/$', views.add_account, name='add_account'),
]
