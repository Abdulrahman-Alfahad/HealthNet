import datetime

from django import forms
from django.db.models import Q
from reservation.models import Appointment
from datetime import date, timedelta


class BaseAppointmentForm(forms.ModelForm):
    """
    A form for the Appointment model that doesn't have either of the two participants fields.
    This form is not meant to be used directly, but rather subclassed.
    """

    def clean_date(self):
        date = self.cleaned_data['date']
        # Validate that the appointment isn't set to a date in the past.
        if date < datetime.datetime.now().date():
            raise forms.ValidationError('Cannot schedule appointment with a past date.')

        return date

    def clean(self):
        cleaned_data = super(BaseAppointmentForm, self).clean()

        # Validate that the provided appointment time does not conflict with another already existing appointment.

        # Make sure the data required for this validation process are valid,
        # otherwise don't even bother running this validation
        if 'date' not in cleaned_data or 'start_time' not in cleaned_data or 'end_time' not in cleaned_data:
            return cleaned_data

        # Get the valid date/time data
        date = cleaned_data['date']
        start_time = cleaned_data['start_time']
        end_time = cleaned_data['end_time']

        # Construct a query to find the appointments that have time conflicts with this one
        cancelled_q = Q(cancelled=False)
        date_q = Q(date=date)
        start_time_q = Q(start_time__lte=start_time) & Q(end_time__gte=start_time)
        end_time_q = Q(start_time__lte=end_time) & Q(start_time__gte=end_time)
        overall_time = Q(start_time__gte=start_time) & Q(start_time__lte=end_time)
        time_q = start_time_q | end_time_q | overall_time
        q = cancelled_q & date_q & time_q
        # Exclude this record from the results, since an appointment cannot conflict with itself.
        if self.instance.id is not None:
            q = ~Q(pk=self.instance.id) & q

        # Count the number of results returned from the query and determine if a conflict exists.
        if Appointment.objects.filter(q).count() > 0:
            raise forms.ValidationError('The time slot is not available, please try a different one.')

        return cleaned_data

    date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Appointment
        fields = ['title', 'date', 'start_time', 'end_time']


class AppointmentFormForPatient(BaseAppointmentForm):
    """
    An Appointment form for patient users.
    This form contains the 'doctor' field, which is the other participant of the appointment.
    The value for the 'patient' field should be supplied when saving.
    """

    def save(self, creator=None, commit=True):
        """
        Save the object with the given creator as the 'patient' participant.
        :param creator: The patient participant.
        """

        appointment = super(AppointmentFormForPatient, self).save(commit=False)

        if creator is not None:
            appointment.patient = creator.patient
            appointment.end_time = (datetime.datetime.combine(date.today(), appointment.start_time) +
                                    timedelta(minutes=30)).time()

            if commit:
                appointment.save()
        else:
            appointment.save()

        return appointment

    class Meta:
        model = Appointment
        fields = BaseAppointmentForm.Meta.fields + ['doctor']
        exclude = ('end_time',)


class AppointmentFormForDoctor(BaseAppointmentForm):
    """
    An appointment form for doctor users.
    This form contains the 'patient' field, which is the other participant of the appointment.
    The value for the 'doctor' field should be supplied when saving.
    """

    def save(self, creator=None, commit=True):
        """
        Save the object with the given creator as the 'doctor' participant.
        :param creator: The doctor participant.
        """

        if creator is not None:
            appointment = super(AppointmentFormForDoctor, self).save(commit=False)
            appointment.doctor = creator.doctor

            if commit:
                appointment.save()
        else:
            appointment = super(AppointmentFormForDoctor, self).save(commit)

        return appointment

    class Meta:
        model = Appointment
        fields = BaseAppointmentForm.Meta.fields + ['patient']
