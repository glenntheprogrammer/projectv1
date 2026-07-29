from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


class DashboardViewTests(TestCase):
    def test_dashboard_context_contains_summary_metrics(self):
        user = get_user_model().objects.create_user(username='admin', password='secret1234')
        course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2025-2026')
        student = Tblstudents.objects.create(idno='1001', fullname='John Doe', courseid=str(course.courseid))
        Tblattendance.objects.create(attend_date='2026-07-29', student_id=student, status='Present')
        Tblattendance.objects.create(attend_date='2026-07-29', student_id=student, status='Late')

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['total_courses'], 1)
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_attendance_records'], 2)
        self.assertEqual(response.context['present_count'], 1)
        self.assertEqual(response.context['late_count'], 1)
