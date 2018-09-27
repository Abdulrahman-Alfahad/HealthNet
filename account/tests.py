from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group, User, AnonymousUser
from django.contrib.auth import get_user
from django.core.urlresolvers import reverse
from datetime import datetime
from hospital.models import Hospital, TreatmentSession
from account.models import ProfileInformation, Patient, Administrator, Doctor, Nurse, \
    create_default_account, create_super_user
from account.forms import ProfileInformationForm, PatientCreationForm
from account.views import register_doctor, create_administrator, create_nurse
from .management.commands import setupgroups

DEFAULT_PROFILE_INFORMATION_DATA = {'gender': ProfileInformation.MALE, 'address': 'Test address', 'phone': '1234567890'}
PASSWORD = '$teamname'


def construct_form_data(username, extra):
    data = default_user_creation_form_data(username)
    data.update(DEFAULT_PROFILE_INFORMATION_DATA)
    if extra:
        data.update(extra)
    return data


def default_user_creation_form_data(username):
    return {
        'username': username, 'first_name': 'First', 'last_name': 'Last', 'email': 'e@mail.com',
        'password1': PASSWORD, 'password2': PASSWORD
    }


def default_patient_data():
    return {
        'emergency_contact_phone': '5153453230', 'proof_of_insurance': '12233455',
        'medical_information': 'allergies', 'preferred_hospital': Hospital.objects.first().id
    }


class PatientUnitTestCase(TestCase):
    PATIENT_USERNAME = 'patient'

    @classmethod
    def setUpTestData(cls):
        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        Group.objects.create(name='Patient')
        create_default_account(cls.PATIENT_USERNAME, PASSWORD, Patient, hospital)

    def test_get_current_treatment_session(self):
        patient = User.objects.get(username=self.PATIENT_USERNAME).patient

        treatment_session = patient.get_current_treatment_session()
        self.assertEqual(treatment_session, None, 'Expected no active treatment session.')

        TreatmentSession.objects.create(patient=patient, treating_hospital=Hospital.objects.first())
        treatment_session = patient.get_current_treatment_session()
        self.assertNotEqual(treatment_session, None, 'Expected an active treatment session.')

        treatment_session.discharge_timestamp = datetime.now()
        treatment_session.save()
        treatment_session = patient.get_current_treatment_session()
        self.assertEqual(treatment_session, None, 'Expected no active treatment session.')


class PatientDataValidationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Hospital.create_default()

    def test_patient_creation_valid(self):
        profile_info = ProfileInformationForm({'gender': ProfileInformation.FEMALE, 'address': '416 River St.', 'phone': '8784563456'})
        create_patient = PatientCreationForm({'emergency_contact_phone': '5153453230', 'medical_information': 'allergies',
                                              'preferred_hospital': Hospital.objects.first().id, 'proof_of_insurance': '12233455'})

        self.assertTrue(profile_info.is_valid(), 'Profile information form should pass validation.')
        self.assertTrue(create_patient.is_valid(), 'Patient form should pass validation.')

    def test_patient_creation_empty_fields(self):
        profile_info = ProfileInformationForm({'gender': '', 'address': '', 'phone': ''})
        create_patient = PatientCreationForm({'emergency_contact_phone': '', 'medical_information': '', 'preferred_hospital': '', 'proof_of_insurance': ''})

        self.assertFalse(profile_info.is_valid(), 'Profile information form should fail validation.')
        self.assertFalse(create_patient.is_valid(), 'Patient form should fail validation.')

        profile_info_errors = profile_info.errors
        self.assertTrue('gender' in profile_info_errors, 'Required field not reporting an error when no value is supplied.')
        self.assertTrue('address' in profile_info_errors, 'Required field not reporting an error when no value is supplied.')
        self.assertTrue('phone' in profile_info_errors, 'Required field not reporting an error when no value is supplied.')

        patient_errors = create_patient.errors
        self.assertTrue('preferred_hospital' in patient_errors, 'Required field not reporting an error when no value is supplied.')
        self.assertTrue('proof_of_insurance' in patient_errors, 'Required field not reporting an error when no value is supplied.')
        self.assertTrue('emergency_contact_phone' in patient_errors, 'Required field not reporting an error when no value is supplied.')


class PatientCreationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Group.objects.create(name='Patient')

        Hospital.create_default()

    def test_success(self):
        username = 'patient'
        response = self.client.post(reverse('account:register_patient'),
                                    construct_form_data(username, default_patient_data()))

        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Patient.objects.filter(user=user).exists(),
                        'Expected a new `Patient` object to be added to the database and associated with the new user.')
        self.assertTrue(user.groups.filter(name='Patient').exists(), 'Expected the new user to be in the "Patient" user group.')

        self.assertTrue(get_user(self.client).is_authenticated(), 'Expected to auto-login to the newly created account.')

        self.client.logout()
        self.assertTrue(self.client.login(username=username, password=PASSWORD),
                        'Expected to be able to log in to the new patient account.')

    def test_redirect_logged_in_users(self):
        username = 'patient'
        create_default_account(username, PASSWORD, Patient, Hospital.objects.first())

        self.client.login(username=username, password=PASSWORD)
        response = self.client.get(reverse('account:register_patient'))
        self.assertEqual(response.status_code, 302, 'Expected to be redirected (to the dashboard).')


class StaffAccountCreationTestCase(TestCase):
    SUPERUSER_USERNAME = 'admin'
    ADMINISTRATOR_USERNAME = 'admini'
    PATIENT_USERNAME = 'patient'

    hospital1 = None
    hospital2 = None

    @classmethod
    def setUpTestData(cls):
        setupgroups.Command().handle(quiet=True)

        cls.hospital1 = Hospital.objects.create(name='Test hospital 1', location='Test location 1')
        cls.hospital2 = Hospital.objects.create(name='Test hospital 2', location='Test location 2')

        create_super_user(cls.SUPERUSER_USERNAME, PASSWORD)
        create_default_account(cls.ADMINISTRATOR_USERNAME, PASSWORD, Administrator, cls.hospital1)
        create_default_account(cls.PATIENT_USERNAME, PASSWORD, Patient, cls.hospital1)

    def setUp(self):
        self.factory = RequestFactory()


