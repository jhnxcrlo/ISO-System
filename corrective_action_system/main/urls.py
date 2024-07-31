from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('manage_users/', views.manage_users_view, name='manage_users'),
    path('add_user/', views.add_user_view, name='add_user'),
    path('update_user/<int:user_id>/', views.update_user_view, name='update_user'),
    path('delete_user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('announcements/', views.announcements_view, name='announcements'),
    path('guidelines/', views.guidelines_view, name='guidelines'),
    path('forms/', views.forms_view, name='forms'),
    path('settings/', views.settings_view, name='settings'),
    path('generate_report/<str:report_type>/', views.generate_report, name='generate_report'),

]
