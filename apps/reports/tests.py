from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


class ReportsViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='reporter', password='secret123')
        self.course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2025-2026')
        self.student = Tblstudents.objects.create(idno='2001', fullname='Alex Doe', courseid=self.course.courseid)

    def test_reports_page_renders(self):
        self.client.login(username='reporter', password='secret123')
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Course Attendance Reports')
