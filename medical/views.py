from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from hospital.models import TreatmentSession
from account.models import Patient, Nurse, get_account_from_user
from .models import Drug, Diagnosis, Test, Prescription
from .forms import DrugForm, DiagnosisForm, TestForm, TestResultsForm, PrescriptionForm
from hnet.logger import CreateLogEntry
import os
from django.conf import settings
from django.http import HttpResponse


@login_required
@permission_required('medical.view_drug')
@user_passes_test(lambda u: not u.is_superuser)
def list_drug(request):
    """ Get the list of the drugs"""
    drug_list = Drug.objects.filter(active=True).order_by('name')

    return render(request, 'medical/drug/list.html', {'drug_list': drug_list})


@login_required
@permission_required('medical.add_drug')
@user_passes_test(lambda u: not u.is_superuser)
def add_drug(request):
    """
    Only administrators are able to add in new
    drugs for a hospital
    """
    if request.method == 'POST':
        form = DrugForm(request.POST)
        if form.is_valid():
            form.save()
            CreateLogEntry(request.user.username, "Added new drug.")
            return render(request, 'medical/drug/add_done.html')
    else:
        form = DrugForm()

    return render(request, 'medical/drug/add.html', {'form': form})


@login_required
@permission_required('medical.view_prescription')
@user_passes_test(lambda u: not u.is_superuser)
def view_prescriptions(request, patient_id):
    """
    patients and doctors and nurses are able to view prescriptions
    for a given patient
    :param patient_id: id of the patient that is being accesed
    :return: list of prescriptions for a patient
    """
    patient = get_object_or_404(Patient, pk=patient_id)
    prescriptions = Prescription.objects.all()
    list_prescription = []
    for prescription in prescriptions:
        if prescription.active():
            if prescription.diagnosis.patient == patient:
                list_prescription.append(prescription)
    context = {'prescription_list': list_prescription, 'patient': patient}
    return render(request, 'patient/patient_overview.html', context)


@permission_required('medical.add_prescription')
@user_passes_test(lambda u: not u.is_superuser)
def add_prescription(request, diagnosis_id):
    """Doctors are able to prescribe for a patient after diagnosing"""
    diagnosis = get_object_or_404(Diagnosis, pk=diagnosis_id)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            form.save_to_diagnosis_by_doctor(diagnosis, request.user.doctor)
            CreateLogEntry(request.user.username, "Added prescription.")
            return render(request, 'medical/prescriptions/add_done.html', {'diagnosis_id': diagnosis_id})
    else:
        form = PrescriptionForm()

    return render(request, 'medical/prescriptions/add.html', {'form': form, 'diagnosis_id': diagnosis_id})


@permission_required('medical.change_prescription')
@user_passes_test(lambda u: not u.is_superuser)
def edit_prescription(request, prescription_id):
    """Doctors can edit a prescription to change amounts or frequency of use"""
    prescription = get_object_or_404(Prescription, pk=prescription_id)

    doctor = request.user.doctor
    if prescription.doctor != doctor:
        """Doctors are only able to edit prescriptions they made"""
        raise PermissionDenied('Cannot edit prescriptions created by another doctor.')

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            CreateLogEntry(request.user.username, "Edited prescription.")
            return render(request, 'medical/prescriptions/edit.html', {'form': form, 'message': 'All changes saved.'})
    else:
        form = PrescriptionForm(instance=prescription)

    return render(request, 'medical/prescriptions/edit.html', {'form': form})


@permission_required('medical.delete_prescription')
@user_passes_test(lambda u: not u.is_superuser)
def remove_prescription(request, prescription_id):
    """
    Doctors are able to remove a prescription for a patient but only
    if they created it themselves
    """
    prescription = get_object_or_404(Prescription, pk=prescription_id)

    doctor = request.user.doctor
    if prescription.doctor != doctor:
        raise PermissionDenied('Cannot delete prescriptions created by another doctor.')

    if request.method == 'POST':
        diagnosis_id = prescription.diagnosis.id
        prescription.delete()
        CreateLogEntry(request.user.username, "Prescription deleted.")
        return render(request, 'medical/prescriptions/remove_done.html', {'diagnosis_id': diagnosis_id})

    return render(request, 'medical/prescriptions/remove.html', {'prescription': prescription})


