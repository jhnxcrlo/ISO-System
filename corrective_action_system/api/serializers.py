from rest_framework import serializers

from main.models import Announcement, Guideline, TemplateModel


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'

class GuidelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guideline
        fields = '__all__'

class TemplateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateModel
        fields = '__all__'
