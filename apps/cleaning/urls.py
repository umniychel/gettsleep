from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/start/', views.task_start, name='task_start'),
    path('<int:pk>/complete/', views.task_complete, name='task_complete'),
]
