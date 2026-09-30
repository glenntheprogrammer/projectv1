from django.urls import path
from . import views

app_name = 'termsettings'

urlpatterns = [
    path('', views.term_settings_view, name='term_settings'),
]
