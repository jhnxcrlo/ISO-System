from django.contrib import admin
from .models import UserProfile, TemplateModel


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'department', 'position')



@admin.register(TemplateModel)
class TemplateModelAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'description', 'file')