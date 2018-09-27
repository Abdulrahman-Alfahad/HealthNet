from django.db import models
from hospital.models import Hospital, TreatmentSession
from django.contrib.auth.models import User, Group


def create_super_user(username, password):
    """
    Create & save a `User` object, and configure it to be a super user. 
    :return: The newly created & saved `User` object.
    """
    super_user = User.objects.create_user(username, 'e@mail.com', password)
    super_user.is_superuser = True
    super_user.is_staff = True
    super_user.save()
    return super_user


def create_default_account(username, password, account_class, hospital):
    """
    Create & save a `User`, a `ProfileInformation`, and an account object of the type specified by `account_class`.
    The new account will be initialized with some predefined values.
    Use this function to create accounts for testing. 
    :param account_class: The model class of the account to create. 
    Should be one of `Patient`, `Administrator`, `Doctor`, and `Nurse`. 
    :param hospital: A `Hospital` object to associate this account with. 
    :return: The newly created & saved `User` object. 
    """

    user = User.objects.create_user(username, 'e@mail.com', password)
    user.first_name = 'First'
    user.last_name = 'Last'
    user.groups.add(account_class.get_group())
    user.save()

    ProfileInformation.create_default(user, account_class.ACCOUNT_TYPE)

    account_class.create_default(user, hospital)

    return user


class AbstractUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    def full_name(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    class Meta:
        abstract = True


class Patient(AbstractUser):
    preferred_hospital = models.ForeignKey(Hospital, related_name='+')

    medical_information = models.TextField(blank=True)

    proof_of_insurance = models.TextField()

    emergency_contact = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT,
                                          help_text='You have the option to link with a registered patient '
                                                    'as an emergency contact.')
    emergency_contact_phone = models.CharField(max_length=10, null=True, blank=True,
                                               help_text='The phone number of an unregistered emergency contact. '
                                                         'You must provide this if you do not '
                                                         'link with a registered patient.')

    class Meta:
        permissions = (
            ('view_patients', 'Can view patients'),
        )

    ACCOUNT_TYPE = 'P'

    @classmethod
    def get_group(cls):
        return Group.objects.get(name='Patient')

    @classmethod
    def create_default(cls, user, hospital):
        """
        Create & save a `Patient` object with some predefined default value.
        Use this function to create accounts for testing. 
        :param user: A `User` object to associate this account with.
        :param hospital: A `Hospital` object to associate this account with.
        :return: A newly created and saved `Patient` object.
        """

        return Patient.objects.create(
            user=user, medical_information='', proof_of_insurance='proof',
            preferred_hospital=hospital, emergency_contact_phone='1234567890'

        )

    def get_current_treatment_session(self):
        return TreatmentSession.objects.filter(patient=self).filter(discharge_timestamp=None).first()

    def get_admitted_hospital(self):
        treatment_session = self.get_current_treatment_session()
        if treatment_session:
            return treatment_session.treating_hospital

    class Meta:
        permissions = (
            ('view_patients', 'Can view patients'),
        )


class Administrator(AbstractUser):
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT)

    ACCOUNT_TYPE = 'A'

    @classmethod
    def get_group(cls):
        return Group.objects.get(name='Administrator')

    @classmethod
    def create_default(cls, user, hospital):
        """
        Create & save an `Administrator` object with some predefined default value.
        Use this function to create accounts for testing. 
        :param user: A `User` object to associate this account with.
        :param hospital: A `Hospital` object to associate this account with.
        :return: A newly created and saved `Administrator` object.
        """

        return Administrator.objects.create(user=user, hospital=hospital)


class Doctor(AbstractUser):
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT)

    treatment_sessions = models.ManyToManyField(TreatmentSession, blank=True)

    ACCOUNT_TYPE = 'D'

    @classmethod
    def get_group(cls):
        return Group.objects.get(name='Doctor')

    @classmethod
    def create_default(cls, user, hospital):
        """
        Create & save a `Doctor` object with some predefined default value.
        Use this function to create accounts for testing. 
        :param user: A `User` object to associate this account with.
        :param hospital: A `Hospital` object to associate this account with.
        :return: A newly created and saved `Doctor` object.
        """

        return Doctor.objects.create(user=user, hospital=hospital)


class Nurse(AbstractUser):
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT)

    treatment_sessions = models.ManyToManyField(TreatmentSession, blank=True)

    ACCOUNT_TYPE = 'N'

    @classmethod
    def get_group(cls):
        return Group.objects.get(name='Nurse')

    @classmethod
    def create_default(cls, user, hospital):
        """
        Create & save a `Nurse` object with some predefined default value.
        Use this function to create accounts for testing. 
        :param user: A `User` object to associate this account with.
        :param hospital: A `Hospital` object to associate this account with.
        :return: A newly created and saved `Nurse` object.
        """

        return Nurse.objects.create(user=user, hospital=hospital)


class ProfileInformation(models.Model):
    """
    A model that describes the basic profile information of a user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_information')

    MALE = 'M'
    FEMALE = 'F'

    GENDER_CHOICES = (
        (MALE, 'Male'),
        (FEMALE, 'Female')
    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    ACCOUNT_TYPE_CHOICES = (
        (Patient.ACCOUNT_TYPE, 'Patient'),
        (Administrator.ACCOUNT_TYPE, 'Administrator'),
        (Doctor.ACCOUNT_TYPE, 'Doctor'),
        (Nurse.ACCOUNT_TYPE, 'Nurse'),
    )

    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPE_CHOICES)

    address = models.CharField(max_length=80)
    phone = models.CharField(max_length=10)

    @classmethod
    def from_user(cls, user):
        """
        Attempt to get the profile information of the given user.
        :return: The profile information if it exist; otherwise, None.
        """
        try:
            return user.profile_information
        except (ProfileInformation.DoesNotExist, AttributeError):
            return None

    @classmethod
    def create_default(cls, user, account_type):
        return ProfileInformation.objects.create(
            user=user, address='Test address', gender='M',
            phone='1234567890', account_type=account_type
        )


def get_account_from_user(user):
    """
    Get the correct account object associated with the given user, or None if it doesn't have an associated account object.
    The account object is one of four types: `Patient`, `Administrator`, `Doctor`, or `Nurse`.
    :param user: A User object.
    :return:
    """

    profile_information = ProfileInformation.from_user(user)
    if profile_information is not None:
        if profile_information.account_type == Patient.ACCOUNT_TYPE:
            return user.patient
        elif profile_information.account_type == Doctor.ACCOUNT_TYPE:
            return user.doctor
        elif profile_information.account_type == Nurse.ACCOUNT_TYPE:
            return user.nurse
        elif profile_information.account_type == Administrator.ACCOUNT_TYPE:
            return user.administrator
