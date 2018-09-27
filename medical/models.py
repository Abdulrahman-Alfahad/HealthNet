from django.db import models
from datetime import date, timedelta
from hospital.models import Hospital, TreatmentSession
from account.models import Doctor, Patient
from .validator import validate_file_extension
import os


class Diagnosis(models.Model):
    treatment_session = models.ForeignKey(TreatmentSession, on_delete=models.CASCADE, null=True)

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, null=True)
    """A high level summary of this patient's condition, including any useful, medical information for the treatment"""
    summary = models.TextField()
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    update_timestamp = models.DateTimeField(auto_now=True)

    archived = models.BooleanField(default=False)

    def get_patient(self):
        if self.patient:
            return self.patient

        return self.treatment_session.patient

    def __str__(self):
        if self.summary:
            line = self.summary.split('\n')[0]
            if len(line) < 97:
                return line
            else:
                return line[:97] + '...'
        else:
            return "Diagnosis created at %s" % self.creation_timestamp.ctime()

    class Meta:
        permissions = (
            ('view_diagnosis', 'Can view diagnoses'),
            ('view_own_diagnoses', 'Can view own diagnoses')
        )


class Test(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT)
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.PROTECT)

    description = models.TextField()
    results = models.TextField()

    def content_file_name(self, filename):
        """
        Used to rename the file to pk of the doctor and test
        gives a unique name for each file
        :param filename: original filename
        :return: new filename
        """
        ext = filename.split('.')[-1]
        filename = "%s_%s.%s" % (self.doctor.id, self.id, ext)
        return os.path.join('medical/static/test_results', filename)

    file = models.FileField(default=None, upload_to=content_file_name, validators=[validate_file_extension])

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    uploaded = models.BooleanField(default=False)
    released = models.BooleanField(default=False)

    def status(self):
        if self.released:
            return 'released'
        elif self.uploaded:
            return 'uploaded'
        else:
            return 'pending'

    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        line = self.description.split('\n')[0]
        if len(line) < 77:
            return line
        else:
            return line[:77] + '...'

    class Meta:
        permissions = (
            ('request_test', 'Can request tests'),
            ('upload_test_results', 'Can upload test results'),
            ('release_test_results', 'Can release test results'),
            ('view_test_results', 'Can view tests'),
        )


class Drug(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ('remove_drug', 'Can remove drugs'),
            ('view_drug', 'Can view drugs'),
        )


class Prescription(models.Model):
    """
    Prescription class that has a diagnosis, doctor, drug, instructions for use
    which a prescribing doctor will create
    """
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT)
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    instruction = models.TextField()
    amount = models.IntegerField(default=1)
    cycle = models.IntegerField(null=True, blank=True, default=None)
    repeats = models.IntegerField(null=True, blank=True, default=None)
    creation_timestamp = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def pluralize_with_abbreviation(factor, unit):
        if factor == 1:
            return unit
        else:
            return '%d %ss' % (factor, unit)

    @staticmethod
    def pluralize(factor, unit):
        return ('%d %s' if factor == 1 else '%d %ss') % (factor, unit)

    def amount_str(self):
        return self.pluralize(self.amount, 'unit')

    def cycle_str(self):
        if not self.cycle:
            return 'N/A'

        if self.cycle % 30 == 0:
            return '%s (%s)' % (self.pluralize_with_abbreviation(self.cycle // 30, 'month'),
                                self.pluralize_with_abbreviation(self.cycle, 'day'))
        elif self.cycle % 7 == 0:
            return self.pluralize_with_abbreviation(self.cycle // 7, 'week')
        else:
            return self.pluralize_with_abbreviation(self.cycle, 'day')

    def quantity_info(self):
        if self.cycle:
            return '%s (refill every %s for %s)' % (self.amount_str(), self.cycle_str(), self.repeats_str())
        else:
            return '%s (one time)' % self.amount_str()

    def repeats_str(self):
        return self.pluralize(self.repeats, 'time')

    def expiration_date(self):
        return self.creation_timestamp.date() + timedelta(days=self.cycle)

    def active(self):
        return date.today() <= self.expiration_date()

    class Meta:
        permissions = (
            ('view_prescription', 'Can view prescriptions'),
            ('export_information', 'Can export information'),
        )
