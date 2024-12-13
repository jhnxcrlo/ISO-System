from django.urls import path, include
from rest_framework import routers

from .views import AnnouncementViewSet, GuidelineViewSet, TemplateModelViewSet, UserLoginViewSet

router = routers.DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)
router.register(r'guideline', GuidelineViewSet)
router.register(r'templates', TemplateModelViewSet)
router.register(r'login', UserLoginViewSet, basename='login')


urlpatterns = [
    path('', include(router.urls)),


]
