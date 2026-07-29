from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.attendance.models import Tblattendance
from apps.students.models import Tblstudents


class AttendanceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.student = Tblstudents.objects.create(idno='1001', fullname='Jane Doe', courseid='C-001')
        Tblattendance.objects.create(attend_date=date.today(), student_id=self.student, status='1')

    def test_attendance_calendar_view_requires_login(self):
        response = self.client.get('/attendance/calendar/1/')
        self.assertEqual(response.status_code, 302)

    def test_attendance_calendar_view_renders(self):
        self.client.login(username='tester', password='secret123')
        response = self.client.get('/attendance/calendar/1/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendance Calendar')
