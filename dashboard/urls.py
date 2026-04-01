from django.urls import path

from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('teacher/', views.teacher_panel, name='teacher_panel'),
    path('quiz/', views.quiz_page, name='quiz_page'),
    path('quiz/submit/', views.quiz_submit, name='quiz_submit'),
    path('homework/', views.homework_page, name='homework_page'),
]

