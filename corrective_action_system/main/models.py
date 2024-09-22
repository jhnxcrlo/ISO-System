from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Process Owner', 'Process Owner'),
        ('Lead Auditor', 'Lead Auditor'),
        ('Internal Auditor', 'Internal Auditor'),
        ('External Auditor', 'External Auditor'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    email_verified = models.BooleanField(default=False)
    password_needs_reset = models.BooleanField(default=False)  # Field to track password reset

    def __str__(self):
        return self.user.username


class LoginEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.timestamp}"


class TemplateModel(models.Model):
    template_name = models.CharField(max_length=255)
    description = models.TextField(default="No description provided")
    file = models.FileField(upload_to='templates/')

    def __str__(self):
        return self.template_name


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Creator of the announcement

    def __str__(self):
        return self.title


class Guideline(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='guidelines/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title