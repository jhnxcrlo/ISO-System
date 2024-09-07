from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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

    def __str__(self):
        return self.user.username


class LoginEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.timestamp}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TemplateModel(models.Model):
    template_name = models.CharField(max_length=255)
    description = models.TextField(default="No description provided")
    file = models.FileField(upload_to='templates/')

    def __str__(self):
        return self.template_name


class RFA(models.Model):
    NON_CONFORMITY_TYPES = [
        ('IQA', 'IQA-Related'),
        ('Supplier', 'Supplier-Related'),
        ('3rd_Party', '3rd Party Audit Related'),
        ('Customer', 'Customer Satisfaction Related'),
        ('Process', 'Process/Procedural-related'),
        ('HRD', 'HRD-Related'),
        ('KPI', 'Relates to KPI/Quality Objective Review'),
        ('Other', 'Others'),
    ]

    CATEGORY_CHOICES = [
        ('Major', 'Major'),
        ('Minor', 'Minor'),
    ]

    reference_number = models.CharField(max_length=50, unique=True, default='DEFAULT_REF')
    date_issued = models.DateField(auto_now_add=True)
    originator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Make sure '1' is a valid user ID
    department = models.CharField(max_length=100, default='General')
    description = models.TextField(default='No description provided')
    non_conformity_type = models.CharField(max_length=20, choices=NON_CONFORMITY_TYPES, default='Other')
    iso_clause_reference = models.CharField(max_length=50, blank=True, default='')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='Minor')
    immediate_action = models.TextField(default='No immediate action provided')
    root_cause_analysis = models.TextField(blank=True, null=True)
    corrective_action_plan = models.TextField(blank=True, null=True)
    responsible_officer = models.CharField(max_length=100, blank=True, default='N/A')
    due_date = models.DateField(blank=True, null=True)
    close_out_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, default="Open")

    def __str__(self):
        return self.reference_number


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who made the comment
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Generic relation to any model
    object_id = models.PositiveIntegerField()  # The ID of the object being commented on
    content_object = GenericForeignKey('content_type', 'object_id')  # Combines the content_type and object_id
    content = models.TextField()  # The text of the comment
    timestamp = models.DateTimeField(default=timezone.now)  # When the comment was made
    status = models.CharField(max_length=20, default='Pending')  # Comment status

    def __str__(self):
        return f'Comment by {self.user.username} on {self.content_type}'
