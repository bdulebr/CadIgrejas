"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: midia_lgpd/urls.py
* DESCRIÇÃO: Rotas do módulo de Mídia e LGPD
"""

from django.urls import path
from . import views

urlpatterns = [
    path('lgpd/termo/', views.ler_assinar_termo, name='ler_assinar_termo'),
    path('midia/painel/', views.painel_midia, name='painel_midia'),
    path('midia/upload/', views.upload_arquivo, name='upload_arquivo'),
    
    # Documentos Avançados
    path('documentos/', views.painel_documentos, name='painel_documentos'),
    path('documentos/template/criar/', views.criar_template_documento, name='criar_template_documento'),
    path('documentos/enviar/', views.enviar_documento, name='enviar_documento'),
    path('documentos/assinar/<uuid:token>/', views.assinar_documento_externo, name='assinar_documento_externo'),
]
