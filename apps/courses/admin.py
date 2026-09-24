from django.contrib import admin

from .models import Tblcourse, Quiz, QuizQuestion


@admin.register(Tblcourse)
class TblcourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'schoolyr', 'status')
    search_fields = ('name', 'section', 'schoolyr')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'is_active', 'created_at')
    list_select_related = ('course',)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'question_type', 'order')
