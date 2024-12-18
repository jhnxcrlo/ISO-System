# forms.py
from datetime import timezone

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import TemplateModel, Guideline, Announcement, NonConformity, ImmediateAction, RootCauseAnalysis, \
    CorrectiveActionPlan, FollowUpAction, CorrectiveActionPlanReview, ActionVerification, CloseOut, UserProfile, \
    GoodPoints, AuditFinding, AuditDetails, Evaluation


class UserCreationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True, label="Role")  # Ensure role is required

    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role']  # Ensure role is included

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': self.cleaned_data['role']}
            )
        return user



# User update form for modifying existing user details
class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[
        ('Process Owner', 'Process Owner'),
        ('Internal Auditor', 'Internal Auditor'),
        ('Lead Auditor', 'Lead Auditor')
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'role']


# Basic form for creating reports
class ReportForm(forms.Form):
    report_title = forms.CharField(max_length=200, label='Report Title')
    report_date = forms.DateField(label='Report Date', widget=forms.TextInput(attrs={'type': 'date'}))
    description = forms.CharField(widget=forms.Textarea, label='Description')


# Form for managing template files
class TemplateForm(forms.ModelForm):
    class Meta:
        model = TemplateModel
        fields = ['template_name', 'description', 'file']


# Form for creating and managing announcements
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']


# Form for creating and managing guidelines
class GuidelineForm(forms.ModelForm):
    class Meta:
        model = Guideline
        fields = ['title', 'description', 'file']


# Custom password change form with additional first_name and last_name fields
class CustomPasswordChangeForm(PasswordChangeForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))
    position = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Position'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Department'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'old_password', 'new_password1', 'new_password2', 'phone_number', 'position', 'department']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Update the user's first and last name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        # Update the related UserProfile fields
        user_profile = user.userprofile
        user_profile.phone_number = self.cleaned_data['phone_number']
        user_profile.position = self.cleaned_data['position']
        user_profile.department = self.cleaned_data['department']

        if commit:
            user.save()
            user_profile.save()
        return user

class NonConformityForm(forms.ModelForm):
    class Meta:
        model = NonConformity
        fields = [
            'non_conformity', 'assignees', 'unit_department',
            'rfa_intent', 'non_conformance_category', 'description_of_non_conformance',
            'iso_clause', 'category', 'status', 'assigned_to'
        ]  # Removed originator_name, email, phone, department, and start_date

        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),  # Optional for display if you still use it elsewhere
        }

    def save(self, commit=True, *args, **kwargs):
        """
        Override save method to auto-fill fields before saving.
        """
        instance = super().save(commit=False, *args, **kwargs)

        # Auto-populate fields
        if not instance.start_date:
            instance.start_date = timezone.now().date()  # Automatically set current date
        if not instance.originator_name and self.initial.get('request_user'):
            instance.originator_name = self.initial['request_user'].get_full_name()

        if commit:
            instance.save()
        return instance

# Form for Immediate Action
class ImmediateActionForm(forms.ModelForm):
    class Meta:
        model = ImmediateAction
        fields = ['action_description']
        widgets = {
            'action_description': forms.Textarea(attrs={'rows': 4}),
        }


