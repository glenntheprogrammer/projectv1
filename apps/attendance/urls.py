from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('ajax/save/', views.attendance_save_ajax, name='attendance_save_ajax'),
    path('calendar/<int:student_id>/', views.attendance_calendar_view, name='attendance_calendar'),
]
