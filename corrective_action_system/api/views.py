from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import Announcement, Guideline, TemplateModel
from .serializers import AnnouncementSerializer, GuidelineSerializer, TemplateModelSerializer, LoginSerializer
from rest_framework.authtoken.models import Token

class UserLoginViewSet(viewsets.ViewSet):
    permission_classes = []

    def create(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            token, created = Token.objects.get_or_create(user=user)
            return (Response
                (
                {
                    "status": "success",
                    "message": "User logged in sucessfully",
                    "data":
                        {
                            "token": token.key,
                        }
                },
                status=status.HTTP_200_OK))
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class GuidelineViewSet(viewsets.ModelViewSet):
    queryset = Guideline.objects.all()
    serializer_class = GuidelineSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class TemplateModelViewSet(viewsets.ModelViewSet):
    queryset = TemplateModel.objects.all()
    serializer_class = TemplateModelSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

