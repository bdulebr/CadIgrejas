"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/urls.py
* DESCRIÇÃO: Rotas do módulo de escalas.
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:00
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:00: Inclusão de rotas de automação e relatórios
"""

from django.urls import path
from . import views
from . import checkin_views
from . import app_views

urlpatterns = [
    path('escalas/', views.painel_escalas, name='painel_escalas'),
    path('escalas/checkins-hoje/', views.checkins_hoje_desktop, name='checkins_hoje_desktop'),
    path('escalas/competencia/nova/', views.nova_competencia, name='nova_competencia'),
    path('escalas/competencia/<int:comp_id>/editar/', views.editor_escala_manual, name='editor_escala_manual'),
    path('escalas/competencia/<int:comp_id>/excluir/', views.excluir_competencia, name='excluir_competencia'),
    path('escalas/competencia/<int:comp_id>/salvar-slot/', views.salvar_slot_escala, name='salvar_slot_escala'),
    path('escalas/competencia/<int:comp_id>/publicar/', views.publicar_competencia, name='publicar_competencia'),
    path('escalas/competencia/deletar-slot/<int:escala_id>/', views.deletar_slot_escala, name='deletar_slot_escala'),
    path('escalas/gerar-automatica/', views.gerar_escala_automatica, name='gerar_escala_automatica'),

    # Gestão de Cultos e Eventos (Super Admin)
    path('escalas/cultos/', views.gerenciar_cultos, name='gerenciar_cultos'),
    path('escalas/cultos/criar/', views.criar_culto, name='criar_culto'),
    path('escalas/cultos/<int:culto_id>/editar/', views.editar_culto, name='editar_culto'),
    path('escalas/cultos/<int:culto_id>/excluir/', views.excluir_culto, name='excluir_culto'),

    path('escalas/api/alocar-slot/', views.alocar_slot_api, name='alocar_slot_api'),
    path('escalas/api/remover-slot/', views.remover_slot_api, name='remover_slot_api'),

    path('minhas-escalas/', views.minhas_escalas, name='minhas_escalas'),
    path('escalas/pdf/', views.exportar_escalas_pdf, name='exportar_escalas_pdf'),
    path('escalas/excel/', views.exportar_escalas_excel, name='exportar_escalas_excel'),
    path('escalas/csv/', views.exportar_escalas_csv, name='exportar_escalas_csv'),
    path('escalas/indisponibilidade/', views.registrar_indisponibilidade, name='registrar_indisponibilidade'),
    path('escalas/indisponibilidade/<int:ind_id>/remover/', views.remover_indisponibilidade, name='remover_indisponibilidade'),
    path('escalas/disponibilidade-fixa/', views.salvar_disponibilidade_fixa, name='salvar_disponibilidade_fixa'),
    path('escalas/baixar-publica/', views.baixar_escala_publica, name='baixar_escala_publica'),
    path('escalas/importar-ocr/', views.importar_escala_ocr, name='importar_escala_ocr'),

    # Check-in QR Code Zero-Trust
    path('escalas/checkin/', checkin_views.checkin_page, name='checkin_page'),
    path('escalas/api/checkin/processar/', checkin_views.api_processar_checkin, name='api_processar_checkin'),
    path('escalas/checkin/qrcode/baixar/', checkin_views.baixar_qrcode_checkin, name='baixar_qrcode_checkin'),
    path('escalas/checkin/manual/<int:escala_id>/', checkin_views.checkin_manual_lider, name='checkin_manual_lider'),
    path('escalas/checkin/manual/avulso/', checkin_views.checkin_manual_avulso, name='checkin_manual_avulso'),
]
