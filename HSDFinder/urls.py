"""djangoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

from . import settings
from django.urls import path, include
from fileOperation import views
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('submit/', views.submit, name='submit'),
    path('heatmap/', views.heatmap, name='heatmap'),
    path('download/<path:filename>/', views.download, name='download'),
    path('example/download/<path:filename>/', views.example_download, name='download'),
    path('database/', include('database.url')),
    path('combiner/', include('combiner.url'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
