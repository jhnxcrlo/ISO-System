from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import TemplateModel, Guideline, Announcement, NonConformity, ImmediateAction, RootCauseAnalysis, \
    CorrectiveActionPlan, FollowUpAction, CorrectiveActionPlanReview, ActionVerification, CloseOut


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", required=False)
    role = forms.ChoiceField(choices=[
        ('Admin', 'Admin'),
        ('Process Owner', 'Process Owner'),
        ('Internal Auditor', 'Internal Auditor'),
        ('Lead Auditor', 'Lead Auditor')
    ])

    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # Only enforce password confirmation for new users
        if not self.instance.pk:
            if not password:
                # Set default password if not provided
                cleaned_data['password'] = 'sorsu123'
            elif password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Set default password if none is provided
        if not self.cleaned_data.get('password'):
            user.set_password('sorsu123')
        else:
            user.set_password(self.cleaned_data['password'])

        # Save user and profile role
        if commit:
            user.save()
            if hasattr(user, 'userprofile'):
                user.userprofile.role = self.cleaned_data['role']
                user.userprofile.save()

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
            'non_conformity', 'assignees', 'originator_name', 'unit_department', 'phone', 'email',
            'rfa_intent', 'department', 'non_conformance_category', 'description_of_non_conformance',
            'iso_clause', 'category', 'start_date', 'status', 'assigned_to'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }


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