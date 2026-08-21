"""
URL configuration for erp_framework project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def favicon_view(request):
    svg_icon = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='#4f46e5'><path d='M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'/></svg>"""
    return HttpResponse(svg_icon, content_type="image/svg+xml")

urlpatterns = [
    path('favicon.ico', favicon_view, name='favicon'),
    path('', RedirectView.as_view(url='/hotel-pos/dashboard/', permanent=False)),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('hotel-pos/', include('hotel_pos.urls', namespace='hotel_pos')),
    path('inventory/', include('inventory.urls')),
    path('reports/', include('reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
