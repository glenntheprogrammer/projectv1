from django.test import TestCase

from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


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
