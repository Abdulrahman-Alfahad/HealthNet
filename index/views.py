from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from account.models import ProfileInformation, get_account_from_user
from account.models import Patient, Doctor, Nurse, Administrator
from .forms import StephenLoginForm


def index(request):
    if request.user.is_superuser:
        return redirect(reverse('index:system_administrator'))
    else:
        profile_information = ProfileInformation.from_user(request.user)
        if profile_information is not None:
            account_type = profile_information.account_type

            if account_type == Patient.ACCOUNT_TYPE:
                return redirect(reverse('index:patient'))
            elif account_type == Doctor.ACCOUNT_TYPE:
                return redirect(reverse('index:doctor'))
            elif account_type == Nurse.ACCOUNT_TYPE:
                return redirect(reverse('index:nurse'))
            elif account_type == Administrator.ACCOUNT_TYPE:
                return redirect(reverse('index:administrator'))
        else:
            return render(request, 'index/index.html')


def test_user_account_type(user, account_type):
    """
    Test whether or not the given user is the given account type.
    """

    profile_information = ProfileInformation.from_user(user)
    if profile_information is not None:
        return profile_information.account_type == account_type
    return False


def log(request):
    return render(request, 'index/log.html')


# TODO: add group verification
@login_required
@user_passes_test(lambda u: test_user_account_type(u, Patient.ACCOUNT_TYPE))
def patient(request):
    patient = get_account_from_user(request.user)
    context = {'patient': patient}
    return render(request, 'index/patient.html', context)


@login_required()
@user_passes_test(lambda u: test_user_account_type(u, Doctor.ACCOUNT_TYPE))
def doctor(request):
    doctor_name = get_account_from_user(request.user)
    return render(request, 'index/doctor.html', {'doctor': doctor_name})


@login_required
@user_passes_test(lambda u: test_user_account_type(u, Nurse.ACCOUNT_TYPE))
def nurse(request):
    nurse_name = get_account_from_user(request.user)
    return render(request, 'index/nurse.html', {'nurse': nurse_name})


@login_required
@user_passes_test(lambda u: test_user_account_type(u, Administrator.ACCOUNT_TYPE))
def administrator(request):
    return render(request, 'index/administrator.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_administrator(request):
    return render(request, 'index/sys_admin.html')


def stephen(request):
    if request.method == 'POST':
        form = StephenLoginForm(request.POST)
        if form.is_valid():
            return render(request, 'index/stephen.html')
    else:
        form = StephenLoginForm()
    return render(request, 'index/stephen_login.html', {'form': form})
