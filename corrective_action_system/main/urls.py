from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import change_password


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('internal-auditor-dashboard/', views.internal_auditor_dashboard_view, name='internal_auditor_dashboard'),
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
    path('guidelines/', views.guideline_list, name='guideline_list'),
    path('guidelines/upload/', views.upload_guideline, name='upload_guideline'),
    path('guidelines/<int:pk>/edit/', views.edit_guideline, name='edit_guideline'),
    path('guidelines/<int:pk>/delete/', views.delete_guideline, name='delete_guideline'),
    path('forms/', views.forms_view, name='forms'),
    path('upload-template/', views.upload_template, name='upload_template'),
    path('download-template/<int:pk>/', views.download_template, name='download_template'),
    path('forms/<int:pk>/delete/', views.delete_template, name='delete_template'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/administrator/registration/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='main/administrator/registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/administrator/registration/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='main/administrator/registration/password_reset_complete.html'), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
