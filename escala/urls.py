"""escala URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django import urls
from django.contrib import admin
from django.urls import re_path
from django.urls.conf import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = [
    re_path(r'^', include('core.urls', namespace='core')),
    re_path(r'^usuario/', include('usuario.urls', namespace='usuario')),
    re_path(r'^pessoal/', include('pessoal.urls', namespace='pessoal')),
    re_path(r'^escala-servicos/', include('previsao.urls', namespace='previsao')),
    re_path(r'^servicos-tirados/', include('servico.urls', namespace='servico')),
    re_path(r'^admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
