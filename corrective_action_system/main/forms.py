from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import TemplateModel, Guideline, Announcement


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", required=False)
    role = forms.ChoiceField(choices=[
        ('Admin', 'Admin'),
        ('Process Owner', 'Process Owner'),
        ('Internal Auditor', 'Internal Auditor')
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
        ('Internal Auditor', 'Internal Auditor')
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
