from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from .forms import UserCreationForm, UserChangeForm, ProfileInformationForm, PatientCreationForm, PatientChangeForm, \
    AdministratorForm, DoctorCreationForm, NurseForm
from .models import Patient, Administrator, get_account_from_user
from hnet.logger import CreateLogEntry


def register_patient(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_information_form = ProfileInformationForm(request.POST)
        patient_form = PatientCreationForm(request.POST)

        if user_form.is_valid() and profile_information_form.is_valid() and patient_form.is_valid():
            user = user_form.save_as_patient_with_profile_information(patient_form, profile_information_form)

            auth.login(request, user)
            CreateLogEntry(request.user.username, "Patient account registered.")
            return render(request, 'account/patient/register_done.html')
    else:
        user_form = UserCreationForm()
        profile_information_form = ProfileInformationForm()
        patient_form = PatientCreationForm()

    return render(request, 'account/patient/register.html',
                  {'user_form': user_form, 'profile_information_form': profile_information_form,
                   'patient_form': patient_form})


@login_required
@permission_required('account.change_profileinformation')
@user_passes_test(lambda u: not u.is_superuser)
def profile(request):
    user = request.user
    profile_information = user.profile_information
    account = get_account_from_user(request.user)

    if request.method == 'POST':
        user_form = UserChangeForm(request.POST, instance=user)
        profile_information_form = ProfileInformationForm(request.POST, instance=profile_information)
        patient_form = PatientChangeForm(request.POST, instance=account) if isinstance(account, Patient) else None
        if user_form.is_valid() and profile_information_form.is_valid() and (patient_form is None or patient_form.is_valid()):
            user_form.save()
            profile_information_form.save()
            if patient_form:
                patient_form.save()
            CreateLogEntry(request.user.username, "Changed profile information.")
            return render(request, 'account/patient/profile.html', {
                'form_list': [user_form, profile_information_form, patient_form],
                'message': 'All changes saved.'
            })
    else:
        user_form = UserChangeForm(instance=user)
        profile_information_form = ProfileInformationForm(instance=profile_information)
        patient_form = PatientChangeForm(instance=account) if isinstance(account, Patient) else None

    return render(request, 'account/patient/profile.html', {
        'form_list': [user_form, profile_information_form, patient_form],
    })


@login_required()
@permission_required('account.add_administrator')
@permission_required('account.add_profileinformation')
def create_administrator(request):
    creator = get_account_from_user(request.user)
    administrator_form = None

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_information_form = ProfileInformationForm(request.POST)

        if user_form.is_valid() and profile_information_form.is_valid():
            if isinstance(creator, Administrator):
                user_form.save_as_administrator_by_creator_with_profile_information(creator, profile_information_form)
                CreateLogEntry(request.user.username, "Administrator account registered.")
                return render(request, 'account/administrator/create_done.html')
            else:
                administrator_form = AdministratorForm(request.POST)
                if administrator_form.is_valid():
                    user_form.save_as_administrator_with_profile_information(administrator_form,
                                                                             profile_information_form)
                    CreateLogEntry(request.user.username, "Administrator account registered.")
                    return render(request, 'account/administrator/create_done.html')

    else:
        user_form = UserCreationForm()
        profile_information_form = ProfileInformationForm()
        if not isinstance(creator, Administrator):
            administrator_form = AdministratorForm()

    return render(request, 'account/administrator/create.html',
                  {'user_form': user_form,
                   'profile_information_form': profile_information_form,
                   'administrator_form': administrator_form})


@login_required()
@permission_required('account.add_doctor')
@permission_required('account.add_profileinformation')
def register_doctor(request):
    creator = get_account_from_user(request.user)
    doctor_form = None

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_information_form = ProfileInformationForm(request.POST)

        if user_form.is_valid() and profile_information_form.is_valid():
            if isinstance(creator, Administrator):
                user_form.save_as_doctor_by_creator_with_profile_information(creator, profile_information_form)
                CreateLogEntry(request.user.username, "Doctor account registered.")
                return render(request, 'account/doctor/register_done.html')
            else:
                doctor_form = DoctorCreationForm(request.POST)
                if doctor_form.is_valid():
                    user_form.save_as_doctor_with_profile_information(doctor_form, profile_information_form)
                    CreateLogEntry(request.user.username, "Doctor account registered.")
                    return render(request, 'account/doctor/register_done.html')
    else:
        user_form = UserCreationForm()
        profile_information_form = ProfileInformationForm()
        if not isinstance(creator, Administrator):
            doctor_form = DoctorCreationForm()

    return render(request, 'account/doctor/doctor.html',
                  {'user_form': user_form, 'profile_information_form': profile_information_form,
                   'doctor_form': doctor_form})


@login_required()
@permission_required('account.add_nurse')
@permission_required('account.add_profileinformation')
def create_nurse(request):
    creator = get_account_from_user(request.user)
    nurse_form = None

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_information_form = ProfileInformationForm(request.POST)

        if user_form.is_valid() and profile_information_form.is_valid():
            if isinstance(creator, Administrator):
                user_form.save_as_nurse_by_creator_with_profile_information(creator, profile_information_form)
                CreateLogEntry(request.user.username, 'Nurse account created.')
                return render(request, 'account/nurse/create_done.html')
            else:
                nurse_form = NurseForm(request.POST)
                if nurse_form.is_valid():
                    user_form.save_as_nurse_with_profile_information(nurse_form, profile_information_form)
                    CreateLogEntry(request.user.username, 'Nurse account created.')
                    return render(request, 'account/nurse/create_done.html')
    else:
        user_form = UserCreationForm()
        profile_information_form = ProfileInformationForm()
        if not isinstance(creator, Administrator):
            nurse_form = NurseForm()

    return render(request, 'account/nurse/create.html', {
        'user_form': user_form,
        'profile_information_form': profile_information_form,
        'nurse_form': nurse_form
    })


@login_required()
@permission_required('account.add_administrator')
@permission_required('account.add_profileinformation')
def add_account(request):
    return render(request, 'account/common/new_account.html')