# Form for Root Cause Analysis
class RootCauseAnalysisForm(forms.ModelForm):
    class Meta:
        model = RootCauseAnalysis
        fields = ['cause_description', 'rca_date', 'responsible_officer', 'estimated_close_date']
        widgets = {
            'cause_description': forms.Textarea(attrs={'rows': 4}),
            'rca_date': forms.DateInput(attrs={'type': 'date'}),
            'estimated_close_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CorrectiveActionPlanForm(forms.ModelForm):
    class Meta:
        model = CorrectiveActionPlan
        fields = ['activity', 'responsible_person', 'time_frame', 'resources_needed', 'result']
        widgets = {
            'activity': forms.Textarea(attrs={'rows': 3}),
            'result': forms.Textarea(attrs={'rows': 2}),
        }

class CorrectiveActionPlanReviewForm(forms.ModelForm):
    class Meta:
        model = CorrectiveActionPlanReview
        fields = ['effectiveness', 'reason']

class FollowUpActionForm(forms.ModelForm):
    class Meta:
        model = FollowUpAction
        fields = ['status', 'responsible_person', 'follow_up_date']
        widgets = {
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'status': 'Status',
            'responsible_person': 'Initials / Responsibility',
            'follow_up_date': 'Date',
        }

class ActionVerificationForm(forms.ModelForm):
    class Meta:
        model = ActionVerification
        fields = [
            "visit_number",
            "date",
            "follow_up_audit_result",
            "new_target_date",
            "status",
            "new_rfa_number",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "new_target_date": forms.DateInput(attrs={"type": "date"}),
            "follow_up_audit_result": forms.Textarea(attrs={"rows": 3}),
        }


class CloseOutForm(forms.ModelForm):
    class Meta:
        model = CloseOut
        fields = ['auditor_name', 'auditor_date', 'process_owner_name', 'process_owner_date']
        widgets = {
            'auditor_date': forms.DateInput(attrs={'type': 'date'}),
            'process_owner_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AuditDetailsForm(forms.ModelForm):
    class Meta:
        model = AuditDetails
        fields = ['date_range', 'location']

class GoodPointsForm(forms.ModelForm):
    class Meta:
        model = GoodPoints
        fields = ['campus', 'description']

class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        fields = ['ref_no', 'clause_no', 'details', 'finding_type', 'linked_rfa']


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            # Section A
            'knowledge1', 'knowledge2', 'knowledge3', 'knowledge4', 'knowledge5',

            # Section B
            'communication1', 'communication2', 'communication3', 'communication4', 'communication5',

            # Section C
            'audit_execution1', 'audit_execution2', 'audit_execution3', 'audit_execution4', 'audit_execution5',

            # Section E
            'continual_improvement1', 'continual_improvement2', 'continual_improvement3',
            'continual_improvement4', 'continual_improvement5',

            # Feedback
            'feedback',
        ]

        widgets = {
            # Section A
            'knowledge1': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'knowledge2': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'knowledge3': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'knowledge4': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'knowledge5': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),

            # Section B
            'communication1': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'communication2': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'communication3': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'communication4': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'communication5': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),

            # Section C
            'audit_execution1': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'audit_execution2': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'audit_execution3': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'audit_execution4': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'audit_execution5': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),

            # Section E
            'continual_improvement1': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'continual_improvement2': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'continual_improvement3': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'continual_improvement4': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'continual_improvement5': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),

            # Feedback
            'feedback': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

        labels = {
            # Section A
            'knowledge1': 'The internal auditor demonstrates understanding of ISO 9001:2015 requirements.',
            'knowledge2': 'The internal auditor applies knowledge effectively during audits.',
            'knowledge3': 'The internal auditor stays updated on changes to the standard.',
            'knowledge4': 'The internal auditor demonstrates proficiency in ISO audit requirements.',
            'knowledge5': 'The internal auditor ensures alignment with ISO standards in audit practices.',

            # Section B
            'communication1': 'The internal auditor communicates effectively with auditees.',
            'communication2': 'The internal auditor listens actively and asks relevant questions.',
            'communication3': 'The internal auditor provides clear and constructive feedback.',
            'communication4': 'The internal auditor demonstrates proficiency in written and verbal communication.',
            'communication5': 'The internal auditor facilitates open and transparent communication during audits.',

            # Section C
            'audit_execution1': 'The internal auditor follows the established audit process.',
            'audit_execution2': 'The internal auditor demonstrates professionalism and objectivity.',
            'audit_execution3': 'The internal auditor adapts to unexpected situations during audits.',
            'audit_execution4': 'The internal auditor uses effective questioning techniques to gather information.',
            'audit_execution5': 'The internal auditor demonstrates a keen attention to detail during the audit process.',

            # Section E
            'continual_improvement1': 'The internal auditor actively seeks feedback and identifies areas for personal improvement.',
            'continual_improvement2': 'The internal auditor contributes to the improvement of the university\'s quality management system.',
            'continual_improvement3': 'The internal auditor encourages a culture of continuous improvement within the team.',
            'continual_improvement4': 'The internal auditor demonstrates a proactive approach to professional development.',
            'continual_improvement5': 'The internal auditor integrates lessons learned from previous audits into current practices.',
        }

