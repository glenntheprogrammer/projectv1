from django.shortcuts import get_object_or_404

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse, CourseSchedule, Quiz, QuizQuestion
from apps.students.models import Tblstudents


def scoped_courses(user):
    return Tblcourse.objects.filter(user=user)


def scoped_students(user):
    return Tblstudents.objects.filter(user=user)


def scoped_attendance(user):
    return Tblattendance.objects.filter(student_id__user=user)


def scoped_course(user, pk):
    return get_object_or_404(scoped_courses(user), pk=pk)


def scoped_student(user, pk):
    return get_object_or_404(scoped_students(user), pk=pk)


def scoped_schedules(user):
    return CourseSchedule.objects.select_related('course').filter(course__user=user)


def scoped_quizzes(user):
    return Quiz.objects.filter(course__user=user)


def scoped_quiz_questions(user):
    return QuizQuestion.objects.filter(quiz__course__user=user)
