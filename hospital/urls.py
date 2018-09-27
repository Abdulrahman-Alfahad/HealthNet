from django.conf.urls import url
from . import views

app_name = 'hospital'
urlpatterns = [
    url(r'^log/$', views.logView, name='log'),
    url(r'^log/(?P<page>[0-9]*)/$', views.logView, name='log'),
    url(r'^statistics/$', views.statisticsView, name='statistics'),
    url(r'^admit/(?P<patient_id>[0-9]+)/$', views.admit_patient, name='admit_patient'),
    url(r'^discharge/(?P<patient_id>[0-9]+)/$', views.discharge_patient, name='discharge_patient'),
    url(r'^doctor_transfer/(?P<patient_id>[0-9]+)/$', views.transfer_patient_as_doctor,
        name='transfer_patient_as_doctor'),
    url(r'^admin_transfer/(?P<patient_id>[0-9]+)/$', views.transfer_patient_as_admin, name='transfer_patient_as_admin'),
    url(r'^system_information/$', views.system_information, name='system_information')
]
