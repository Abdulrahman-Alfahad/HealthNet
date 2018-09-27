from datetime import date, timedelta
from django.db import models
from account.models import Patient, Doctor, get_account_from_user


class Appointment(models.Model):
    """
    A model object that stores an appointment's information.
    Replaced 'participants' variable in design document with 'doctor' and 'patient'.
    """
    title = models.CharField(max_length=50)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return self.view_appointment()

    def view_appointment(self):
        return "Doctor: " + self.doctor.__str__() + ".\nPatient: " + self.patient.__str__() + \
               ".\nDate: " + self.date.__str__() + \
               ".\nTime: " + self.start_time.__str__() + " - " + self.end_time.__str__() + "."

    def accessible_by_user(self, user):
        return self.patient.user == user or self.doctor.user == user

    @classmethod
    def get_for_user_in_year_in_month(cls, user, year, month):
        return user.appointment_set.exclude(cancelled=True).filter(date__year=year).filter(date__month=month).order_by(
            'date', 'start_time')

    @classmethod
    def get_for_user_in_week_starting_at_date(cls, user, starting_date):
        """
        Get the list of appointments this user have in the week starting at the given date.
        :param user: A user object.
        :param starting_date: A datetime.date object representing the first day of the week.
        :return: The list of appointments this user have in the week;
                 Or, an empty list if the user doesn't have any appointment;
                 Or, None if the user is a type of account that's not supposed to have any appointment.
        """

        account = get_account_from_user(user)
        try:
            return account.appointment_set.exclude(cancelled=True).filter(date__gte=starting_date).filter(
                date__lt=starting_date + timedelta(days=7)).order_by('date', 'start_time')
        except AttributeError:
            return None

    @classmethod
    def get_for_user_in_date(cls, user, date):
        return user.appointment_set.exclude(cancelled=True).filter(date=date).order_by('start_time')

    class Meta:
        permissions = (
            ('cancel_appointment', 'Can cancel appointment'),
            ('view_appointment', 'Can view appointments'),
        )
