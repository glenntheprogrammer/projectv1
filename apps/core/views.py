import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    failed_attempts, remaining = _get_lock_state(request)
    if remaining is not None:
        messages.error(request, f'Too many failed attempts. Try again in {remaining} seconds.')
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    if request.method == 'GET':
        return render(request, 'auth/login.html')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        _reset_lock_state(request)
        login(request, user)
        return redirect('dashboard')

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        remaining = _set_lock_state(request)
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    messages.error(request, f'{INVALID_LOGIN_MESSAGE} {remaining_attempts} attempts remaining.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    total_courses = Tblcourse.objects.count()
    total_students = Tblstudents.objects.count()
    total_attendance_records = Tblattendance.objects.count()

    attendance_status_counts = Tblattendance.objects.values('status').annotate(count=models.Count('status'))
    status_map = {item['status'].lower(): item['count'] for item in attendance_status_counts}

    present_count = status_map.get('present', 0)
    late_count = status_map.get('late', 0)
    absent_count = status_map.get('absent', 0)
    excused_count = status_map.get('excused', 0)

    attendance_breakdown = [
        {'label': 'Present', 'value': present_count, 'color': '#2fb344'},
        {'label': 'Late', 'value': late_count, 'color': '#f59f00'},
        {'label': 'Absent', 'value': absent_count, 'color': '#d63939'},
        {'label': 'Excused', 'value': excused_count, 'color': '#206bc4'},
    ]

    # --- Per-student mini bar chart (last 14 days) ---
    today = timezone.localdate()
    date_range = [today - timedelta(days=i) for i in range(13, -1, -1)]
    date_labels = [d.strftime('%b %d') for d in date_range]

    students = Tblstudents.objects.all().order_by('fullname')

    attendance_qs = Tblattendance.objects.filter(
        attend_date__gte=date_range[0],
        attend_date__lte=today,
    ).values('student_id', 'attend_date', 'status')

    # Group records by student_id -> {date: status}
    records_by_student = {}
    for row in attendance_qs:
        records_by_student.setdefault(row['student_id'], {})[row['attend_date']] = row['status'].lower()

    student_performance = []

    for student in students:
        status_by_date = records_by_student.get(student.id, {})

        daily_present = []  # 1/0/None per day, for the sparkline
        for d in date_range:
            status = status_by_date.get(d)
            if status is None:
                daily_present.append(None)
            else:
                daily_present.append(1 if status == 'present' else 0)

        last_7_dates = date_range[-7:]
        prev_7_dates = date_range[-14:-7]

        def _rate_for(dates):
            marked = [
                1 if status_by_date.get(d) == 'present' else 0
                for d in dates if d in status_by_date
            ]
            return (sum(marked) / len(marked)) * 100 if marked else None

        current_rate = _rate_for(last_7_dates)
        previous_rate = _rate_for(prev_7_dates)

        if current_rate is None:
            current_rate_display = 0
        else:
            current_rate_display = round(current_rate)

        if current_rate is not None and previous_rate is not None:
            delta = round(current_rate - previous_rate)
        else:
            delta = 0

        student_performance.append({
            'student': student,
            'attendance_rate': current_rate_display,
            'delta': delta,
            'sparkline_json': json.dumps(daily_present),
        })

    context = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_attendance_records': total_attendance_records,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'excused_count': excused_count,
        'attendance_breakdown': attendance_breakdown,
        'student_performance': student_performance,
        'chart_labels': json.dumps(date_labels),
    }
    return render(request, 'home.html', context)


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'GET':
        return render(request, 'auth/register.html')

    form_data = {
        'username': request.POST.get('username', ''),
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'password': request.POST.get('password', ''),
        'confirm_password': request.POST.get('confirm_password', ''),
    }

    errors = _validate_registration_data(form_data)
    if errors:
        return render(request, 'auth/register.html', {'errors': errors, 'form_data': form_data})

    user = User.objects.create_user(
        username=form_data['username'].strip(),
        first_name=form_data['first_name'].strip(),
        last_name=form_data['last_name'].strip(),
        email=form_data['email'].strip(),
        password=form_data['password'],
    )
    login(request, user)
    return redirect('dashboard')