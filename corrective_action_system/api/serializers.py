from django.contrib.auth.models import User
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

    def validate_file(self, value):
        # Validate file size and type if needed
        if value.size > 10 * 1024 * 1024:  # 10 MB size limit
            raise serializers.ValidationError("File size exceeds the maximum limit of 10MB.")
        if not value.name.endswith(('.pdf', '.docx', '.xlsx')):
            raise serializers.ValidationError("Unsupported file format. Allowed: .pdf, .docx, .xlsx.")
        return value


class TemplateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateModel
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username:
            raise serializers.ValidationError("Username is required")

        user = User.objects.filter(username=username).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        attrs['user'] = user
        return attrs