from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('equipments:dashboard')),  
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('equipments/', include('equipments.urls')),
    # ... other app urls ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)