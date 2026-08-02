from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents
from apps.students.views import student_save_ajax


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
