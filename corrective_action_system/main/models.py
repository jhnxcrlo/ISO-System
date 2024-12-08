# models.py

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

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
    class StageChoices(models.TextChoices):
        OPEN = 'open', 'Open'
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        CLOSED = 'closed', 'Closed'

    # New nc_stage field to track non-conformity status
    nc_stage = models.CharField(max_length=20, choices=StageChoices.choices, default=StageChoices.OPEN)

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

    TASK_CATEGORY_CHOICES = [('major', 'Major'), ('minor', 'Minor'), ('ofi', 'OFI')]
    category = models.CharField(max_length=20, choices=TASK_CATEGORY_CHOICES)
    start_date = models.DateField()

    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')


    def __str__(self):
        return f"{self.non_conformity} - {self.originator_name}"

    def get_task_url(self):
        """Return the Process Owner-specific URL."""
        return reverse('task_detail', kwargs={'task_id': self.pk})

    def get_non_conformity_url(self):
        """Return the Internal Auditor-specific URL."""
        return reverse('non_conformity_detail', kwargs={'nc_id': self.pk})


# Signals for automating the status update
@receiver(post_save, sender=NonConformity)
def update_nc_stage(sender, instance, created, **kwargs):
    if created:
        # When a new non-conformity is created, set status to OPEN
        instance.nc_stage = NonConformity.StageChoices.OPEN
        instance.save()

    # Automate status change based on conditions
    # If the non-conformity has a corrective action plan, set status to PENDING
    if instance.status == 'in_progress' and instance.nc_stage == NonConformity.StageChoices.OPEN:
        instance.nc_stage = NonConformity.StageChoices.PENDING
        instance.save()

    # If the non-conformity has been verified as effective, set status to CLOSED
    if instance.status == 'completed' and instance.nc_stage == NonConformity.StageChoices.PENDING:
        instance.nc_stage = NonConformity.StageChoices.CLOSED
        instance.save()

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
        choices=[("effective", "Close (Effective)"), ("not_effective", "Close (Not Effective)")]
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

class AuditDetails(models.Model):
    date_range = models.CharField(
        max_length=255,
        verbose_name="Audit Date Range",
        help_text="Specify the date range of the audit."
    )
    location = models.CharField(
        max_length=255,
        verbose_name="Audit Location",
        help_text="Specify the location where the audit was conducted."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date Created",
        help_text="The date and time when this audit detail was created."
    )

    class Meta:
        verbose_name = "Audit Detail"
        verbose_name_plural = "Audit Details"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.date_range} | {self.location}"


class GoodPoints(models.Model):
    audit_detail = models.ForeignKey(
        AuditDetails,
        on_delete=models.CASCADE,
        null=True,  # Allow null values for existing rows
        blank=True,  # Allow forms to leave this field empty
        related_name='good_points',  # Enable reverse relation from AuditDetails
        verbose_name='Audit Detail',  # Human-readable name for admin
        help_text="Link this good point to a specific audit detail."
    )
    campus = models.CharField(
        max_length=255,
        verbose_name='Campus',
        help_text='Enter the campus associated with this good point.'
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Provide a detailed description of the good point.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date Created',
        help_text='The date and time when this entry was created.'
    )

    class Meta:
        verbose_name = 'Good Point'
        verbose_name_plural = 'Good Points'
        ordering = ['-created_at']

    def __str__(self):
        return f"Good Point: {self.campus} - {self.description[:50]}"


class AuditFinding(models.Model):
    ref_no = models.AutoField(primary_key=True)  # Auto increment for ref_no
    clause_no = models.CharField(
        max_length=50,
        verbose_name="Clause Number"
    )
    details = models.TextField(
        verbose_name="Details"
    )
    finding_type = models.CharField(
        max_length=50,
        choices=NonConformity.TASK_CATEGORY_CHOICES,  # Use the task category choices
        verbose_name="Finding Type"
    )
    linked_rfa = models.ForeignKey(
        NonConformity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Linked RFA"
    )
    audit_detail = models.ForeignKey(
        AuditDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="audit_findings",
        verbose_name="Audit Detail",
        help_text="Link this finding to an audit detail."
    )

    def __str__(self):
        return f"Ref No: {self.ref_no}, Clause No: {self.clause_no}"

    @classmethod
    def create_from_non_conformity(cls, non_conformity: NonConformity):
        """Method to create an AuditFinding from a NonConformity instance."""
        return cls.objects.create(
            clause_no=non_conformity.iso_clause,
            details=non_conformity.description_of_non_conformance,
            finding_type=non_conformity.category,
            linked_rfa=non_conformity
        )


class Evaluation(models.Model):
    ROLE_CHOICES = [
        ('process_owner', 'Process Owner'),
        ('lead_auditor', 'Lead Auditor'),
    ]

    action_verification = models.ForeignKey(
        'ActionVerification',
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    # Section A: Knowledge of ISO 9001:2015 Standards
    knowledge1 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    knowledge2 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    knowledge3 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    knowledge4 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    knowledge5 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    # Section B: Communication Skills
    communication1 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    communication2 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    communication3 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    communication4 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    communication5 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    # Section C: Audit Execution
    audit_execution1 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    audit_execution2 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    audit_execution3 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    audit_execution4 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    audit_execution5 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    # Section E: Continual Improvement
    continual_improvement1 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    continual_improvement2 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    continual_improvement3 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    continual_improvement4 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    continual_improvement5 = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    # Additional feedback
    feedback = models.TextField(blank=True, null=True)

    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation by {self.evaluator} ({self.role})"

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"



