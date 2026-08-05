from django.contrib import admin

from .models import Tblcourse, CourseSchedule, Quiz, QuizQuestion


@admin.register(Tblcourse)
class TblcourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'schoolyr', 'status')
    search_fields = ('name', 'section', 'schoolyr')


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'day', 'start_time', 'end_time', 'room')
    list_filter = ('day',)
    list_select_related = ('course',)
    search_fields = ('course__name', 'room')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'is_active', 'created_at')
    list_select_related = ('course',)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'question_type', 'order')
