from calendar import Calendar
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.scoping import scoped_student
from apps.students.models import Tblstudents
from .models import Tblattendance


def _status_label(status_value):
    labels = {
        '1': 'Present',
        '2': 'Late',
        '3': 'Absent',
        '4': 'Excused',
    }
    return labels.get(status_value, 'Recorded')


@login_required(login_url='login')
@require_POST
def attendance_save_ajax(request):
    student_id = request.POST.get('student_id', '').strip()
    status = request.POST.get('status', '').strip()

    if not student_id:
        return JsonResponse({'error': 'A student must be selected.'}, status=400)

    if status not in {'1', '2', '3', '4'}:
        return JsonResponse({'error': 'Please choose a valid attendance status.'}, status=400)

    student = scoped_student(request.user, student_id)

    try:
        attendance, created = Tblattendance.objects.update_or_create(
            attend_date=date.today(),
            student_id=student,
            defaults={'status': status},
        )
    except IntegrityError:
        attendance = Tblattendance.objects.filter(
            attend_date=date.today(),
            student_id=student,
        ).first()
        attendance.status = status
        attendance.save(update_fields=['status'])

    return JsonResponse({
        'status': 'saved',
        'label': _status_label(status),
        'student': student.fullname,
    })


@login_required(login_url='login')
def attendance_calendar_view(request, student_id):
    student = scoped_student(request.user, student_id)

    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    current_month = date(year, month, 1)

    records = Tblattendance.objects.filter(
        student_id=student,
        attend_date__year=year,
        attend_date__month=month,
    ).order_by('attend_date')

    attendance_map = {record.attend_date: record for record in records}
    calendar_weeks = []

    for week in Calendar(firstweekday=6).monthdayscalendar(year, month):
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': None, 'record': None, 'is_today': False})
                continue

            current_date = date(year, month, day)
            record = attendance_map.get(current_date)
            if record:
                week_days.append({
                    'day': day,
                    'record': record,
                    'is_today': current_date == date.today(),
                    'label': _status_label(record.status),
                    'css_class': 'bg-success-subtle' if record.status == '1' else 'bg-warning-subtle' if record.status == '2' else 'bg-danger-subtle' if record.status == '3' else 'bg-info-subtle',
                })
            else:
                week_days.append({
                    'day': day,
                    'record': None,
                    'is_today': current_date == date.today(),
                    'label': 'No entry',
                    'css_class': 'table-light',
                })
        calendar_weeks.append(week_days)

    if month == 1:
        prev_month = date(year - 1, 12, 1)
    else:
        prev_month = date(year, month - 1, 1)

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    return render(request, 'attendance_calendar.html', {
        'student': student,
        'calendar_weeks': calendar_weeks,
        'student_id': student_id,
        'month_label': current_month.strftime('%B %Y'),
        'prev_month': prev_month,
        'next_month': next_month,
        'current_year': year,
        'current_month': month,
    })
