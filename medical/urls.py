from django.conf.urls import url
from . import views

app_name = 'medical'
urlpatterns = [
    url(r'^drug/$', views.list_drug, name='list_drug'),
    url(r'^drug/add/$', views.add_drug, name='add_drug'),
    url(r'^drug/remove/(?P<drug_id>[0-9]+)/$', views.remove_drug, name='remove_drug'),
    url(r'^drug/update/(?P<drug_id>[0-9]+)/$', views.update_drug, name='update_drug'),
    url(r'^patient/$', views.view_patients, name='view_patients'),
    url(r'^patient_admin/$', views.view_patients_admin, name='view_patients_admin'),
    url(r'^patient/(?P<patient_id>[0-9]+)/$', views.view_medical_information, name='view_medical_information'),
    url(r'^diagnosis/create/(?P<patient_id>[0-9]+)/$', views.create_diagnosis, name='create_diagnosis'),
    url(r'^diagnosis/update/(?P<diagnosis_id>[0-9]+)/$', views.update_diagnosis, name='update_diagnosis'),
    url(r'^diagnosis/archive/(?P<diagnosis_id>[0-9]+)/$', views.archive_diagnosis, name='archive_diagnosis'),
    url(r'^prescriptions/(?P<patient_id>[0-9]+)/$', views.view_prescriptions, name='view_prescriptions'),
    url(r'^prescriptions/add/(?P<diagnosis_id>[0-9]+)/$', views.add_prescription, name='add_prescriptions'),
    url(r'^prescriptions/edit/(?P<prescription_id>[0-9]+)/$', views.edit_prescription, name='edit_prescriptions'),
    url(r'^prescriptions/remove/(?P<prescription_id>[0-9]+)/$', views.remove_prescription, name='remove_prescription'),
    url(r'^test/request/(?P<diagnosis_id>[0-9]+)/$', views.request_test, name='request_test'),
    url(r'^test/upload/(?P<test_id>[0-9]+)/$', views.upload_test_result, name='upload_test_result'),
    url(r'^test/test_view/$', views.test_view, name='test_view'),
    url(r'^test/release/(?P<test_id>[0-9]+)/$', views.release_test_result, name='release_test_result'),
    url(r'^test/test_detail/(?P<test_id>[0-9]+)/$', views.test_detail, name='test_detail'),
    url(r'^download_info/$', views.export_information, name='export_information'),
    url(r'^medical_info/$', views.medical_view_options, name='medical_info'),
    url(r'^medical_overview/$', views.medical_overview, name='medical_overview')
]
