from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list_page, name='course_list'),
    path('ajax/list/', views.course_list_ajax, name='course_list_ajax'),
    path('ajax/get/<str:pk>/', views.course_get_ajax, name='course_get_ajax'),
    path('ajax/save/', views.course_save_ajax, name='course_save_ajax'),
    path('ajax/delete/<str:pk>/', views.course_delete_ajax, name='course_delete_ajax'),
    path('<str:pk>/export-students/', views.course_students_export, name='course_students_export'),
    path('schedules/', views.schedule_page, name='schedule_list'),
    path('schedules/ajax/get/<int:pk>/', views.schedule_get_ajax, name='schedule_get_ajax'),
    path('schedules/ajax/save/', views.schedule_save_ajax, name='schedule_save_ajax'),
    path('schedules/ajax/delete/<int:pk>/', views.schedule_delete_ajax, name='schedule_delete_ajax'),
    path('schedules/ajax/events/', views.schedule_events_ajax, name='schedule_events_ajax'),
    path('<int:course_id>/quizzes/', views.quiz_list_page, name='quiz_list'),
    path('<int:course_id>/quizzes/save/', views.quiz_save_view, name='quiz_save'),
    path('<int:course_id>/quizzes/delete/<int:quiz_id>/', views.quiz_delete_view, name='quiz_delete'),
    path('quiz/<int:quiz_id>/preview/', views.quiz_preview_page, name='quiz_preview'),
    path('quiz/<int:quiz_id>/questions/save/', views.question_save_view, name='question_save'),
    path('quiz/question/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),
]
