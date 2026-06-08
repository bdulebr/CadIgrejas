"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: midia_lgpd/urls.py
* DESCRIÇÃO: Rotas do módulo de Mídia e LGPD
"""

from django.urls import path
from . import views

urlpatterns = [
    path('lgpd/termo/', views.ler_assinar_termo, name='ler_assinar_termo'),
    path('lgpd/portal/', views.portal_lgpd, name='portal_lgpd'),
    path('lgpd/portal/exportar/', views.exportar_dados_pessoais, name='exportar_dados_pessoais'),
    path('lgpd/portal/esquecimento/', views.solicitar_esquecimento, name='solicitar_esquecimento'),
    path('midia/painel/', views.painel_midia, name='painel_midia'),
    path('midia/upload/', views.upload_arquivo, name='upload_arquivo'),

    # PV Drive Avançado
    path('drive/', views.pv_drive, {'modo': 'pessoal'}, name='pv_drive_home'),
    path('drive/pessoal/', views.pv_drive, {'modo': 'pessoal'}, name='pv_drive_pessoal'),
    path('drive/pessoal/pasta/<int:pasta_id>/', views.pv_drive, {'modo': 'pessoal'}, name='pv_drive_pessoal_pasta'),
    path('drive/dep/<int:alvo_id>/', views.pv_drive, {'modo': 'departamento'}, name='pv_drive_dep'),
    path('drive/dep/<int:alvo_id>/pasta/<int:pasta_id>/', views.pv_drive, {'modo': 'departamento'}, name='pv_drive_pasta'),
    path('drive/pasta/criar/', views.criar_pasta, name='criar_pasta'),
    path('drive/pasta/download/<int:pasta_id>/', views.download_pasta_zip, name='download_pasta_zip'),
    path('drive/upload/', views.upload_drive, name='upload_drive'),
    path('drive/upload_inteligente_ocr/', views.upload_inteligente_ocr, name='upload_inteligente_ocr'),
    path('drive/lixeira/', views.pv_drive_lixeira, name='pv_drive_lixeira'),
    path('drive/restaurar/<int:arquivo_id>/', views.restaurar_arquivo, name='restaurar_arquivo'),
    path('drive/arquivo/<int:arquivo_id>/visualizar/', views.visualizar_arquivo, name='visualizar_arquivo'),
    path('drive/arquivo/<int:arquivo_id>/baixar/', views.baixar_arquivo, name='baixar_arquivo'),
    path('drive/pasta/<int:pasta_id>/compartilhar/', views.compartilhar_pasta, name='compartilhar_pasta'),
    path('drive/compartilhamento/<int:permissao_id>/cancelar/', views.cancelar_compartilhamento, name='cancelar_compartilhamento'),

    # Documentos Avançados
    path('documentos/', views.painel_documentos, name='painel_documentos'),
    path('documentos/enviar/', views.enviar_documento, name='enviar_documento'),
    path('documentos/assinar/<uuid:token>/', views.assinar_documento_externo, name='assinar_documento_externo'),
]
