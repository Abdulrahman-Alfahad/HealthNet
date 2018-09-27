from django.db import models


class Hospital(models.Model):
    """A model that describes the basic information of a hospital."""

    name = models.CharField(max_length=30)
    location = models.CharField(max_length=200)

    """A flag indicating whether or not this hospital is operational. Remove a hospital by setting this flag to False."""
    operational = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @staticmethod
    def create_default():
        return Hospital.objects.create(name='Test hospital', location='Test location')

    class Meta:
        permissions = (
            ('can_view_system_information', 'Can view system information'),
        )


class TreatmentSession(models.Model):
    """
    A model object that stores information of a patient's stay at a hospital.
    """

    patient = models.ForeignKey('account.Patient', on_delete=models.PROTECT)

    """The hospital at which the patient received his treatment."""
    treating_hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT)

    """The time when the patient was admitted to the hospital and started his treatment."""
    admission_timestamp = models.DateTimeField(auto_now_add=True)
    """The time when the treatment finished and the patient was discharged."""
    discharge_timestamp = models.DateTimeField(null=True, blank=True, default=None)

    """
    The patient may have received some treatment (possibly at another hospital) before this one.
    Reference to a treatment session before this one, if there is one; NULL, if there isn't.
    """
    previous_session = models.OneToOneField('self', on_delete=models.CASCADE, null=True, blank=True, default=None,
                                            related_name='next_session')

    """
    Any additional medical or non-medical notes about the patient that might help with any future treatment for this patient.
    """
    notes = models.TextField(blank=True)

    class Meta:
        permissions = (
            ('view_treatmentsession', 'Can view treatment sessions'),
            ('discharge_patient', 'Can discharge patient'),
            ('transfer_patient_any_hospital', 'Can transfer patient to any hospital'),
            ('transfer_patient_receiving_hospital', "Can transfer patient to user's hospital")
        )
