from django import forms
from .models import Drug, Diagnosis, Test, Prescription
from account.models import Patient


class DrugForm(forms.ModelForm):
    """
    A form for obtaining information related to a drug.
    Can be used for adding new drugs as well as editing existing drugs.
    """

    class Meta:
        model = Drug
        fields = ['name', 'description']


class DiagnosisForm(forms.ModelForm):
    def save_for_patient(self, patient):
        diagnosis = self.save(commit=False)

        diagnosis.patient = patient

        treatment_session = patient.get_current_treatment_session()
        if treatment_session:
            diagnosis.treatment_session = treatment_session
        else:
            pass

        diagnosis.save()

        return diagnosis

    class Meta:
        model = Diagnosis
        fields = ['summary']


class TestForm(forms.ModelForm):
    """
    A form for obtaining information for a medical test.
    """

    def save_for_diagnosis(self, doctor, diagnosis):
        test = self.save(commit=False)
        test.doctor = doctor
        test.diagnosis = diagnosis
        test.save()

        return test

    class Meta:
        model = Test
        fields = ['description']


class TestResultsForm(forms.ModelForm):
    """
    A form for obtaining test results in text form.
    """

    def uploadfile(self, file, commit=True):
        test = super(TestResultsForm, self).save(commit=commit)
        test.file = file
        test.uploaded = True
        test.save()

    def save(self, commit=True):
        test = super(TestResultsForm, self).save(commit=commit)
        test.uploaded = True
        test.save()

        return test

    class Meta:
        model = Test
        fields = ['results', 'file']


class PrescriptionForm(forms.ModelForm):
    def save_to_diagnosis_by_doctor(self, diagnosis, doctor, commit=True):
        prescription = super(PrescriptionForm, self).save(commit=False)
        prescription.diagnosis = diagnosis
        prescription.doctor = doctor

        if commit:
            prescription.save()

        return prescription

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Cannot prescribe 0 or less units of drugs.')

        return amount

    def clean_cycle(self):
        cycle = self.cleaned_data.get('cycle')
        if cycle is not None and cycle <= 0:
            raise forms.ValidationError('Invalid value. Cycle duration must be greater than 0.')

        return cycle

    def clean_repeats(self):
        repeats = self.cleaned_data.get('repeats')
        if repeats is not None and repeats <= 0:
            raise forms.ValidationError('Invalid value. Repeat count must be greater than 0.')

        return repeats

    def clean(self):
        cleaned_data = super(PrescriptionForm, self).clean()
        repeats = self.cleaned_data.get('repeats')
        cycle = self.cleaned_data.get('cycle')

        if (repeats is None) != (cycle is None):
            raise forms.ValidationError('Cycle and repeats must be given at the same time.')

        return cleaned_data

    class Meta:
        model = Prescription
        fields = ['drug', 'instruction', 'amount', 'cycle', 'repeats']
