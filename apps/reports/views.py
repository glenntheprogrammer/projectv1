from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


@login_required(login_url='login')
def course_reports_view(request):
    courses = Tblcourse.objects.filter(status='active').order_by('name')
    report_rows = []

    for course in courses:
        students = Tblstudents.objects.filter(courseid=course.courseid).order_by('fullname')
        course_report = {
            'course': course,
            'most_late': [],
            'most_absent': [],
            'perfect_attendance': [],
        }

        for student in students:
            records = Tblattendance.objects.filter(student_id=student).order_by('attend_date')
            late_count = records.filter(status='2').count()
            absent_count = records.filter(status='3').count()
            present_count = records.filter(status='1').count()
            excused_count = records.filter(status='4').count()

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
                    'excused_count': excused_count,
                })

        course_report['most_late'] = sorted(course_report['most_late'], key=lambda item: item['late_count'], reverse=True)[:5]
        course_report['most_absent'] = sorted(course_report['most_absent'], key=lambda item: item['absent_count'], reverse=True)[:5]
        course_report['perfect_attendance'] = sorted(course_report['perfect_attendance'], key=lambda item: item['present_count'], reverse=True)[:5]
        report_rows.append(course_report)

    return render(request, 'reports/course_reports.html', {
        'report_rows': report_rows,
    })
