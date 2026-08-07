from django.conf import settings
from django.db import models


class Tblcourse(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    courseid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    section = models.CharField(max_length=100)
    schoolyr = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='courses',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'tblcourse'

    def __str__(self):
        return self.name


class CourseSchedule(models.Model):
    DAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    course = models.ForeignKey(Tblcourse, related_name='schedules', on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'tblcourseschedule'
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.course.name} - {self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Quiz(models.Model):
    course = models.ForeignKey(Tblcourse, related_name='quizzes', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblquiz'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('identification', 'Identification'),
        ('true_false', 'True/False'),
        ('multiple_choice', 'Multiple Choice'),
    ]

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    option_a = models.CharField(max_length=255, blank=True)
    option_b = models.CharField(max_length=255, blank=True)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    correct_option = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'tblquizquestion'
        ordering = ['order', 'id']

    def __str__(self):
        return self.question_text[:80]
