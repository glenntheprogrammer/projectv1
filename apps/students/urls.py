from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list_page, name='student_list'),
    path('course/<str:course_id>/', views.student_list_page, name='student_list_by_course'),
    path('ajax/list/', views.student_list_ajax, name='student_list_ajax'),
    path('ajax/get/<int:pk>/', views.student_get_ajax, name='student_get_ajax'),
    path('ajax/save/', views.student_save_ajax, name='student_save_ajax'),
    path('ajax/delete/<int:pk>/', views.student_delete_ajax, name='student_delete_ajax'),
]
