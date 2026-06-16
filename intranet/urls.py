"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/urls.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
"""
URL configuration for intranet project.

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
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import TemplateView

from core.views import pwa_manifest, pwa_service_worker

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/img/logo.jpg', permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('gestao_membros.urls')),
    path('', include('escalas.urls')),
    path('almoxarifado/', include('almoxarifado.urls')),
    path('pdv/', include('pdv.urls')),
    path('visitantes/', include('visitantes.urls')),
    path('casais/', include('ministerio_casais.urls')),
    path('', include('midia_lgpd.urls')),
    path('api/', include('api.urls')),
    path('tesouraria/', include('tesouraria.urls')),
    path('permissoes/', include('permissoes.urls')),
    path('sw.js', pwa_service_worker, name='sw.js'),
    path('manifest.json', pwa_manifest, name='manifest.json'),
]

from django.urls import re_path
from django.views.static import serve

# Em ambiente Intranet, servimos a mdia via Django mesmo em modo Produo (Waitress).
# Para redes fechadas, a performance do WSGI lendo discos locais SSD  mais que suficiente.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
