from calendar import Calendar
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.scoping import scoped_student
from .models import Tblattendance
from .terms import (
    filter_by_term,
    get_active_term,
    status_counts,
    term_context,
    term_label,
)


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
    active_term = get_active_term(request.user)

    try:
        attendance, created = Tblattendance.objects.update_or_create(
            attend_date=date.today(),
            student_id=student,
            defaults={'status': status, 'term': active_term},
        )
    except IntegrityError:
        attendance = Tblattendance.objects.filter(
            attend_date=date.today(), student_id=student,
        ).first()
        attendance.status = status
        attendance.term = active_term
        attendance.save(update_fields=['status', 'term'])

    # The badges on the student list report on whichever term that page is
    # showing, so hand back fresh totals rather than letting the page guess.
    counts = status_counts(
        Tblattendance.objects.filter(student_id=student, term=active_term)
    )

    return JsonResponse({
        'status': 'saved',
        'label': _status_label(status),
        'student': student.fullname,
        'term': active_term,
        'term_label': term_label(active_term),
        'counts': counts,
    })



@login_required(login_url='login')
def attendance_calendar_view(request, student_id):
    student = scoped_student(request.user, student_id)

    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    current_month = date(year, month, 1)

    term_context_data = term_context(request)
    term = term_context_data['view_term']

    records = filter_by_term(
        Tblattendance.objects.filter(
            student_id=student,
            attend_date__year=year,
            attend_date__month=month,
        ),
        term,
    ).order_by('attend_date')

    attendance_map = {record.attend_date: record for record in records}
    calendar_weeks = []
    totals = {'1': 0, '2': 0, '3': 0, '4': 0}

    for week in Calendar(firstweekday=6).monthdayscalendar(year, month):
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': None, 'record': None, 'is_today': False})
                continue

            current_date = date(year, month, day)
            record = attendance_map.get(current_date)

            if record:
                totals[record.status] = totals.get(record.status, 0) + 1
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

    page_context = {
        'student': student,
        'calendar_weeks': calendar_weeks,
        'student_id': student_id,
        'month_label': current_month.strftime('%B %Y'),
        'prev_month': prev_month,
        'next_month': next_month,
        'current_year': year,
        'current_month': month,
        'month_totals': {
            'present_count': totals.get('1', 0),
            'late_count': totals.get('2', 0),
            'absent_count': totals.get('3', 0),
            'excused_count': totals.get('4', 0),
        },
    }
    page_context.update(term_context_data)

    return render(request, 'attendance_calendar.html', page_context)
