from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import Group, User

from hnet.logger import CreateLogEntry
from .models import Patient, Administrator, ProfileInformation, Doctor, Nurse
from .fields import PhoneField


class UserAuthenticationForm(auth_forms.AuthenticationForm):
    def confirm_login_allowed(self, user):
        super(UserAuthenticationForm, self).confirm_login_allowed(user)
        if user.is_active:
            profile_information = ProfileInformation.from_user(user)
            if profile_information is not None:
                if profile_information.account_type == Patient.ACCOUNT_TYPE:
                    CreateLogEntry(user, "Patient logged in.")
                elif profile_information.account_type == Doctor.ACCOUNT_TYPE:
                    CreateLogEntry(user, "Doctor logged in.")
                elif profile_information.account_type == Nurse.ACCOUNT_TYPE:
                    CreateLogEntry(user, "Nurse logged in.")
                elif profile_information.account_type == Administrator.ACCOUNT_TYPE:
                    CreateLogEntry(user, "Administrator logged in.")


class UserCreationForm(auth_forms.UserCreationForm):
    """A form used for creating new users. """

    def save(self, commit=True):
        """
        Save and, if commit is true, authenticate the newly created user.
        :return: The newly created user object.
        """
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            user = authenticate(username=self.cleaned_data['username'], password=self.cleaned_data['password1'])

        return user

    def save_as_patient_with_profile_information(self, patient_form, profile_information_form):
        """
        Save the information in this form and the given forms as a new patient user.
        :return: The newly created and saved `User` object (not `Patient` object).
        """
        user = self.save()
        patient_group = Group.objects.get(name='Patient')
        user.groups.add(patient_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Patient.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        patient = patient_form.save(commit=False)
        patient.user = user
        patient.save()

        return user

    def save_as_administrator_with_profile_information(self, administrator_form, profile_information_form):
        """
        Saves the information in this form and the given forms as a new administrator.
        :param administrator_form: An `AdministratorForm` object. 
        :param profile_information_form: A `ProfileInformationForm` object.
        :return: The newly created and saved `User` object (not `Administrator` object).
        """

        user = self.save()
        administrator_group = Group.objects.get(name='Administrator')
        user.groups.add(administrator_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Administrator.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_administrator = administrator_form.save(commit=False)
        new_administrator.user = user
        new_administrator.save()

        return user

    def save_as_administrator_by_creator_with_profile_information(self, creator, profile_information_form):
        """
        Saves the information in this form and the given form as a new administrator.
        The `hospital` field of the new `Administrator` account will be the same as that of `creator`.
        :param creator: An `Administrator` object, representing the person who created this account. 
        :param profile_information_form: A `ProfileInformationForm` object.
        :return: The newly created and saved `User` object (not `Administrator` object).
        """

        user = self.save()
        administrator_group = Group.objects.get(name='Administrator')
        user.groups.add(administrator_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Administrator.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_administrator = Administrator()
        new_administrator.user = user
        new_administrator.hospital = creator.hospital
        new_administrator.save()

        return user

    def save_as_doctor_with_profile_information(self, doctor_form, profile_information_form):
        """
        Saves the information in this form and the given form as a new doctor.
        This is used if the creator is a superuser.
        :param doctor_form: A 'DoctorForm' object
        :param profile_information_form: A 'ProfileInformationForm' object
        :return: The newly created and saved user object (not doctor object)
        """
        user = self.save()
        doctor_group = Group.objects.get(name='Doctor')
        user.groups.add(doctor_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Doctor.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_doctor = doctor_form.save(commit=False)
        new_doctor.user = user
        new_doctor.save()

        return user

    def save_as_doctor_by_creator_with_profile_information(self, creator, profile_information_form):
        """
        Saves the information in this form and the given form as a new doctor.
        This is used if the creator is an Administrator for a given hospital.
        :param creator: The 'Administrator' object that is creating the account
        :param profile_information_form: A 'ProfileInformationForm' object
        :return: The newly created and saved user object (not doctor object)
        """
        user = self.save()
        doctor_group = Group.objects.get(name='Doctor')
        user.groups.add(doctor_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Doctor.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_doctor = Doctor()
        new_doctor.user = user
        new_doctor.hospital = creator.hospital
        new_doctor.save()

        return user

    def save_as_nurse_by_creator_with_profile_information(self, creator, profile_information_form):
        """
        Saves the information in this form and the given form as a new nurse.
        The `hospital` field of the new `Nurse` account will be the same as that of `creator`.
        :param creator: An `Administrator` object, representing the person who created this account. 
        :param profile_information_form: A `ProfileInformationForm` object.
        :return: The newly created and saved `User` object (not `Nurse` object).
        """

        user = self.save()
        nurse_group = Group.objects.get(name='Nurse')
        user.groups.add(nurse_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Nurse.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_nurse = Nurse()
        new_nurse.user = user
        new_nurse.hospital = creator.hospital
        new_nurse.save()

        return new_nurse

    def save_as_nurse_with_profile_information(self, nurse_form, profile_information_form):
        """
        Saves the information in this form and the given form as a new nurse
        :param nurse_form:  A `NurseForm` object. 
        :param profile_information_form: A `ProfileInformationForm` object.
        :return: The newly created and saved user object (not nurse object)
        """

        user = self.save()
        nurse_group = Group.objects.get(name='Nurse')
        user.groups.add(nurse_group)
        user.save()

        profile_information = profile_information_form.save(commit=False)
        profile_information.account_type = Nurse.ACCOUNT_TYPE
        profile_information.user = user
        profile_information.save()

        new_nurse = nurse_form.save(commit=False)
        new_nurse.user = user
        new_nurse.save()

        return user

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username.startswith('.'):
            raise forms.ValidationError('Username cannot start with a \'.\' character.')

        return username

    class Meta(auth_forms.UserCreationForm.Meta):
        fields = auth_forms.UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileInformationForm(forms.ModelForm):
    """A form used for obtaining generic profile information relevant to all types of account. """

    phone = PhoneField()

    class Meta:
        model = ProfileInformation
        fields = ['gender', 'address', 'phone']


class PatientCreationForm(forms.ModelForm):
    """A form used for obtaining patient-specific information. """

    emergency_contact_phone = PhoneField(required=False,
                                         help_text='The phone number of an unregistered emergency contact. '
                                                   'You must provide this if you do not link with a registered patient.')

    def clean(self):
        cleaned_data = super(PatientCreationForm, self).clean()

        # Validate that at least one of emergency_contact and emergency_contact_phone is supplied.
        if 'emergency_contact' in cleaned_data and 'emergency_contact_phone' in cleaned_data:
            if cleaned_data['emergency_contact'] is None and not cleaned_data['emergency_contact_phone']:
                self.add_error('emergency_contact_phone',
                               'If you choose not to link with a registered patient account, '
                               'you must provide an emergency contact phone number.')

        return cleaned_data

    class Meta:
        model = Patient
        fields = ['medical_information', 'preferred_hospital', 'proof_of_insurance', 'emergency_contact',
                  'emergency_contact_phone']


class PatientChangeForm(PatientCreationForm):
    """A form used for updating patient-specific information. """

    def clean_emergency_contact(self):
        # Validate that a patient does not have himself as his emergency contact.
        if self.instance is not None:
            if self.instance == self.cleaned_data['emergency_contact']:
                raise forms.ValidationError('Your emergency contact cannot be yourself.')

        return self.cleaned_data['emergency_contact']


class DoctorCreationForm(forms.ModelForm):
    """A form used for obtaining doctor-specific information."""

    class Meta:
        model = Doctor
        # Will have to be modified because Doctors can work for multiple hospitals
        fields = ['hospital']


class AdministratorForm(forms.ModelForm):
    """A form used for obtaining administrator-specific information. """

    class Meta:
        model = Administrator
        fields = ['hospital']


class NurseForm(forms.ModelForm):
    """A form used for obtaining nurse-specific information. """

    class Meta:
        model = Nurse
        fields = ['hospital']
