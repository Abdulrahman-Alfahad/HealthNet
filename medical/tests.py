from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from medical.models import Test, Diagnosis
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models import create_default_account, Patient, Doctor
from hospital.models import Hospital


class UploadFileTest(TestCase):
    def setup(self):
        self.factory = RequestFactory()

    def test_upload_file(self):
        doctor_username = 'doctor'
        patient_username = 'patient'
        password = '$teamname'
        hospital = Hospital.create_default()
        Group.objects.create(name='Patient')
        Group.objects.create(name='Doctor')
        create_default_account(doctor_username, password, Doctor, hospital)
        create_default_account(patient_username, password, Patient, hospital)
        doctor = User.objects.get(username=doctor_username).doctor
        patient = User.objects.get(username=patient_username).patient
        diagnosis = Diagnosis.objects.create(patient=patient)
        test = Test.objects.create(doctor=doctor, diagnosis=diagnosis, description="", results=SimpleUploadedFile('file.txt', b'test file'))
        response = self.client.post(reverse('medical:upload_test_result', args=[test.id]))
        self.assertEqual(response.status_code, 302, 'Expected to upload test result.')
