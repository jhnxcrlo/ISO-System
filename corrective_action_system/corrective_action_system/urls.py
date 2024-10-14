from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', include('main.urls')),
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', lambda request: redirect('login', permanent=False)),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
