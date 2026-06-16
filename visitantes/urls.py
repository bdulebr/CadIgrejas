"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: visitantes/urls.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.visitantes_dashboard, name='visitantes_dashboard'),
    path('arquivo/', views.visitantes_arquivo, name='visitantes_arquivo'),
    path('perfil/<int:visitante_id>/', views.visitante_perfil, name='visitante_perfil'),
    path('cadastrar/', views.cadastrar_visitante, name='cadastrar_visitante'),
    path('perfil/<int:visitante_id>/editar/', views.editar_visitante, name='editar_visitante'),
    path('perfil/<int:visitante_id>/tornar-membro/', views.tornar_membro, name='tornar_membro'),
    path('perfil/<int:visitante_id>/desistencia/', views.desistencia_visitante, name='desistencia_visitante'),
    path('perfil/<int:visitante_id>/excluir/', views.excluir_visitante, name='excluir_visitante'),
    path('perfil/<int:visitante_id>/acompanhamento/add/', views.adicionar_acompanhamento, name='adicionar_acompanhamento'),
    path('perfil/<int:visitante_id>/visita/add/', views.adicionar_visita, name='adicionar_visita'),
    path('exportar/geral/', views.exportar_relatorio_geral_pdf, name='exportar_relatorio_geral_visitantes_pdf'),
    path('exportar/individual/<int:visitante_id>/', views.exportar_relatorio_individual_pdf, name='exportar_relatorio_individual_visitantes_pdf'),
]
