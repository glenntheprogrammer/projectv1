from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.course_reports_view, name='course_reports'),
]
