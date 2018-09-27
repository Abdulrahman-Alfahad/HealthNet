from django import forms
from .models import TreatmentSession
from account.models import Doctor



class TransferForm(forms.ModelForm):
    """
    A form for obtaining the hospital a patient should be transferred to.
    """

    def save_by_admin(self, patient, old_session):
        treatment_session = self.save(commit=False)
        treatment_session.patient = patient
        treatment_session.previous_session = old_session
        treatment_session.save()

    class Meta:
        model = TreatmentSession
        fields = ['treating_hospital']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TransferForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['treating_hospital'].queryset = \
                self.fields['treating_hospital'].queryset.exclude(administrator=user.administrator)
