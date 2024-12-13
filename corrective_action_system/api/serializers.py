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
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.xlsx']
        if not any(value.name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("Only .pdf, .docx, and .xlsx files are allowed.")

        # Validate file size (e.g., 5 MB max)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must not exceed 5 MB.")

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