@login_required
@permission_required('account.view_patients')
@user_passes_test(lambda u: not u.is_superuser)
def view_patients(request):
    """
    Nurses and Doctors are able to view the patients in their hospital
    """
    account = get_account_from_user(request.user)
    hospital = account.hospital

    patients = Patient.objects.all()
    if request.user.profile_information.account_type == Nurse.ACCOUNT_TYPE:
        patients = [p for p in patients if p.get_admitted_hospital() == hospital or p.preferred_hospital == hospital]

    context = {'patient_list': patients, 'hospital': hospital}

    return render(request, 'patient/view_patients.html', context)


@login_required
@permission_required('hospital.transfer_patient_any_hospital')
@user_passes_test(lambda u: not u.is_superuser)
def view_patients_admin(request):
    """
    Administrators are able to transfer patients to other hospitals
    so they must also be able to see patients for any hospital
    """
    admin = get_account_from_user(request.user)
    hospital = admin.hospital
    list_patients = []
    patients = Patient.objects.all()
    for patient in patients:
        session = patient.get_current_treatment_session()
        if session:
            if session.treating_hospital == hospital:
                list_patients.append(patient)

    context = {'patient_list': list_patients, 'hospital': hospital}

    return render(request, 'patient/view_patients_admin.html', context)


@permission_required('medical.remove_drug')
@user_passes_test(lambda u: not u.is_superuser)
def remove_drug(request, drug_id):
    """
    Administrators can remove drugs from the
    drug list at the hospitals
    """
    drug = get_object_or_404(Drug, pk=drug_id)

    if not drug.active:
        return render(request, 'medical/drug/already_removed.html')

    if request.method == 'POST':
        drug.active = False
        drug.save()
        CreateLogEntry(request.user.username, "Drug removed.")
        return render(request, 'medical/drug/remove_done.html')
    else:
        return render(request, 'medical/drug/remove.html', {'drug': drug})


@permission_required('medical.change_drug')
@user_passes_test(lambda u: not u.is_superuser)
def update_drug(request, drug_id):
    """
    Administrators are able to update the description
    or name of a specific drug in a list
    """
    drug = get_object_or_404(Drug, pk=drug_id)
    if not drug.active:
        raise Http404()

    if request.method == 'POST':
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            form.save()
            CreateLogEntry(request.user.username, "Removed drug.")
            return render(request, 'medical/drug/update.html', {'form': form, 'message': 'All changes saved.'})
    else:
        form = DrugForm(instance=drug)

    return render(request, 'medical/drug/update.html', {'form': form})


@permission_required('medical.view_diagnosis')
@permission_required('hospital.view_treatmentsession')
def view_medical_information(request, patient_id):
    """
    Displays the medical information for a requested patient
    Only nurses and doctors have this permission, as do patients
    to view their own information
    """
    patient = get_object_or_404(Patient, pk=patient_id)

    medical_information = list(Diagnosis.objects.filter(patient=patient).filter(treatment_session=None))
    medical_information.extend(TreatmentSession.objects.filter(patient=patient))

    medical_information.sort(
        reverse=True,
        key=lambda item: item.creation_timestamp if isinstance(item, Diagnosis) else item.admission_timestamp
    )

    can_transfer = False
    if patient.get_current_treatment_session() is not None:
        if request.user.has_perm("hospital.transfer_patient_receiving_hospital"):
            can_transfer = get_account_from_user(request.user).hospital != \
                           patient.get_current_treatment_session().treating_hospital

    return render(request, 'medical/patient/medical_information.html', {
        'medical_information': medical_information, 'patient': patient,
        'user_has_edit_permission': request.user.has_perm('medical.change_diagnosis'),
        'user_has_add_permission': request.user.has_perm('medical.add_diagnosis'),
        'can_discharge': request.user.has_perm('hospital.discharge_patient'),
        'can_transfer': can_transfer,
    })


