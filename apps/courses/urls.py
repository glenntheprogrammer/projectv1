from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list_page, name='course_list'),
    path('ajax/list/', views.course_list_ajax, name='course_list_ajax'),
    path('ajax/get/<str:pk>/', views.course_get_ajax, name='course_get_ajax'),
    path('ajax/save/', views.course_save_ajax, name='course_save_ajax'),
    path('ajax/delete/<str:pk>/', views.course_delete_ajax, name='course_delete_ajax'),
]
