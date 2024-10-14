from django.shortcuts import render
from rest_framework import generics, viewsets
from main.models import Announcement, Guideline, TemplateModel
from .serializers import AnnouncementSerializer, GuidelineSerializer, TemplateModelSerializer

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

class GuidelineViewSet(viewsets.ModelViewSet):
    queryset = Guideline.objects.all()
    serializer_class = GuidelineSerializer

class TemplateModelViewSet(viewsets.ModelViewSet):
    queryset = TemplateModel.objects.all()
    serializer_class = TemplateModelSerializer
