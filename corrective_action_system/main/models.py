from django.conf import settings
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
    start_date = models.DateField()

    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')

    def __str__(self):
        return f"{self.non_conformity} - {self.originator_name}"


# Model for Immediate Action
class ImmediateAction(models.Model):
    non_conformity = models.OneToOneField(NonConformity, on_delete=models.CASCADE, related_name='immediate_action')
    action_description = models.TextField()
    acknowledged_by = models.CharField(max_length=255, default="Unknown")  # Add field for acknowledgment name
    acknowledgment_date = models.DateField(null=True, blank=True)  # Add field for the acknowledgment date

    def __str__(self):
        return f"Immediate Action for {self.non_conformity.non_conformity}"



# Model for Root Cause Analysis
class RootCauseAnalysis(models.Model):
    non_conformity = models.OneToOneField(NonConformity, on_delete=models.CASCADE, related_name='root_cause_analysis')
    cause_description = models.TextField()
    rca_date = models.DateField(null=True, blank=True)
    responsible_officer = models.CharField(max_length=100)
    estimated_close_date = models.DateField(null=True, blank=True)
    root_cause_completed = models.BooleanField(default=False)
    supporting_evidence = models.FileField(upload_to='supporting_evidence/', blank=True, null=True)

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

class CorrectiveActionPlanReview(models.Model):
    corrective_action_plan = models.ForeignKey(
        'CorrectiveActionPlan', on_delete=models.CASCADE, related_name='reviews'
    )
    effectiveness = models.CharField(
        max_length=20,
        choices=[('Accepted', 'Accepted'), ('Not Accepted', 'Not Accepted')],
        verbose_name="Effectiveness"
    )
    reason = models.TextField(
        blank=True, null=True, verbose_name="Reason (if Not Accepted)"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Reviewed By"
    )
    review_date = models.DateField(auto_now_add=True, verbose_name="Review Date")

    restart_process = models.BooleanField(default=False, verbose_name="Restart Process Required")

    def __str__(self):
        return f"Review of {self.corrective_action_plan} by {self.reviewer}"

class FollowUpAction(models.Model):
    non_conformity = models.ForeignKey(
        'NonConformity',
        on_delete=models.CASCADE,
        related_name='follow_up_actions'
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed')
        ],
        default='Pending'
    )
    responsible_person = models.CharField(max_length=100, verbose_name="Initials / Responsibility")
    follow_up_date = models.DateField(verbose_name="Follow-Up Date")

    def __str__(self):
        return f"Follow-Up: {self.non_conformity.non_conformity} ({self.status})"


class ActionVerification(models.Model):
    corrective_action_plan = models.ForeignKey(
        'CorrectiveActionPlan',
        on_delete=models.CASCADE,
        related_name='action_verifications'
    )

    visit_number = models.IntegerField(verbose_name="No. of Visits")
    date = models.DateField()
    follow_up_audit_result = models.TextField(verbose_name="Follow-up Audit Result (Objective Evidences)")
    new_target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("effective", "Close (Effective)"),
            ("not_effective", "Close (Not Effective)")
        ]
    )
    new_rfa_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="New RFA #")

    def __str__(self):
        return f"Visit {self.visit_number}: {self.status}"


class CloseOut(models.Model):
    non_conformity = models.OneToOneField(
        'NonConformity', on_delete=models.CASCADE, related_name='close_out'
    )
    auditor_name = models.CharField(max_length=255)
    auditor_date = models.DateField()
    process_owner_name = models.CharField(max_length=255)
    process_owner_date = models.DateField()

    def __str__(self):
        return f"Close Out for {self.non_conformity.non_conformity}"

class Comment(models.Model):
    SECTION_CHOICES = [
        ('immediate_action', 'Immediate Action'),
        ('root_cause', 'Root Cause Analysis'),
        ('corrective_action', 'Corrective Action Plan'),
    ]

    task = models.ForeignKey('NonConformity', on_delete=models.CASCADE, related_name='comments')
    section = models.CharField(max_length=50, choices=SECTION_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.task} - {self.get_section_display()}"

    @property
    def is_reply(self):
        return self.parent is not None

