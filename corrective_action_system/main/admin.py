from django.contrib import admin
from fontTools.feaLib.ast import Comment

from .models import UserProfile, TemplateModel, NonConformity, RootCauseAnalysis, ImmediateAction, CorrectiveActionPlan, \
    FollowUpAction, ActionVerification, CorrectiveActionPlanReview, CloseOut, Comment


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'department', 'position')


@admin.register(TemplateModel)
class TemplateModelAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'description', 'file')

# Register other models if needed independently
admin.site.register(NonConformity)
admin.site.register(ImmediateAction)
admin.site.register(RootCauseAnalysis)
admin.site.register(CorrectiveActionPlan)
admin.site.register(CorrectiveActionPlanReview)
admin.site.register(FollowUpAction)
admin.site.register(ActionVerification)
admin.site.register(CloseOut)
admin.site.register(Comment)