@login_required
@permission_required('medical.add_diagnosis')
def create_diagnosis(request, patient_id):
    """Doctors are able to create a diagnosis for a patient"""
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            diagnosis = form.save_for_patient(patient)
            CreateLogEntry(request.user.username, "Diagnosis created.")
            return HttpResponseRedirect('%s?%s' % (
                reverse('medical:update_diagnosis', args=[diagnosis.id]),
                urlencode({'message': 'Diagnosis successfully created.'})
            ))
    else:
        form = DiagnosisForm()

    return render(request, 'medical/diagnosis/create.html',
                  {'patient': patient, 'form': form})


@login_required
@permission_required('medical.change_diagnosis')
def update_diagnosis(request, diagnosis_id):
    diagnosis = get_object_or_404(Diagnosis, pk=diagnosis_id)

    message = request.GET.get('message')
    archived = False
    if diagnosis.archived is True:
        archived = True

    if request.method == 'POST':
        form = DiagnosisForm(request.POST, instance=diagnosis)
        if form.is_valid():
            form.save()
            CreateLogEntry(request.user.username, "Diagnosis updated.")
            return render(request, 'medical/diagnosis/update.html',
                          {'form': form, 'message': 'All changes saved.', 'archived': archived})
    else:
        form = DiagnosisForm(instance=diagnosis)

    return render(request, 'medical/diagnosis/update.html',
                  {'form': form, 'message': message, 'archived': archived})


@login_required
@permission_required('medical.request_test')
@user_passes_test(lambda u: not u.is_superuser)
def request_test(request, diagnosis_id):
    """Doctors must do a 3 step test request, edit, and release"""
    diagnosis = get_object_or_404(Diagnosis, pk=diagnosis_id)
    doctor = request.user.doctor

    if doctor is None:
        return render(request, 'medical/test/requested.html')

    if request.method == 'POST':
        test_form = TestForm(request.POST)
        if test_form.is_valid():
            test_form.save_for_diagnosis(doctor, diagnosis)
            CreateLogEntry(request.user.username, "Test requested.")
            return render(request, 'medical/test/requested.html', {'diagnosis_id': diagnosis_id})
    else:
        test_form = TestForm()

    return render(request, 'medical/test/request.html', {'test_form': test_form, 'diagnosis': diagnosis})


@login_required()
@permission_required('medical.upload_test_results')
@user_passes_test(lambda u: not u.is_superuser)
def upload_test_result(request, test_id):
    test = get_object_or_404(Test, pk=test_id)

    if request.method == 'POST':
        results_form = TestResultsForm(request.POST, request.FILES, instance=test)
        if results_form.is_valid():
            results_form.save()
            CreateLogEntry(request.user.username, "Test results uploaded.")
            return render(request, 'medical/test/uploaded.html', {'test': test})
    else:
        results_form = TestResultsForm(instance=test)

    return render(request, 'medical/test/upload.html', {'results_form': results_form, 'test': test})


@permission_required('medical.release_test_results')
@user_passes_test(lambda u: not u.is_superuser)
def release_test_result(request, test_id):
    test = get_object_or_404(Test, pk=test_id)

    if request.method == 'POST':
        test.released = True
        test.save()
        CreateLogEntry(request.user.username, "Test result released.")
        return render(request, 'medical/test/release_done.html', {'diagnosis_id': test.diagnosis.id})

    return render(request, 'medical/test/release.html', {'test': test})


