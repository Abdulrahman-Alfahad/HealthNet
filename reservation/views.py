import datetime
import math

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from reservation.models import Appointment, get_account_from_user
from reservation.forms import AppointmentFormForPatient, AppointmentFormForDoctor
from account.models import Patient, Doctor, Nurse, ProfileInformation, get_account_from_user
from hnet.logger import CreateLogEntry


@login_required
@permission_required('reservation.view_appointment')
@user_passes_test(lambda u: not u.is_superuser)
def calendar(request, month=datetime.date.today().month, year=datetime.date.today().year):
    """
    main calendar view. This is the monthview
    :param month: passed in month
    :param year: passed in year
    :return: monthview of the calendar
    """
    month = int(month)
    year = int(year)

    if not is_month_valid(month) or not is_year_valid(year):
        raise Http404()

    week_list = calculate_day(str(month), str(year))

    # forward and back arrow calculations
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    month_name = datetime.date(1900, month, 1).strftime('%B')

    context = {'year': year, 'month': month, 'month_name': month_name,
               'prev_month': prev_month, 'prev_year': prev_year, 'next_month': next_month,
               'next_year': next_year, 'week_list': week_list}

    # grab all appointments for the select user
    profile_information = ProfileInformation.from_user(request.user)
    if profile_information is not None:
        account_type = profile_information.account_type
        if account_type == Patient.ACCOUNT_TYPE:
            appointments = Appointment.get_for_user_in_year_in_month(request.user.patient, year, month)
            if appointments is None:
                raise Http404()
            context['appointment_list'] = appointments
            return render(request, 'reservation/calendar.html', context)
        elif account_type == Doctor.ACCOUNT_TYPE:
            appointments = Appointment.get_for_user_in_year_in_month(request.user.doctor, year, month)
            if appointments is None:
                raise Http404()
            context['appointment_list'] = appointments
            return render(request, 'reservation/calendar.html', context)

    raise PermissionDenied()


@login_required()
@permission_required('reservation.view_appointment')
@user_passes_test(lambda u: not u.is_superuser)
def weekview(request, day=datetime.date.today().day, month=datetime.date.today().month,
             year=datetime.date.today().year):
    """
    weekview of the calendar. Displays the calendar and appointments
    for a given week instead of month
    :param request:
    :param day: start day of the week
    :param month: start month of the given week
    :param year: start year of the given week
    :return: weekview of the calendar with appointments
    """
    doctors = []
    person = "user"
    day = int(day)
    month = int(month)
    year = int(year)

    week_starting_date = datetime.date(day=day, month=month, year=year)
    weekday = week_starting_date.isoweekday()
    if weekday != 7:
        week_starting_date -= datetime.timedelta(days=weekday)
    week_ending_date = week_starting_date + datetime.timedelta(days=6)

    # if nurse, get selected doctors to show, otherwise show your own appointments
    doctor_list = None
    profile_information = ProfileInformation.from_user(request.user)
    account_type = profile_information.account_type
    if account_type == Nurse.ACCOUNT_TYPE:
        nurse = get_account_from_user(request.user)
        hospital = nurse.hospital
        person = "nurse"
        doctors = Doctor.objects.all().filter(hospital=hospital)
        if request.method == "POST":
            doctor_list = [parse_int(x) for x in request.POST.getlist("doctor_list")]
            appointments = Appointment.objects.filter(cancelled=False).filter(doctor_id__in=doctor_list)
        else:
            appointments = Appointment.objects.filter(cancelled=False).filter(doctor__hospital=hospital)
    else:
        appointments = Appointment.get_for_user_in_week_starting_at_date(request.user, week_starting_date)

    week = get_week(week_starting_date, week_ending_date)
    last_week = week_starting_date - datetime.timedelta(days=1)
    next_week = week_ending_date + datetime.timedelta(days=1)
    # 'start_date' and 'end_date' are `datetime.date` objects representing the dates at the start and end of the week.
    context = {'appointment_list': appointments, 'week': week, 'start_day': week_starting_date,
               'end_day': week_ending_date, 'next_week': next_week, 'last_week': last_week, 'person': person,
               'doctors': doctors, 'selected_doctor_list': doctor_list}

    return render(request, 'reservation/weekview.html', context)


