from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.attendance.models import Tblattendance
from apps.attendance.terms import filter_by_term, status_counts, term_context
from apps.courses.models import Tblcourse
from apps.scoping import scoped_courses, scoped_students
from apps.students.models import Tblstudents


@login_required(login_url='login')
def course_reports_view(request):
    courses = scoped_courses(request.user).filter(status='active').order_by('name')
    term_context_data = term_context(request)
    view_term = term_context_data['view_term']
    report_rows = []

    for course in courses:
        students = scoped_students(request.user).filter(courseid=course.courseid).order_by('fullname')
        course_report = {
            'course': course,
            'most_late': [],
            'most_absent': [],
            'perfect_attendance': [],
        }

        for student in students:
            counts = status_counts(
                filter_by_term(
                    Tblattendance.objects.filter(student_id=student),
                    view_term,
                )
            )

            late_count = counts['late_count']
            absent_count = counts['absent_count']
            present_count = counts['present_count']

            if late_count > 0:
                course_report['most_late'].append({
                    'student': student,
                    'late_count': late_count,
                })

            if absent_count > 0:
                course_report['most_absent'].append({
                    'student': student,
                    'absent_count': absent_count,
                })

            if late_count == 0 and absent_count == 0 and present_count > 0:
                course_report['perfect_attendance'].append({
                    'student': student,
                    'present_count': present_count,
                    'excused_count': counts['excused_count'],
                })

        course_report['most_late'] = sorted(course_report['most_late'], key=lambda item: item['late_count'], reverse=True)
        course_report['most_absent'] = sorted(course_report['most_absent'], key=lambda item: item['absent_count'], reverse=True)
        course_report['perfect_attendance'] = sorted(course_report['perfect_attendance'], key=lambda item: item['present_count'], reverse=True)
        report_rows.append(course_report)

    page_context = {
        'report_rows': report_rows,
    }
    page_context.update(term_context_data)

    return render(request, 'reports/course_reports.html', page_context)