class DoctorCreationTestCase(StaffAccountCreationTestCase):
    def test_successful(self):
        username = 'doctor0'
        request = self.factory.post(reverse('account:create_doctor'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = register_doctor(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Doctor.objects.filter(user=user).exists(),
                        'Expected a new `Doctor` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Doctor').exists(),
                        'Expected the new account to be in the "Doctor" user group.')
        self.assertEqual(user.doctor.hospital, self.hospital1, 'Expected the new account to be associated with the hospital "%s"' % self.hospital1.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

        username = 'doctor1'
        request = self.factory.post(reverse('account:create_doctor'), construct_form_data(username, {'hospital': self.hospital2.id}))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = register_doctor(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Doctor.objects.filter(user=user).exists(),
                        'Expected a new `Doctor` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Doctor').exists(),
                        'Expected the new account to be in the "Doctor" user group.')
        self.assertEqual(user.doctor.hospital, self.hospital2, 'Expected the new account to be associated with the hospital "%s"' % self.hospital2.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

    def test_failed_with_incomplete_values(self):
        username = 'doctor'

        request = self.factory.post(reverse('account:create_doctor'), {})
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = register_doctor(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertFalse(Doctor.objects.exists(), 'Expected failing to create a new doctor account.')

        request = self.factory.post(reverse('account:create_doctor'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = register_doctor(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertFalse(Doctor.objects.exists(), 'Expected failing to create a new doctor account.')

    def test_failed_with_insufficient_permission(self):
        username = 'doctor'

        request = self.factory.post(reverse('account:create_doctor'), construct_form_data(username, None))
        request.user = AnonymousUser()
        response = register_doctor(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new doctor account.')

        request = self.factory.post(reverse('account:create_doctor'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.PATIENT_USERNAME)
        response = register_doctor(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new doctor account.')


class NurseCreationTestCase(StaffAccountCreationTestCase):
    def test_successful(self):
        username = 'nurse0'
        request = self.factory.post(reverse('account:create_nurse'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = create_nurse(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Nurse.objects.filter(user=user).exists(),
                        'Expected a new `Nurse` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Nurse').exists(),
                        'Expected the new account to be in the "Nurse" user group.')
        self.assertEqual(user.nurse.hospital, self.hospital1, 'Expected the new account to be associated with the hospital "%s"' % self.hospital1.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

        username = 'nurse1'
        request = self.factory.post(reverse('account:create_nurse'), construct_form_data(username, {'hospital': self.hospital2.id}))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = create_nurse(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Nurse.objects.filter(user=user).exists(),
                        'Expected a new `Nurse` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Nurse').exists(),
                        'Expected the new account to be in the "Nurse" user group.')
        self.assertEqual(user.nurse.hospital, self.hospital2, 'Expected the new account to be associated with the hospital "%s"' % self.hospital2.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

    def test_failed_with_incomplete_values(self):
        username = 'nurse'

        request = self.factory.post(reverse('account:create_nurse'), {})
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = create_nurse(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertFalse(Nurse.objects.exists(), 'Expected failing to create a new nurse account.')

        request = self.factory.post(reverse('account:create_nurse'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = create_nurse(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertFalse(Nurse.objects.exists(), 'Expected failing to create a new nurse account.')

    def test_failed_with_insufficient_permission(self):
        username = 'nurse'

        request = self.factory.post(reverse('account:create_nurse'), construct_form_data(username, None))
        request.user = AnonymousUser()
        response = create_nurse(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new nurse account.')

        request = self.factory.post(reverse('account:create_nurse'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.PATIENT_USERNAME)
        response = create_nurse(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new nurse account.')


class AdministratorCreationTestCase(StaffAccountCreationTestCase):
    def test_administrator_account_creation_successful(self):
        username = 'administrator0'
        request = self.factory.post(reverse('account:create_administrator'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = create_administrator(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Administrator.objects.filter(user=user).exists(),
                        'Expected a new `Administrator` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Administrator').exists(),
                        'Expected the new account to be in the "Administrator" user group.')
        self.assertEqual(user.administrator.hospital, self.hospital1, 'Expected the new account to be associated with the hospital "%s"' % self.hospital1.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

        username = 'administrator1'
        request = self.factory.post(reverse('account:create_administrator'), construct_form_data(username, {'hospital': self.hospital2.id}))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = create_administrator(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertTrue(User.objects.filter(username=username).exists(),
                        'Expected a new user with the username "%s" to be added to the database.' % username)
        user = User.objects.get(username=username)
        self.assertTrue(Administrator.objects.filter(user=user).exists(),
                        'Expected a new `Administrator` object associated with the new user to be added to the database.')
        self.assertTrue(user.groups.filter(name='Administrator').exists(),
                        'Expected the new account to be in the "Administrator" user group.')
        self.assertEqual(user.administrator.hospital, self.hospital2, 'Expected the new account to be associated with the hospital "%s"' % self.hospital2.name)

        self.assertTrue(self.client.login(username=username, password=PASSWORD), 'Expected to be able to log in to the new account.')

    def test_failed_with_incomplete_values(self):
        username = 'administrator'

        administrator_count = Administrator.objects.count()
        request = self.factory.post(reverse('account:create_administrator'), {})
        request.user = User.objects.get(username=self.ADMINISTRATOR_USERNAME)
        response = create_administrator(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertEqual(Administrator.objects.count(), administrator_count, 'Expected failing to create a new administrator account.')

        administrator_count = Administrator.objects.count()
        request = self.factory.post(reverse('account:create_administrator'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.SUPERUSER_USERNAME)
        response = create_administrator(request)
        self.assertEqual(response.status_code, 200, 'Expected the account creation operation to be successful.')
        self.assertEqual(Administrator.objects.count(), administrator_count, 'Expected failing to create a new administrator account.')

    def test_failed_with_insufficient_permission(self):
        username = 'administrator'

        request = self.factory.post(reverse('account:create_administrator'), construct_form_data(username, None))
        request.user = AnonymousUser()
        response = create_administrator(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new administrator account.')

        request = self.factory.post(reverse('account:create_administrator'), construct_form_data(username, None))
        request.user = User.objects.get(username=self.PATIENT_USERNAME)
        response = create_administrator(request)
        self.assertEqual(response.status_code, 302,
                         'Expected a redirect response due to insufficient permission for creating a new administrator account.')
