from django.contrib import admin
from .models import UserProfile, TemplateModel

admin.site.register(UserProfile)

@admin.register(TemplateModel)
class TemplateModelAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'description', 'file')