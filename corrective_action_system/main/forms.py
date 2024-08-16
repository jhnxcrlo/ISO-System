from django import forms
from django.contrib.auth.models import User
from .models import Announcement

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    role = forms.ChoiceField(choices=[('Process Owner', 'Process Owner'), ('Internal Auditor', 'Internal Auditor')])

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('Process Owner', 'Process Owner'), ('Internal Auditor', 'Internal Auditor')])

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']

class ReportForm(forms.Form):
    report_title = forms.CharField(max_length=200, label='Report Title')
    report_date = forms.DateField(label='Report Date', widget=forms.TextInput(attrs={'type': 'date'}))
    description = forms.CharField(widget=forms.Textarea, label='Description')