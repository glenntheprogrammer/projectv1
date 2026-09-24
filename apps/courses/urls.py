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
    path('<int:course_id>/quizzes/', views.quiz_list_page, name='quiz_list'),
    path('<int:course_id>/quizzes/save/', views.quiz_save_view, name='quiz_save'),
    path('<int:course_id>/quizzes/delete/<int:quiz_id>/', views.quiz_delete_view, name='quiz_delete'),
    path('quiz/<int:quiz_id>/preview/', views.quiz_preview_page, name='quiz_preview'),
    path('quiz/<int:quiz_id>/questions/save/', views.question_save_view, name='question_save'),
    path('quiz/question/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),
]
