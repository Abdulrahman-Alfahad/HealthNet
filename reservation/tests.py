import datetime
from django.test import TestCase
from reservation.forms import BaseAppointmentForm, AppointmentFormForPatient, AppointmentFormForDoctor
from django.contrib.auth.models import User
from account.models import Patient, Doctor
from hospital.models import Hospital
from reservation.models import Appointment


# Create your tests here.
class AppointmentFormTestCaseBase(TestCase):
    def setUp(self):
        hospital = Hospital.objects.create(name='Test hospital', location='Test location')
        user_doctor = User.objects.create_user(username='d', password='password')
        user_patient = User.objects.create_user(username='p', password='password')
        doctor = Doctor.objects.create(user=user_doctor, hospital=hospital)
        Patient.objects.create(user=user_patient, preferred_hospital=hospital, medical_information='',
                               proof_of_insurance='')

    def tomorrow(self):
        return (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    def yesterday(self):
        return (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    def patient(self):
        return Patient.objects.first()

    def doctor(self):
        return Doctor.objects.first()


class BaseAppointmentFormTestCase(AppointmentFormTestCaseBase):
    def test_success_scenario(self):
        base_apt = BaseAppointmentForm({'title': 'Check up', 'start_time': '4:30', 'end_time': '5:30',
                                        'date': self.tomorrow()})

        self.assertTrue(base_apt.is_valid(), 'Base form should be validated')

    def test_empty_scenario(self):
        base_apt = BaseAppointmentForm({'title': '', 'date': '', 'start_time': '', 'end_time': ''})

        self.assertFalse(base_apt.is_valid(), 'Form should fail because of blank sections')

        base_apt_errors = base_apt.errors
        self.assertTrue('title' in base_apt_errors, 'Field not reporting an error when field not supplied')
        self.assertTrue('date' in base_apt_errors, 'Field not reporting an error when blank')
        self.assertTrue('start_time' in base_apt_errors, 'Field not reporting an error when field not supplied')
        self.assertTrue('end_time' in base_apt_errors, 'Field not reporting an error when left blank')

    def test_past_date(self):
        form = BaseAppointmentForm({'title': 'Check up', 'start_time': '4:30', 'end_time': '5:30',
                                    'date': self.yesterday()})

        self.assertFalse(form.is_valid(), 'Base form should be validated')

        errors = form.errors
        self.assertTrue('date' in errors, 'Field not reporting error when scheduling an appointment with a past date.')

    def test_conflicting_times(self):
        Appointment.objects.create(title='appointment 1', patient=self.patient(), doctor=self.doctor(),
                                   date=self.tomorrow(), start_time='4:00', end_time='5:00')

        form = BaseAppointmentForm({'title': 'appointment 2', 'start_time': '4:30', 'end_time': '5:30',
                                    'date': self.tomorrow()})

        self.assertFalse(form.is_valid(),
                         'Form not reporting error when having time conflict with an existing appointment.')


class AppointmentFormForDoctorTestCase(AppointmentFormTestCaseBase):
    def test_success_scenario(self):
        apt_form_doctors = AppointmentFormForDoctor({'title': 'Check up', 'date': self.tomorrow(), 'start_time': '2:00',
                                                     'end_time': '3:00', 'patient': self.patient().id})

        self.assertTrue(apt_form_doctors.is_valid(), 'Appointment form for doctor should be validated')

    def test_empty_scenario(self):
        apt_form_doctors = AppointmentFormForDoctor({'title': '', 'date': '', 'start_time': '', 'end_time': '',
                                                     'patient': ''})

        self.assertFalse(apt_form_doctors.is_valid(), 'Form should fail because of blank sections')

        doctor_apt_errors = apt_form_doctors.errors
        self.assertTrue('patient' in doctor_apt_errors, 'Field not reporting an error when field not supplied')


class AppointmentFormForPatientTestCase(AppointmentFormTestCaseBase):
    def test_success_scenario(self):
        apt_form_patients = AppointmentFormForPatient({'title': 'Check up', 'date': self.tomorrow(), 'start_time':
            '2:00', 'doctor': self.doctor().id})

        self.assertTrue(apt_form_patients.is_valid(), 'Appointment form for patients should be validated')

    def test_empty_scenario(self):
        apt_form_patients = AppointmentFormForPatient({'title': '', 'date': '', 'start_time': '', 'doctor': ''})

        self.assertFalse(apt_form_patients.is_valid(), 'Form should fail because of blank sections')

        patient_apt_errors = apt_form_patients.errors
        self.assertTrue('doctor' in patient_apt_errors, 'Field not reporting an error when field not supplied')
