from django.db import models
from datetime import date, timedelta
from functools import reduce
from account.models import Patient, Doctor, Nurse
from reservation.models import Appointment
from hospital.models import TreatmentSession


def format_timedelta(delta):
    total_seconds = delta.seconds
    hours = total_seconds // 3600
    minutes = total_seconds % 3600 // 60
    seconds = total_seconds % 60

    return '{} days {:02}h {:02}m {:02}s'.format(delta.days, hours, minutes, seconds)


class Statistics:
    def __init__(self, hospital):
        self.hospital = hospital

    def calculate(self):
        return ["Number of patients visiting the hospital : " + str(self.num_of_patients()),
                "Average visits per patient : " + str(self.average_visits_per_patient()),
                "Average length of stay : " + format_timedelta(self.average_length_of_stay()),
                "Number of prescriptions given : " + str(self.num_prescriptions_given()),
                "Number of Doctors : " + str(self.num_of_doctors()),
                "Number of Nurses : " + str(self.num_of_nurses()),
                "Appointments today : " + str(self.num_of_appointments_today())]

    def num_of_patients(self):
        treatment_session_query = TreatmentSession.objects.filter(discharge_timestamp=None).filter(treating_hospital=self.hospital)
        return Patient.objects.filter(treatmentsession__in=treatment_session_query).count()

    def num_of_doctors(self):
        return Doctor.objects.filter(hospital=self.hospital).filter(user__is_active=True).count()

    def num_of_nurses(self):
        return Nurse.objects.filter(hospital=self.hospital).filter(user__is_active=True).count()

    def num_of_appointments_today(self):
        return Appointment.objects.filter(cancelled=False).filter(date=date.today()).filter(doctor__hospital=self.hospital).count()

    def average_visits_per_patient(self):
        treatment_session_query = TreatmentSession.objects.filter(treating_hospital=self.hospital)
        query_results = treatment_session_query.aggregate(
            visit_count=models.Count('id'),
            patient_count=models.Count('patient', distinct=True)
        )
        if query_results['patient_count'] == 0:
            return 0
        else:
            return query_results['visit_count'] / query_results['patient_count']

    def average_length_of_stay(self):
        treatment_session = TreatmentSession.objects.exclude(discharge_timestamp=None).filter(treating_hospital=self.hospital)
        if treatment_session.count() == 0:
            return timedelta()
        else:
            total_time = reduce(lambda acc, x: acc + (x.discharge_timestamp - x.admission_timestamp), treatment_session, timedelta())
            return total_time / treatment_session.count()

    def num_prescriptions_given(self):
        from medical.models import Prescription
        return Prescription.objects.filter(doctor__hospital=self.hospital).count()

    def __str__(self):
        return "Statistics for " + self.hospital.name