@login_required()
@permission_required('medical.export_information')
def export_information(request):
    """
    Patients are able to export their personal medical information
    such as the prescriptions they have and any relevant
    diagnoses. Also they can export test results
    :param request: the requesting user (Patient)
    :return: none
    """
    patient = get_account_from_user(request.user)
    prescriptions = Prescription.objects.all()
    tests = Test.objects.all()

    file_path = os.path.join(settings.MEDIA_ROOT, 'media/medical_information/%s.txt' % request.user.username)
    """Write all the information to the file to be served"""
    with open(file_path, 'w') as info_file:
        info_file.write("Medical Information for " + patient.user.first_name + " " + patient.user.last_name +
                        "\n\nPrescriptions:\n\n")
        if not prescriptions:
            info_file.write("You have no prescriptions.")
        else:
            for prescription in prescriptions:
                if prescription.diagnosis.patient == patient:
                    info_file.write(
                        "Diagnosis: " + prescription.diagnosis.summary + "\nDrug: " + prescription.drug.name + "\n" +
                        "Prescribing Doctor: Dr. " + prescription.doctor.user.first_name + " "
                        + prescription.doctor.user.last_name + "\n" + "Amount: " + prescription.quantity_info() +
                        "\nDirections: " + prescription.instruction + "\n\n")
        info_file.write("\n\nTest Results:\n\n")
        if not tests:
            info_file.write("You have no test results.")
        else:
            for test in tests:
                if test.diagnosis.patient == patient and test.released:
                    info_file.write(
                        "Test Released by Doctor: Dr. " + test.doctor.user.first_name + test.doctor.user.last_name +
                        "\n" + "Description: " + test.description + "\n" + "Results: " + test.results + "\n\n")

        info_file.close()

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/text;charset=UTF-8")
            response['Content-Disposition'] = 'inline; filename=medical_information.txt'
            CreateLogEntry(request.user.username, "Patient exported medical information.")
            return response
    else:
        raise Http404


@login_required()
@permission_required('medical.view_prescription')
def medical_view_options(request):
    """Second screen of options that a patient can view"""
    patient = get_account_from_user(request.user)
    context = {'patient': patient}
    return render(request, 'medical/patient/medical_view_options.html', context)


@login_required()
@permission_required('medical.view_test_results')
def test_view(request):
    patient = request.user.patient
    tests = Test.objects.all().filter(diagnosis__patient=patient).filter(released=True)
    context = {'patient': patient, 'test_list': tests}
    return render(request, 'medical/test/test_view.html', context)


@login_required()
@permission_required('medical.view_test_results')
def test_detail(request, test_id):
    """Display the specific test result with picture uploads if any"""
    test = get_object_or_404(Test, pk=test_id)
    if not test.released:
        raise Http404()
    file_path = "test_results/" + str(test.doctor.id) + "_" + str(test.id) + test.extension()
    context = {'test': test, 'path': file_path}
    return render(request, 'medical/test/test_detail.html', context)


@login_required()
@permission_required('medical.view_own_diagnoses')
def medical_overview(request):
    patient = request.user.patient
    medical_information = list(Diagnosis.objects.filter(patient=patient).filter(treatment_session=None))
    medical_information.extend(TreatmentSession.objects.filter(patient=patient))

    medical_information.sort(
        reverse=True,
        key=lambda item: item.creation_timestamp if isinstance(item, Diagnosis) else item.admission_timestamp
    )

    context = {'patient': patient, 'medical_information': medical_information}
    return render(request, 'medical/patient/medical_overview.html', context)


@login_required()
@permission_required('medical.add_diagnosis')
def archive_diagnosis(request, diagnosis_id):
    diagnosis = get_object_or_404(Diagnosis, pk=diagnosis_id)

    if diagnosis.archived is True:
        return render(request, 'medical/diagnosis/already_archived.html', {'diagnosis': diagnosis})

    if request.method == 'POST':
        diagnosis.archived = True
        diagnosis.save()
        CreateLogEntry(request.user.username, "Diagnosis archived.")
        return render(request, 'medical/diagnosis/archive_done.html', {'diagnosis': diagnosis})

    return render(request, 'medical/diagnosis/archive.html', {'diagnosis': diagnosis})
