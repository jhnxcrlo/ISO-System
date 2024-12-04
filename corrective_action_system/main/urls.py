from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import change_password, add_review, preview_rfa, generate_pdf, audit_report_summary_view, \
    generate_audit_report_summary_pdf, user_profile_view

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('password_change/', change_password, name='password_change'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),

    # User Management
    path('manage_users/', views.manage_users_view, name='manage_users'),
    path('add_user/', views.add_user, name='add_user'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('lead-auditor/lead_auditor_manage_user/', views.lead_auditor_manage_user, name='lead_auditor_manage_user'),

    # Announcements
    path('', views.announcement_list, name='announcement_list'),
    path('create/', views.create_announcement, name='create_announcement'),
    path('<int:pk>/update/', views.update_announcement, name='update_announcement'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),

    # Dashboards
    path('internal-auditor-dashboard/', views.internal_auditor_dashboard_view, name='internal_auditor_dashboard'),
    path('process-owner-dashboard/', views.process_owner_dashboard_view, name='process_owner_dashboard'),
    path('lead-auditor-dashboard/', views.lead_auditor_dashboard_view, name='lead_auditor_dashboard'),

    # Monitoring Logs
    path('internal-auditor-monitoring-log/', views.internal_auditor_monitoring_log, name='internal_auditor_monitoring_log'),
    path('lead-auditor-monitoring-log/', views.lead_auditor_monitoring_log, name='lead_auditor_monitoring_log'),
    path('internal-auditor-monitoring-log/', views.internal_auditor_monitoring_log, name='monitoring_log'),

    # Non-Conformity Management
    path('non-conformity/add/', views.add_non_conformity, name='add_non_conformity'),
    path('internal-auditor/non-conformity/<int:nc_id>/', views.combined_non_conformity_detail, name='non_conformity_detail'),
    path('lead-auditor/non-conformity/<int:nc_id>/', views.combined_non_conformity_detail, name='lead_auditor_non_conformity_detail'),
    path('internal-auditor/add-non-conformity/', views.add_non_conformity, name='add_non_conformity'),
    path('lead-auditor/add-non-conformity/', views.add_non_conformity, name='lead_auditor_add_non_conformity'),

    # Task Management
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/add_immediate_action/', views.add_immediate_action, name='add_immediate_action'),
    path('task/<int:task_id>/root-cause-analysis/', views.add_root_cause_analysis, name='add_root_cause_analysis'),
    path('task/<int:task_id>/corrective-action-plan/', views.corrective_action_plan, name='corrective_action_plan'),
    path('close-out/<int:nc_id>/', views.close_out_action, name='close_out_action'),
    path('non-conformity/<int:task_id>/complete_step/', views.complete_step, name='complete_step'),

    # RFA and PDFs
    path('rfa/pdf/<int:nc_id>/', generate_pdf, name='generate_pdf'),
    path('internal-auditor/preview-rfa/<int:nc_id>/', views.preview_rfa, name='preview_rfa'),
    path('lead-auditor/preview-rfa/<int:nc_id>/', views.preview_rfa, name='lead_auditor_preview_rfa'),

    # Corrective Action Plan Reviews and Follow-Up
    path('internal-auditor/add-follow-up/<int:nc_id>/', views.add_follow_up, name='add_follow_up'),
    path('lead-auditor/add-follow-up/<int:nc_id>/', views.add_follow_up, name='lead_auditor_add_follow_up'),
    path('internal-auditor/add-review/<int:cap_id>/', views.add_review, name='add_review'),
    path('lead-auditor/add-review/<int:cap_id>/', views.add_review, name='lead_auditor_add_review'),
    path('internal-auditor/action-verification/<int:cap_id>/', views.action_verification, name='action_verification'),
    path('lead-auditor/action-verification/<int:cap_id>/', views.action_verification, name='lead_auditor_action_verification'),

    # Forms Management
    path('lead-auditor/forms/', views.manage_forms_view, name='lead_auditor_forms'),
    path('internal-auditor/forms/', views.manage_forms_view, name='internal_auditor_forms'),
    path('forms/upload/', views.upload_template, name='upload_template'),
    path('forms/<int:pk>/delete/', views.delete_template, name='delete_template'),
    path('forms/<int:pk>/edit/', views.edit_template, name='edit_template'),
    path('forms/<int:pk>/download/', views.download_template, name='download_template'),
    path('process-owner/forms/', views.process_owner_forms_view, name='process_owner_forms'),

    # Guidelines
    path('lead-auditor/guidelines/', views.guideline_management_view, name='lead_auditor_guidelines'),
    path('internal-auditor/guidelines/', views.guideline_management_view, name='internal_auditor_guidelines'),
    path('process-owner/guidelines/', views.guideline_management_view, name='process_owner_guidelines'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_as_read, name='mark_notification_as_read'),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/administrator/registration/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='main/administrator/registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/administrator/registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='main/administrator/registration/password_reset_complete.html'), name='password_reset_complete'),
    path('audit-report-summary/', audit_report_summary_view, name='audit_report_summary'),
    path('audit-report-summary-pdf/', generate_audit_report_summary_pdf, name='audit_report_summary_pdf'),
    path("profile/", user_profile_view, name="user_profile"),

]

# Static and Media Files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
