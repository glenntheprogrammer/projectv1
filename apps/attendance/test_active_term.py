from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.attendance.models import MIDTERM, PRELIM, Tblattendance, Tbltermsetting
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


class TermSettingsPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2026-2027', user=self.user)
        self.student = Tblstudents.objects.create(
            idno='1001', fullname='Jane Doe', courseid=self.course.courseid, user=self.user,
        )

    def test_requires_login(self):
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 302)

    def test_page_renders_with_all_three_terms(self):
        self.client.login(username='tester', password='secret123')
        response = self.client.get('/settings/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_term'], PRELIM)
        self.assertEqual([row['slug'] for row in response.context['term_rows']], [PRELIM, MIDTERM, 'endterm'])
        self.assertContains(response, 'Per term')

    def test_saving_selects_the_active_term(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.post('/settings/', {'active_term': MIDTERM})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Tbltermsetting.objects.get(user=self.user).active_term,
            MIDTERM,
        )

    def test_saving_invalid_term_is_rejected(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.post('/settings/', {'active_term': 'finals'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Please choose a valid term.')
        self.assertFalse(Tbltermsetting.objects.filter(user=self.user).exists())

    def test_get_is_not_allowed_to_change_the_term(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get('/settings/?active_term=midterm')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_term'], PRELIM)


class ActiveTermDrivesAttendanceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2026-2027', user=self.user)
        self.student = Tblstudents.objects.create(
            idno='1001', fullname='Jane Doe', courseid=self.course.courseid, user=self.user,
        )
        self.client.login(username='tester', password='secret123')

    def test_saving_attendance_stamps_the_active_term(self):
        Tbltermsetting.objects.create(user=self.user, active_term=MIDTERM)

        response = self.client.post('/attendance/ajax/save/', {'student_id': str(self.student.id), 'status': '1'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['term'], MIDTERM)
        self.assertEqual(
            Tblattendance.objects.get(student_id=self.student, attend_date=date.today()).term,
            MIDTERM,
        )

    def test_saved_response_counts_only_the_active_term(self):
        Tbltermsetting.objects.create(user=self.user, active_term=MIDTERM)
        yesterday = date.today().replace(day=1)
        Tblattendance.objects.create(
            attend_date=yesterday, student_id=self.student, status='1', term=PRELIM,
        )

        response = self.client.post('/attendance/ajax/save/', {'student_id': str(self.student.id), 'status': '3'})

        self.assertEqual(response.json()['counts'], {
            'present_count': 0,
            'late_count': 0,
            'absent_count': 1,
            'excused_count': 0,
        })

    def test_switching_term_moves_a_same_day_edit_to_the_new_term(self):
        Tbltermsetting.objects.create(user=self.user, active_term=PRELIM)
        self.client.post('/attendance/ajax/save/', {'student_id': str(self.student.id), 'status': '1'})

        Tbltermsetting.objects.update(user=self.user, active_term=MIDTERM)
        self.client.post('/attendance/ajax/save/', {'student_id': str(self.student.id), 'status': '3'})

        record = Tblattendance.objects.get(student_id=self.student, attend_date=date.today())
        self.assertEqual(record.status, '3')
        self.assertEqual(record.term, MIDTERM)
        self.assertEqual(
            Tblattendance.objects.filter(student_id=self.student, attend_date=date.today()).count(),
            1,
        )

    def test_switching_term_leaves_previous_term_history_intact(self):
        Tbltermsetting.objects.create(user=self.user, active_term=PRELIM)
        self.client.post('/attendance/ajax/save/', {'student_id': str(self.student.id), 'status': '1'})

        Tbltermsetting.objects.update(user=self.user, active_term=MIDTERM)
        other_day = date.today() - timedelta(days=1)
        Tblattendance.objects.create(
            attend_date=other_day, student_id=self.student, status='2', term=PRELIM,
        )

        self.assertEqual(Tblattendance.objects.filter(student_id=self.student, term=PRELIM).count(), 2)
        self.assertEqual(Tblattendance.objects.filter(student_id=self.student, term=MIDTERM).count(), 0)


class TermScopedPagesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2026-2027', user=self.user)
        self.student = Tblstudents.objects.create(
            idno='1001', fullname='Jane Doe', courseid=self.course.courseid, user=self.user,
        )
        Tbltermsetting.objects.create(user=self.user, active_term=PRELIM)

        prelim_day = date.today() - timedelta(days=1)
        Tblattendance.objects.create(attend_date=prelim_day, student_id=self.student, status='3', term=PRELIM)

        self.client.login(username='tester', password='secret123')

    def test_students_list_counts_follow_the_view_term(self):
        active = self.client.get('/students/')
        self.assertEqual(active.context['students'][0]['attendance_counts']['absent_count'], 1)

        midterm = self.client.get('/students/?term=midterm')
        self.assertEqual(midterm.context['students'][0]['attendance_counts']['absent_count'], 0)
        self.assertEqual(midterm.context['view_term'], MIDTERM)
        self.assertFalse(midterm.context['is_active_term_view'])

    def test_calendar_only_renders_records_of_the_view_term(self):
        active = self.client.get(f'/attendance/calendar/{self.student.id}/')
        self.assertContains(active, 'Absent')

        midterm = self.client.get(f'/attendance/calendar/{self.student.id}/?term=midterm')
        self.assertNotContains(midterm, 'Absent')
        self.assertEqual(midterm.context['month_totals']['absent_count'], 0)

    def test_reports_expose_the_term_context(self):
        response = self.client.get('/reports/?term=midterm')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['view_term'], MIDTERM)

        for course_report in response.context['report_rows']:
            self.assertEqual(course_report['most_absent'], [])