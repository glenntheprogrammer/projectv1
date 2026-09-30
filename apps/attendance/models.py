from django.conf import settings
from django.db import models

from apps.students.models import Tblstudents

PRELIM = 'prelim'
MIDTERM = 'midterm'
ENDTERM = 'endterm'

TERM_CHOICES = [
    (PRELIM, 'Prelim'),
    (MIDTERM, 'Midterm'),
    (ENDTERM, 'End term'),
]
TERM_LABELS = dict(TERM_CHOICES)
DEFAULT_TERM = PRELIM


class Tblattendance(models.Model):
    attend_id = models.AutoField(primary_key=True)
    attend_date = models.DateField()
    student_id = models.ForeignKey(Tblstudents, on_delete=models.CASCADE, db_column='student_id', to_field='id')
    status = models.CharField(max_length=50)
    term = models.CharField(max_length=20, choices=TERM_CHOICES, default=DEFAULT_TERM)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tblattendance'
        constraints = [
            models.UniqueConstraint(
                fields=['student_id', 'attend_date'],
                name='unique_student_attendance_per_day',
            ),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.status}"


class Tbltermsetting(models.Model):
    """Which term the user is currently recording attendance for."""

    setting_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='term_setting',
        on_delete=models.CASCADE,
    )
    active_term = models.CharField(max_length=20, choices=TERM_CHOICES, default=DEFAULT_TERM)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbltermsetting'

    def __str__(self):
        return f"{self.user} - {self.get_active_term_display()}"
