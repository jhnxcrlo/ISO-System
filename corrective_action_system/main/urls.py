from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('internal-auditor-dashboard/', views.internal_auditor_dashboard_view, name='internal_auditor_dashboard'),
    path('process-owner-dashboard/', views.process_owner_dashboard_view, name='process_owner_dashboard'),
    path('manage_users/', views.manage_users_view, name='manage_users'),
    path('add_user/', views.add_user, name='add_user'),
    path('update_user/<int:user_id>/', views.update_user_view, name='update_user'),
    path('delete_user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/update/', views.announcement_update, name='announcement_update'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('guidelines/', views.guidelines_view, name='guidelines'),
    path('forms/', views.forms_view, name='forms'),
    path('upload-template/', views.upload_template, name='upload_template'),
    path('download-template/<int:pk>/', views.download_template, name='download_template'),
    path('forms/<int:pk>/delete/', views.delete_template, name='delete_template'),
    path('generate-report/<int:report_type>/', views.generate_report, name='generate_report'),
    path('settings/', views.settings_view, name='settings'),
    path('generate_report/<str:report_type>/', views.generate_report, name='generate_report'),
]
