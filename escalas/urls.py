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

urlpatterns = [
    path('escalas/', views.painel_escalas, name='painel_escalas'),
    path('escalas/competencia/nova/', views.nova_competencia, name='nova_competencia'),
    path('escalas/competencia/<int:comp_id>/editar/', views.editor_escala_manual, name='editor_escala_manual'),
    path('escalas/competencia/<int:comp_id>/excluir/', views.excluir_competencia, name='excluir_competencia'),
    path('escalas/competencia/<int:comp_id>/salvar-slot/', views.salvar_slot_escala, name='salvar_slot_escala'),
    path('escalas/competencia/<int:comp_id>/publicar/', views.publicar_competencia, name='publicar_competencia'),
    path('escalas/competencia/deletar-slot/<int:escala_id>/', views.deletar_slot_escala, name='deletar_slot_escala'),
    path('escalas/gerar-automatica/', views.gerar_escala_automatica, name='gerar_escala_automatica'),
    
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
]
