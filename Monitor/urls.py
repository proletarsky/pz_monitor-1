"""Monitor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework import routers
from machines.views import RawDataViewSet
from .view import main_index, register, edit, validate, not_validate, validate_phone

urlpatterns = [
                  url(r'^$', main_index),
                  url(r'^machines/', include('machines.urls')),
                  url(r'^admin/', admin.site.urls),
                  url(r'^accounts/', include('django.contrib.auth.urls')),
                  url(r'^accounts/register/$', register, name='register'),
                  url(r'^accounts/edit/$', edit, name='edit'),
                  url(r'^accounts/validate/$', validate, name='validate'),
                  url(r'^accounts/not_validate/$', not_validate, name='not_validate'),
                  url(r'^validate_phone/$', validate_phone, name='validate_phone'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
