from django.shortcuts import render
from rest_framework import generics, viewsets

from main.models import Announcement
from .serializers import AnnouncementSerializer


# Create your views here.

#viewset

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
