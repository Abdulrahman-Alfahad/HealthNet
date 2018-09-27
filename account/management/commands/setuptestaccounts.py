from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError
from django.db.models.deletion import ProtectedError
from django.contrib.auth.models import Group, User
from account.models import Doctor, Nurse, Patient, Administrator, ProfileInformation, \
    create_default_account, create_super_user
from hospital.models import Hospital

default_password = '$teamname'


def check_table(model_type):
    return model_type.objects.count() > 0


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            Group.objects.get(name='Administrator')
            Group.objects.get(name='Doctor')
            Group.objects.get(name='Nurse')
            Group.objects.get(name='Patient')

            if check_table(User) or check_table(ProfileInformation) or check_table(Patient) \
                    or check_table(Doctor) or check_table(Nurse) or check_table(Administrator):
                while True:
                    self.stdout.write(self.style.NOTICE('You have existing account data. '
                                                        'Continuing will remove all of them and create new accounts. '
                                                        'Are you sure you want to continue? (y or n)'))

                    response = input()
                    if response == 'n':
                        print('No changes are made.')
                        return
                    elif response == 'y':
                        break

                User.objects.all().delete()
                ProfileInformation.objects.all().delete()
                Patient.objects.all().delete()
                Doctor.objects.all().delete()
                Nurse.objects.all().delete()
                Administrator.objects.all().delete()

            if check_table(Hospital):
                while True:
                    self.stdout.write(self.style.WARNING('You have existing hospital records. '
                                                         'This is not required, but you can choose to remove them before preceding. '
                                                         'Do you wish to remove existing hospital records? (y or n)'))

                    response = input()
                    if response == 'y':
                        Hospital.objects.all().delete()
                        break
                    elif response == 'n':
                        break

            hospital = Hospital.objects.create(name='Test hospital', location='Test location')
            self.stdout.write(self.style.SUCCESS('Successfully created test hospital record.'))

            create_default_account('patient', default_password, Patient, hospital)
            self.stdout.write(self.style.SUCCESS('Successfully created patient account with '
                                                 'username: patient, password: %s' % default_password))

            create_default_account('doctor', default_password, Doctor, hospital)
            self.stdout.write(self.style.SUCCESS('Successfully created doctor account with '
                                                 'username: doctor, password: %s' % default_password))

            create_default_account('nurse', default_password, Nurse, hospital)
            self.stdout.write(self.style.SUCCESS('Successfully created nurse account with '
                                                 'username: nurse, password: %s' % default_password))

            create_default_account('admini', default_password, Administrator, hospital)
            self.stdout.write(self.style.SUCCESS('Successfully created administrator account with '
                                                 'username: admini, password: %s' % default_password))

            create_super_user('admin', default_password)
            self.stdout.write(self.style.SUCCESS('Successfully created super user with '
                                                 'username: admin, password: %s' % default_password))
        except OperationalError:
            raise CommandError('Operation cannot be completed. Did you forget to do database migration?')
        except Group.DoesNotExist:
            raise CommandError('Operation cannot be completed. Did you forget to run setupgroups?')
        except ProtectedError:
            raise CommandError('Operation cannot be completed. Failed to remove existing records. '
                               'There\'re some records in the database referencing the existing records. '
                               'If you\'re sure you\'re OK with wiping the entire database, '
                               'try running `python manage.py flush`.')
