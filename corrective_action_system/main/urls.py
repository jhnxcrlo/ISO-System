from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import change_password, add_review

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('internal-auditor-dashboard/', views.internal_auditor_dashboard_view, name='internal_auditor_dashboard'),
    path('internal-auditor-monitoring-log/', views.internal_auditor_monitoring_log, name='internal_auditor_monitoring_log'),
    path('internal-auditor/forms/', views.internal_auditor_forms_view, name='internal_auditor_forms'),
    path('process-owner-forms/', views.process_owner_forms_view, name='process_owner_forms'),
    path('process-owner-dashboard/', views.process_owner_dashboard_view, name='process_owner_dashboard'),
    path('manage_users/', views.manage_users_view, name='manage_users'),
    path('add_user/', views.add_user, name='add_user'),
    path('delete_user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('password_change/', change_password, name='password_change'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('', views.announcement_list, name='announcement_list'),
    path('create/', views.create_announcement, name='create_announcement'),
    path('<int:pk>/update/', views.update_announcement, name='update_announcement'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),
                  # Admin views
    path('administrator/guidelines/', views.admin_guideline_list, name='admin_guideline_list'),
    path('administrator/guidelines/upload/', views.admin_upload_guideline, name='admin_upload_guideline'),
    path('administrator/guidelines/edit/<int:pk>/', views.admin_edit_guideline, name='admin_edit_guideline'),
    path('administrator/guidelines/delete/<int:pk>/', views.admin_delete_guideline,name='admin_delete_guideline'),

                  # Internal Auditor views
    path('internal-auditor/guidelines/', views.internal_auditor_guideline_list,name='internal_auditor_guideline_list'),
    path('internal-auditor/guidelines/upload/', views.internal_auditor_upload_guideline,name='internal_auditor_upload_guideline'),
    path('internal-auditor/guidelines/edit/<int:pk>/', views.internal_auditor_edit_guideline,name='internal_auditor_edit_guideline'),
    path('internal-auditor/guidelines/delete/<int:pk>/', views.internal_auditor_delete_guideline,name='internal_auditor_delete_guideline'),
    path('non-conformity/add/', views.add_non_conformity, name='add_non_conformity'),
    path('internal-auditor-monitoring-log/', views.internal_auditor_monitoring_log, name='monitoring_log'),  # Your monitoring log view
    path('fm-qms-010-page-1/', views.fm_qms_010_page_1, name='fm_qms_010_page_1'),
    path('non_conformity/<int:nc_id>/add_follow_up/', views.add_follow_up, name='add_follow_up'),
    path('corrective_action_plan/<int:cap_id>/add_review/', views.add_review, name='add_review'),
    path('close-out/<int:nc_id>/', views.close_out_action, name='close_out_action'),
    path('non-conformity/<int:task_id>/complete_step/', views.complete_step, name='complete_step'),
#path('rfa-form/', views.rfa_create, name='create_rfa'),


                  # Process Owner views (view only)
    path('process-owner/guidelines/', views.process_owner_guideline_list,name='process_owner_guideline_list'),    path('forms/', views.forms_view, name='forms'),
    path('upload-template/', views.upload_template, name='upload_template'),
    path('download-template/<int:pk>/', views.download_template, name='download_template'),
    path('forms/<int:pk>/delete/', views.delete_template, name='delete_template'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/administrator/registration/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='main/administrator/registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/administrator/registration/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='main/administrator/registration/password_reset_complete.html'), name='password_reset_complete'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/add_immediate_action/', views.add_immediate_action, name='add_immediate_action'),
    path('task/<int:task_id>/root-cause-analysis/', views.add_root_cause_analysis, name='add_root_cause_analysis'),
    path('task/<int:task_id>/corrective-action-plan/', views.corrective_action_plan, name='corrective_action_plan'),
    #path for deleting corrective action
    path('internal-audit/non-conformity/<int:nc_id>/', views.non_conformity_detail, name='non_conformity_detail'),
    #path for corrective action verification
    path('corrective_action_plan/<int:cap_id>/verification/', views.action_verification, name='action_verification'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)