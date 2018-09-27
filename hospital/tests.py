from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, AnonymousUser
from account.management.commands import setupgroups
from account.models import Patient, Doctor, Nurse, create_default_account, Administrator
from medical.models import Diagnosis
from hospital.models import Hospital, TreatmentSession
from hospital import views

PATIENT_USERNAME = 'patient'
DOCTOR_USERNAME = 'doctor'
NURSE_USERNAME = 'nurse'
ADMINISTRATOR_USERNAME = 'admini'
PASSWORD = '$teamname'


class PatientAdmissionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        setupgroups.Command().handle(quiet=True)

        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        create_default_account(PATIENT_USERNAME, PASSWORD, Patient, hospital)
        create_default_account(DOCTOR_USERNAME, PASSWORD, Doctor, hospital)
        create_default_account(NURSE_USERNAME, PASSWORD, Nurse, hospital)

    def setUp(self):
        self.factory = RequestFactory()

    def test_doctor_successful(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        views.admit_patient(request, patient.id)

        self.assertTrue(TreatmentSession.objects.exists(), 'Expected a new treatment session to be created.')
        treatment_session = TreatmentSession.objects.first()
        self.assertEqual(treatment_session.patient, patient,
                         'Expected the new treatment session to be associated with the given patient.')
        self.assertEqual(treatment_session.discharge_timestamp, None, 'Unexpected discharge for patient.')

    def test_nurse_successful(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=NURSE_USERNAME)
        views.admit_patient(request, patient.id)

        self.assertTrue(TreatmentSession.objects.exists(), 'Expected a new treatment session to be created.')
        treatment_session = TreatmentSession.objects.first()
        self.assertEqual(treatment_session.patient, patient,
                         'Expected the new treatment session to be associated with the given patient.')
        self.assertEqual(treatment_session.discharge_timestamp, None, 'Unexpected discharge for patient.')

    def test_failed_permission(self):
        patient_user = User.objects.get(username=PATIENT_USERNAME)
        patient = patient_user.patient
        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = AnonymousUser()
        response = views.admit_patient(request, patient.id)

        self.assertEqual(response.status_code, 302, 'Expected to be redirected due to insufficient permission.')
        self.assertFalse(TreatmentSession.objects.exists(), 'Expected failing to create new treatment session.')

        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = patient_user
        response = views.admit_patient(request, patient.id)

        self.assertEqual(response.status_code, 302, 'Expected to be redirected due to insufficient permission.')
        self.assertFalse(TreatmentSession.objects.exists(), 'Expected failing to create new treatment session.')

    def test_failed_already_admitted(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        # Create & send the first request
        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        views.admit_patient(request, patient.id)
        # Create & send the second request
        request = self.factory.post(reverse('hospital:admit_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        views.admit_patient(request, patient.id)

        self.assertEqual(TreatmentSession.objects.count(), 1,
                         'Expected skipping treatment session creation since patient is already admitted.')

    def test_failed_non_post_request(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        request = self.factory.get(reverse('hospital:admit_patient', args=[patient.id]))
        request.user = User.objects.get(username=NURSE_USERNAME)
        response = views.admit_patient(request, patient.id)

        self.assertEqual(response.status_code, 302, 'Expected to be redirected.')
        self.assertFalse(TreatmentSession.objects.exists(),
                         'Expected skipping treatment session creation due to incorrect HTTP request method.')


class PatientDischargeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        setupgroups.Command().handle(quiet=True)

        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        create_default_account(PATIENT_USERNAME, PASSWORD, Patient, hospital)
        create_default_account(DOCTOR_USERNAME, PASSWORD, Doctor, hospital)
        create_default_account(NURSE_USERNAME, PASSWORD, Nurse, hospital)

    def setUp(self):
        self.factory = RequestFactory()

    def test_empty_successful(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)

        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        self.assertFalse(TreatmentSession.objects.exists(),
                         'Expected the treatment session to be deleted since it\' empty (no diagnoses).')

    def test_non_empty_successful(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        Diagnosis.objects.create(treatment_session=treatment_session, patient=patient, summary='Diagnosis summary')

        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)

        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        self.assertTrue(TreatmentSession.objects.exists(),
                        'Expected the treatment session to be be kept since it\' empty (no diagnoses).')
        treatment_session = TreatmentSession.objects.first()
        self.assertNotEqual(treatment_session.discharge_timestamp, None,
                            'Expected the discharge timestamp to be assigned when discharging.')

    def test_failed_already_discharged(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        # Admit the patient
        TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        # Create & send request
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)
        # Initial assertion.
        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        # Send request a second time.
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)
        # More Assertions.
        self.assertEqual(response.status_code, 302, 'Expected to be redirected since already discharged.')
        self.assertFalse(TreatmentSession.objects.exists(),
                         'Expected the treatment session to be deleted since it\' empty (no diagnoses).')

        # Admit the patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        Diagnosis.objects.create(treatment_session=treatment_session, patient=patient, summary='Diagnosis summary')
        # Create & send request
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)
        # Initial assertion.
        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        # Send request a second time.
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)
        # More Assertions.
        self.assertEqual(response.status_code, 302, 'Expected to be redirected since already discharged.')
        self.assertTrue(TreatmentSession.objects.exists(),
                        'Expected the treatment session to be be kept since it\' empty (no diagnoses).')
        treatment_session = TreatmentSession.objects.first()
        self.assertNotEqual(treatment_session.discharge_timestamp, None,
                            'Expected the discharge timestamp to be assigned when discharging.')

    def test_failed_not_admitted(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        # Create a different patient account to admit.
        admitted_patient_username = 'admitted_patient'
        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        admitted_patient = create_default_account(admitted_patient_username, PASSWORD, Patient, hospital).patient
        # Admit the second patient account.
        TreatmentSession.objects.create(patient=admitted_patient, treating_hospital=hospital)
        # Create & send request to discharge the first patient account.
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=DOCTOR_USERNAME)
        response = views.discharge_patient(request, patient.id)
        # Make Assertions.
        self.assertEqual(response.status_code, 302, 'Expected to be redirected since patient not admitted.')
        self.assertEqual(TreatmentSession.objects.count(), 1,
                         'Expected no changes to any treatment session since the requested patient isn\'t admitted.')

    def test_failed_permission_nurse(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        request = self.factory.post(reverse('hospital:discharge_patient', args=[patient.id]), {})
        request.user = User.objects.get(username=NURSE_USERNAME)
        response = views.discharge_patient(request, patient.id)

        self.assertEqual(response.status_code, 302, 'Expected to be redirected due to insufficient permission.')
        self.assertTrue(TreatmentSession.objects.exists(),
                        'Expected no changes to any treatment session due to insufficient permission.')


class PatientTransferTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        setupgroups.Command().handle(quiet=True)

        cls.old_hospital = Hospital.objects.create(name='Old Hospital')
        cls.new_hospital = Hospital.objects.create(name='New Hospital')
        create_default_account(PATIENT_USERNAME, PASSWORD, Patient, cls.new_hospital)
        create_default_account(DOCTOR_USERNAME, PASSWORD, Doctor, cls.new_hospital)
        create_default_account(ADMINISTRATOR_USERNAME, PASSWORD, Administrator, cls.old_hospital)
        create_default_account(NURSE_USERNAME, PASSWORD, Nurse, cls.new_hospital)

    def setUp(self):
        self.factory = RequestFactory()

    def test_successful_administrator(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=self.old_hospital)

        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]),
                                    {'treating_hospital': self.new_hospital.id})
        request.user = User.objects.get(username=ADMINISTRATOR_USERNAME)
        response = views.transfer_patient_as_admin(request, patient.id)

        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        self.assertTrue(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                        'Expected a new treatment session referencing the old one to be added to the database.')
        new_session = TreatmentSession.objects.get(previous_session=treatment_session)
        self.assertNotEqual(new_session.previous_session.discharge_timestamp, None,
                            'Expected the patient to be discharged from the old treatment session ')
        self.assertEqual(new_session.treating_hospital, self.new_hospital,
                         "Expected the new treatment session to be associated with the new hospital.")

    def test_successful_doctor(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=self.old_hospital)

        doctor = User.objects.get(username=DOCTOR_USERNAME)
        request = self.factory.post(reverse('hospital:transfer_patient_as_doctor', args=[patient.id]))
        request.user = doctor
        response = views.transfer_patient_as_doctor(request, patient.id)

        self.assertEqual(response.status_code, 200, 'Expected the operation to be successful.')
        self.assertTrue(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                        'Expected a new treatment session referencing the old one to be added to the database.')
        new_session = TreatmentSession.objects.get(previous_session=treatment_session)
        self.assertNotEqual(new_session.previous_session.discharge_timestamp, None,
                            'Expected the patient to be discharged from the old treatment session ')
        new_session = TreatmentSession.objects.get(previous_session=treatment_session)
        self.assertEqual(new_session.treating_hospital, doctor.doctor.hospital,
                         "Expected the new treatment session to be at the doctor's hospital")

    def test_failed_not_logged_in(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=self.old_hospital)
        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]),
                                    {'treating_hospital': self.new_hospital.id})
        request.user = AnonymousUser()
        response = views.transfer_patient_as_admin(request, patient.id)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for transferring a patient.')
        self.assertFalse(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                         'Expected no new treatment session referencing the old one to be added to the database.')
        self.assertEqual(treatment_session.discharge_timestamp, None,
                         'Expected the patient to not be discharged from the old hospital.')
        self.assertEqual(TreatmentSession.objects.count(), 1, 'Expected no changes to the database.')

    def test_failed_no_permissions(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient
        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=self.old_hospital)
        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]),
                                    {'treating_hospital': self.new_hospital.id})
        request.user = User.objects.get(username=PATIENT_USERNAME)
        response = views.transfer_patient_as_admin(request, patient.id)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for transferring a patient.')
        self.assertFalse(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                         'Expected no new treatment session referencing the old one to be added to the database.')
        self.assertEqual(treatment_session.discharge_timestamp, None,
                         'Expected the patient to not be discharged from the old hospital.')
        self.assertEqual(TreatmentSession.objects.count(), 1, 'Expected no changes to the database.')

        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]),
                                    {'treating_hospital': self.new_hospital.id})
        request.user = User.objects.get(username=NURSE_USERNAME)
        response = views.transfer_patient_as_admin(request, patient.id)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for transferring a patient.')
        self.assertFalse(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                         'Expected no new treatment session referencing the old one to be added to the database.')
        self.assertEqual(treatment_session.discharge_timestamp, None,
                         'Expected the patient to not be discharged from the old hospital.')
        self.assertEqual(TreatmentSession.objects.count(), 1, 'Expected no changes to the database.')

    def test_failed_no_treating_hospital(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient

        treatment_session = TreatmentSession.objects.create(patient=patient, treating_hospital=self.old_hospital)
        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]), {})
        request.user = User.objects.get(username=ADMINISTRATOR_USERNAME)
        response = views.transfer_patient_as_admin(request, patient.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TreatmentSession.objects.count(), 1, 'Expected no changes to the database.')
        self.assertFalse(TreatmentSession.objects.filter(previous_session=treatment_session).exists(),
                         'Expected no new treatment session referencing the old one to be added to the database.')
        self.assertEqual(treatment_session.discharge_timestamp, None,
                         'Expected the patient to not be discharged from the old hospital.')

    def test_failed_patient_not_admitted(self):
        patient = User.objects.get(username=PATIENT_USERNAME).patient

        request = self.factory.post(reverse('hospital:transfer_patient_as_admin', args=[patient.id]),
                                    {'treating_hospital': self.new_hospital.id})
        request.user = User.objects.get(username=ADMINISTRATOR_USERNAME)
        response = views.transfer_patient_as_admin(request, patient.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TreatmentSession.objects.exists(),
                         'Expected no new treatment session to be added to the database.')


class ViewStatisticsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        setupgroups.Command().handle(quiet=True)

        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        create_default_account(PATIENT_USERNAME, PASSWORD, Patient, hospital)
        create_default_account(DOCTOR_USERNAME, PASSWORD, Doctor, hospital)
        create_default_account(NURSE_USERNAME, PASSWORD, Nurse, hospital)
        create_default_account(ADMINISTRATOR_USERNAME, PASSWORD, Administrator, hospital)

    def setUp(self):
        self.factory = RequestFactory()

    def test_redirect(self):
        response = self.client.get(reverse("hospital:statistics"))
        self.assertEqual(response.status_code, 302, 'Expected to view statistics page.')