@login_required
@permission_required('reservation.view_appointment')
@user_passes_test(lambda u: not u.is_superuser)
def overview(request, day=None, month=None, year=None):
    """
    main overview for a selected day.
    Tells you all the appointments for that day
    :param request: requested page
    :param day: current day that was selected
    :param month: month of the day that was selected
    :param year: year of the day that was selected
    :return: page with all the appointments for a given day
    """
    if day is None or month is None or year is None:
        date = datetime.date.today()
    else:
        try:
            date = datetime.date(int(year), int(month), int(day))
        except ValueError:
            raise Http404()

    month_name = datetime.date(1900, date.month, 1).strftime('%B')

    context = {'month_name': month_name, 'date': date,
               'can_cancel': request.user.has_perm('reservation.cancel_appointment')}

    profile_information = ProfileInformation.from_user(request.user)
    if profile_information is not None:
        account_type = profile_information.account_type
        if account_type == Patient.ACCOUNT_TYPE:
            appointments = Appointment.get_for_user_in_date(request.user.patient, date)
            context['appointment_list'] = appointments
            return render(request, 'reservation/overview.html', context)
        elif account_type == Doctor.ACCOUNT_TYPE:
            appointments = Appointment.get_for_user_in_date(request.user.doctor, date)
            context['appointment_list'] = appointments
            return render(request, 'reservation/overview.html', context)
        elif account_type == Nurse.ACCOUNT_TYPE:
            hospital = request.user.nurse.hospital
            # filter all cancelled and appointments that are not for a given hospital for the Nurse
            appointments = Appointment.objects.filter(cancelled=False).filter(date=date).filter(doctor__hospital=hospital)
            context['appointment_list'] = appointments
            return render(request, 'reservation/overview_nurse.html', context)

    raise PermissionDenied()


@login_required
@permission_required('reservation.add_appointment')
@user_passes_test(lambda u: not u.is_superuser)
def create_appointment(request):
    """
    Used to create an appointment. Sys admins/admins/nurses are
    not able to view this page
    :param request: page requested
    :return: none
    """
    profile_information = ProfileInformation.from_user(request.user)
    account_type = profile_information.account_type
    if account_type == Patient.ACCOUNT_TYPE:
        form_type = AppointmentFormForPatient
    elif account_type == Doctor.ACCOUNT_TYPE:
        # doctors have different form than patient
        form_type = AppointmentFormForDoctor
    else:
        raise PermissionDenied()

    if request.method == 'POST':
        form = form_type(request.POST)
        if form.is_valid():
            CreateLogEntry(request.user.username, "Appointment created.")
            form.save(request.user)
            return redirect(reverse('reservation:create_done'))
    else:
        form = form_type()

    return render(request, 'reservation/appointment/create.html', {'form': form})


@login_required
@permission_required('reservation.add_appointment')
def create_appointment_done(request):
    """
    Used to notify user that an appointment has been created
    :param request: requested page
    :return: none
    """
    return render(request, 'reservation/appointment/create_done.html')


@login_required
@permission_required('reservation.change_appointment')
def edit_appointment(request, appointment_id):
    """
    Used to edit a selected appointment
    to change the time or reason etc.
    :param request: page requested by user
    :param appointment_id: id of the appointment
    :return: none
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if not appointment.accessible_by_user(request.user):
        raise PermissionDenied()

    if ProfileInformation.from_user(request.user).account_type == Doctor.ACCOUNT_TYPE:
        if request.method == 'POST':
            form = AppointmentFormForDoctor(request.POST, instance=appointment)
            if form.is_valid():
                CreateLogEntry(request.user.username, "Appointment edited.")
                form.save()
                return render(request, 'reservation/appointment/edit.html',
                              {'form': form, 'message': 'All changes saved.'})
        else:
            form = AppointmentFormForDoctor(instance=appointment)
    else:
        if request.method == 'POST':
            form = AppointmentFormForPatient(request.POST, instance=appointment)
            if form.is_valid():
                CreateLogEntry(request.user.username, "Appointment edited.")
                form.save()
                return render(request, 'reservation/appointment/edit.html',
                              {'form': form, 'message': 'All changes saved.'})
        else:
            form = AppointmentFormForPatient(instance=appointment)

    return render(request, 'reservation/appointment/edit.html', {'form': form})


@login_required
@permission_required('reservation.cancel_appointment')
def cancel_appointment(request, appointment_id):
    """
    Used to cancel a selected appointment
    :param request: user requested page
    :param appointment_id: id of the appointment to cancel
    :return: none
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if not appointment.accessible_by_user(request.user):
        raise PermissionDenied()

    if request.method == 'POST':
        appointment.cancelled = True
        appointment.save()
        CreateLogEntry(request.user.username, "Appointment canceled.")

        return render(request, 'reservation/appointment/cancel_done.html')
    else:
        return render(request, 'reservation/appointment/cancel.html', {'appointment': appointment})


