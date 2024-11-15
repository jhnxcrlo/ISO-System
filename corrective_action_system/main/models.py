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
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
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


class Template(models.Model):
    template_name = models.CharField(max_length=100)
    description = models.TextField()
    template_file = models.FileField(upload_to='templates/')
    completed = models.BooleanField(default=False)  # New field to track completion


class NonConformity(models.Model):
    non_conformity = models.CharField(max_length=255)
    assignees = models.CharField(max_length=255)
    originator_name = models.CharField(max_length=100)
    unit_department = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    RFA_INTENT_CHOICES = [
        ('correct_nc', 'Correct NC'),
        ('prevent_nc', 'Prevent NC'),
        ('improvement', 'Improvement')
    ]
    rfa_intent = models.CharField(max_length=20, choices=RFA_INTENT_CHOICES)

    department = models.CharField(max_length=100)

    CATEGORY_CHOICES = [
        ('iqa_related', 'IQA-Related'),
        ('supplier_related', 'Supplier-Related'),
        ('3rd_party_audit_related', '3rd Party Audit Related'),
        ('process_procedural', 'Process/Procedural-related'),
        ('customer_satisfaction', 'Customer Satisfaction Related'),
        ('kpi_quality_objective', 'Relates to KPI/Quality Objective Review'),
        ('hrd_related', 'HRD-Related'),
        ('others', 'Others')
    ]
    non_conformance_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    description_of_non_conformance = models.TextField()
    iso_clause = models.CharField(max_length=50)

    TASK_CATEGORY_CHOICES = [('major', 'Major'), ('minor', 'Minor'), ('others', 'Others')]
    category = models.CharField(max_length=20, choices=TASK_CATEGORY_CHOICES)

    task = models.IntegerField()
    start_date = models.DateField()
    deadline = models.DateField()

    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')

    def __str__(self):
        return f"{self.non_conformity} - {self.originator_name}"


# Model for Immediate Action
class ImmediateAction(models.Model):
    non_conformity = models.OneToOneField(NonConformity, on_delete=models.CASCADE, related_name='immediate_action')
    action_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Immediate Action for {self.non_conformity.non_conformity}"


# Model for Root Cause Analysis
class RootCauseAnalysis(models.Model):
    non_conformity = models.OneToOneField(NonConformity, on_delete=models.CASCADE, related_name='root_cause_analysis')
    cause_description = models.TextField()
    rca_date = models.DateField(null=True, blank=True)
    responsible_officer = models.CharField(max_length=100)
    estimated_close_date = models.DateField(null=True, blank=True)
    fishbone_data = models.JSONField(blank=True, null=True)  # For storing Fishbone Diagram data
    five_whys = models.JSONField(default=dict)
    root_cause_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Root Cause Analysis for {self.non_conformity.non_conformity}"


class CorrectiveActionPlan(models.Model):
    non_conformity = models.ForeignKey('NonConformity', on_delete=models.CASCADE, related_name='corrective_action_plans')
    activity = models.TextField(verbose_name="Step-by-Step Activities")
    responsible_person = models.CharField(max_length=100, verbose_name="Responsible Person/Unit")
    time_frame = models.CharField(max_length=100, verbose_name="Time Frame")
    resources_needed = models.CharField(max_length=255, verbose_name="Resources Needed")
    result = models.TextField(blank=True, null=True, verbose_name="Result")

    def __str__(self):
        return f"Corrective Action for {self.non_conformity.non_conformity}"