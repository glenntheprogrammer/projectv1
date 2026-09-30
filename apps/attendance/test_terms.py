from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.attendance.models import (
    DEFAULT_TERM,
    ENDTERM,
    MIDTERM,
    PRELIM,
    TERM_CHOICES,
    Tblattendance,
    Tbltermsetting,
)
from apps.attendance.terms import (
    get_active_term,
    set_active_term,
    status_counts,
    term_breakdown,
    view_term,
)
from apps.courses.models import Tblcourse
from apps.students.models import Tblstudents


class ActiveTermSettingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')

    def test_defaults_to_prelim_when_no_setting_exists(self):
        self.assertEqual(get_active_term(self.user), PRELIM)
        self.assertEqual(get_active_term(self.user), DEFAULT_TERM)

    def test_set_active_term_creates_then_updates_one_row(self):
        set_active_term(self.user, MIDTERM)
        self.assertEqual(get_active_term(self.user), MIDTERM)

        set_active_term(self.user, ENDTERM)
        self.assertEqual(get_active_term(self.user), ENDTERM)
        self.assertEqual(Tbltermsetting.objects.filter(user=self.user).count(), 1)

    def test_term_is_stored_per_user(self):
        other = get_user_model().objects.create_user(username='other', password='secret123')
        set_active_term(self.user, ENDTERM)

        self.assertEqual(get_active_term(other), PRELIM)

    def test_unrecognised_stored_term_falls_back_to_default(self):
        Tbltermsetting.objects.create(user=self.user, active_term='nonsense')

        self.assertEqual(get_active_term(self.user), PRELIM)


class ViewTermTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.factory = RequestFactory()

    def test_defaults_to_the_active_term(self):
        set_active_term(self.user, MIDTERM)
        request = self.factory.get('/students/')
        request.user = self.user

        self.assertEqual(view_term(request), MIDTERM)

    def test_query_string_overrides_the_active_term(self):
        set_active_term(self.user, MIDTERM)
        request = self.factory.get('/students/?term=endterm')
        request.user = self.user

        self.assertEqual(view_term(request), ENDTERM)

    def test_unknown_query_string_value_ignores_override(self):
        set_active_term(self.user, MIDTERM)
        request = self.factory.get('/students/?term=bogus')
        request.user = self.user

        self.assertEqual(view_term(request), MIDTERM)


class StatusCountsTests(TestCase):
    def test_counts_group_by_status(self):
        student = Tblstudents.objects.create(idno='1001', fullname='Jane Doe', courseid=1)

        # The unique constraint is one row per student per day, so spread the
        # statuses across different dates.
        Tblattendance.objects.create(attend_date='2026-08-01', student_id=student, status='1', term=PRELIM)
        Tblattendance.objects.create(attend_date='2026-08-02', student_id=student, status='1', term=PRELIM)
        Tblattendance.objects.create(attend_date='2026-08-03', student_id=student, status='3', term=PRELIM)

        counts = status_counts(Tblattendance.objects.filter(term=PRELIM))

        self.assertEqual(counts, {
            'present_count': 2,
            'late_count': 0,
            'absent_count': 1,
            'excused_count': 0,
        })

    def test_term_breakdown_splits_totals_per_term(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        course = Tblcourse.objects.create(name='Math', section='A', schoolyr='2026-2027', user=user)
        student = Tblstudents.objects.create(
            idno='1001', fullname='Jane Doe', courseid=course.courseid, user=user,
        )

        Tblattendance.objects.create(attend_date='2026-08-01', student_id=student, status='1', term=PRELIM)
        Tblattendance.objects.create(attend_date='2026-08-02', student_id=student, status='2', term=MIDTERM)
        Tblattendance.objects.create(attend_date='2026-08-03', student_id=student, status='2', term=MIDTERM)

        rows = {row['slug']: row for row in term_breakdown(user)}

        self.assertEqual([slug for slug, _ in TERM_CHOICES], [PRELIM, MIDTERM, ENDTERM])
        self.assertEqual(rows[PRELIM]['counts']['present_count'], 1)
        self.assertEqual(rows[PRELIM]['total'], 1)
        self.assertEqual(rows[MIDTERM]['counts']['late_count'], 2)
        self.assertEqual(rows[MIDTERM]['total'], 2)
        self.assertEqual(rows[ENDTERM]['total'], 0)


class TermChoicesTests(TestCase):
    def test_three_fixed_terms_are_offered(self):
        self.assertEqual(TERM_CHOICES, [
            ('prelim', 'Prelim'),
            ('midterm', 'Midterm'),
            ('endterm', 'End term'),
        ])