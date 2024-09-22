from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
                  # Authentication-related paths
                  path('login/', views.login_view, name='login'),
                  path('password_reset/', auth_views.PasswordResetView.as_view(
                      template_name='main/administrator/registration/password_reset.html'), name='password_reset'),
                  path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
                      template_name='main/administrator/registration/password_reset_done.html'),
                       name='password_reset_done'),
                  path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
                      template_name='main/administrator/registration/password_reset_confirm.html'),
                       name='password_reset_confirm'),
                  path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
                      template_name='main/administrator/registration/password_reset_complete.html'),
                       name='password_reset_complete'),

                  # Dashboard views
                  path('dashboard/', views.dashboard_view, name='dashboard'),
                  path('internal-auditor-dashboard/', views.internal_auditor_dashboard_view,
                       name='internal_auditor_dashboard'),
                  path('process-owner-dashboard/', views.process_owner_dashboard_view, name='process_owner_dashboard'),

                  # User management
                  path('manage_users/', views.manage_users_view, name='manage_users'),
                  path('add_user/', views.add_user, name='add_user'),
                  path('delete_user/<int:user_id>/', views.delete_user_view, name='delete_user'),
                  path('verify/<str:token>/', views.verify_email, name='verify_email'),

                  # Announcements
                  path('announcements/', views.announcement_list, name='announcement_list'),
                  path('announcements/create/', views.announcement_create, name='announcement_create'),
                  path('announcements/<int:pk>/update/', views.announcement_update, name='announcement_update'),
                  path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

                  # Guidelines and forms
                  path('guidelines/', views.guidelines_view, name='guidelines'),
                  path('forms/', views.forms_view, name='forms'),
                  path('upload-template/', views.upload_template, name='upload_template'),
                  path('download-template/<int:pk>/', views.download_template, name='download_template'),
                  path('forms/<int:pk>/delete/', views.delete_template, name='delete_template'),

                  # Process Owner specific
                  path('process-owner-forms/', views.process_owner_forms_view, name='process_owner_forms'),
                  path('process-owner-guidelines/', views.process_owner_guidelines_view,
                       name='process_owner_guidelines'),

                  # Internal Auditor specific
                  path('internal-auditor-forms/', views.internal_auditor_forms_view, name='internal_auditor_forms'),
                  path('internal-auditor-guidelines/', views.internal_auditor_guidelines_view,
                       name='internal_auditor_guidelines'),
                  path('main/internal_auditor_monitoring_log/', views.internal_auditor_monitoring_log,
                        name='internal_auditor_monitoring_log'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