def is_month_valid(month):
    """Test whether or not the given month is a valid value."""

    return 1 <= month <= 12


def is_year_valid(year):
    """Test whether or not the given year is a valid value."""

    return 1000 < year < 9999


def get_week(start_day, end_day):
    """
    Calculate the start and end days in a week.
    Used for the weekview calendar
    :param start_day: the datetime when the week starts
    :param end_day: the datetime when the week should end
    :return: list of weekdays
    """
    # keep original date object
    start_date = start_day
    end_date = end_day
    # grab days for beginning and end of week
    start_day = start_day.day
    end_day = end_day.day
    counter = start_day
    if start_day < end_day:
        weekday = []
        while counter != end_day + 1:
            weekday.append(start_date)
            start_date += datetime.timedelta(days=1)
            counter += 1
    else:
        weekday = [0] * 7
        day_index = 6
        while end_day >= 1 and day_index >= 0:
            weekday[day_index] = end_date
            end_date -= datetime.timedelta(days=1)
            end_day -= 1
            day_index -= 1

        temp_index = 0
        while day_index >= 0:
            weekday[temp_index] = start_date
            start_date += datetime.timedelta(days=1)
            day_index -= 1
            temp_index += 1

    return weekday


def calculate_day(month, year):
    """
    Function is used to calculate the days in the month and
    when it stars and ends. Extra days are added as place
    holders
    :param month: a month in the form of an int
    :param year: a year
    :return: list of days for a given month
    """
    if int(month) == 2 or int(month) == 1:
        year = int(year) - 1
        month = int(month) + 12

    final = 1 + (2 * int(month)) + (3 * (int(month) + 1) / 5) + int(year) + math.floor(int(year) / 4) - \
            math.floor(int(year) / 100) + math.floor(int(year) / 400) + 2

    remainder = math.floor(final / 7)
    remainder *= 7
    final -= remainder

    thirtyone_months = ["12", "13", "3", "5", "7", "8", "10"]

    if (int(year) / 4 and int(month) == 14) or (month == 14 and int(year) / 100 and int(year) / 400):
        counter = 29
    if month == 14:
        counter = 28
    elif month in thirtyone_months or month == 13:
        counter = 31
    else:
        counter = 30

    count = 1
    days_one = []
    days_two = []
    days_three = []
    days_four = []
    days_five = []
    days_six = []

    # populate each of the weeks to be displayed
    if (int(final) == 0):
        final = 7

    for i in range(0, int(final) - 1):
        days_one.append("none")

    for i in range(0, 7 - (int(final) - 1)):
        days_one.append(count)
        count += 1

    for i in range(0, 7):
        days_two.append(count)
        count += 1

    for i in range(0, 7):
        days_three.append(count)
        count += 1

    for i in range(0, 7):
        days_four.append(count)
        count += 1
    counter -= (21 + (7 - (final - 1)))
    if int(counter) - 7 < 0 and int(counter) > 0:
        for i in range(0, int(counter)):
            days_five.append(count)
            count += 1
        for i in range(int(counter), 7):
            days_five.append("none")
        for i in range(0, 7):
            days_six.append("none")
    elif int(counter) == 0:
        for i in range(0, 7):
            days_five.append("none")
            days_six.append("none")
    else:
        for i in range(0, 7):
            days_five.append(count)
            count += 1
        counter -= 7
        if int(counter) - 7 < 0 and int(counter) > 0:
            for i in range(0, int(counter)):
                days_six.append(count)
                count += 1
            for i in range(int(counter), 7):
                days_six.append("none")

    days = [days_one, days_two, days_three, days_four, days_five, days_six]

    return days


def parse_int(input):
    try:
        return int(input)
    except ValueError:
        return None
