from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents
from apps.students.views import student_list_page, student_save_ajax


class StudentCourseDuplicationTests(TestCase):
    def test_same_idno_and_fullname_can_be_saved_for_different_courses(self):
        course_one = Tblcourse.objects.create(name='Math', section='A', schoolyr='2025-2026')
        course_two = Tblcourse.objects.create(name='Science', section='B', schoolyr='2025-2026')

        Tblstudents.objects.create(idno='1001', fullname='John Doe', courseid=course_one.courseid)
        Tblstudents.objects.create(idno='1001', fullname='John Doe', courseid=course_two.courseid)

        self.assertEqual(
            Tblstudents.objects.filter(idno='1001', fullname='John Doe').count(),
            2,
        )


class StudentAttendanceCountsTests(TestCase):
    def test_student_list_page_includes_attendance_status_counts(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret')
        course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2025-2026')
        student = Tblstudents.objects.create(idno='1001', fullname='John Doe', courseid=course.courseid)

        Tblattendance.objects.create(attend_date='2025-08-01', student_id=student, status='1')
        Tblattendance.objects.create(attend_date='2025-08-02', student_id=student, status='2')
        Tblattendance.objects.create(attend_date='2025-08-03', student_id=student, status='3')
        Tblattendance.objects.create(attend_date='2025-08-04', student_id=student, status='4')

        self.client.force_login(self.user)
        response = self.client.get('/students/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['students'][0]['attendance_counts']['present_count'], 1)
        self.assertEqual(response.context['students'][0]['attendance_counts']['late_count'], 1)
        self.assertEqual(response.context['students'][0]['attendance_counts']['absent_count'], 1)
        self.assertEqual(response.context['students'][0]['attendance_counts']['excused_count'], 1)


class StudentSaveAjaxTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='tester', password='secret')
        self.course_one = Tblcourse.objects.create(name='Math', section='A', schoolyr='2025-2026')
        self.course_two = Tblcourse.objects.create(name='Science', section='B', schoolyr='2025-2026')
        self.url = reverse('students:student_save_ajax')

    def test_multiple_selected_courses_create_separate_student_records(self):
        request = self.factory.post(self.url, {
            'idno': '1001',
            'fullname': 'John Doe',
            'courseid': [str(self.course_one.courseid), str(self.course_two.courseid)],
        })
        request.user = self.user

        response = student_save_ajax(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Tblstudents.objects.filter(idno='1001', fullname='John Doe').count(),
            2,
        )
        self.assertEqual(
            set(Tblstudents.objects.filter(idno='1001', fullname='John Doe').values_list('courseid', flat=True)),
            {str(self.course_one.courseid), str(self.course_two.courseid)},
        )
