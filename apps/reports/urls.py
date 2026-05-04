from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_main, name='reports'),
]
