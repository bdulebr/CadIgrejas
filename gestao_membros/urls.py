"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/urls.py
* DESCRIÇÃO: Rotas para o módulo de Gestão de Membros
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 13:55
* LOG DE ALTERAÇÕES:
* - 25/05/2026 13:55: Criação inicial
"""

from django.urls import path
from . import views

urlpatterns = [
    path('departamentos/', views.listar_departamentos, name='departamentos'),
    path('painel-lider/', views.painel_lider, name='painel_lider'),
    path('painel-lider/aprovar/<int:membro_id>/', views.aprovar_membro, name='aprovar_membro'),
    path('painel-lider/rejeitar/<int:membro_id>/', views.rejeitar_membro, name='rejeitar_membro'),
    path('painel-lider/evoluir/<int:membro_id>/', views.evoluir_membro, name='evoluir_membro'),

    path('departamentos/<int:dep_id>/funcoes/criar/', views.criar_funcao, name='criar_funcao'),
    path('departamento/funcao/excluir/<int:funcao_id>/', views.excluir_funcao, name='excluir_funcao'),
    path('departamento/funcao/<int:funcao_id>/vincular/', views.vincular_membro_funcao, name='vincular_membro_funcao'),
    path('departamento/funcao/<int:funcao_id>/desvincular/<int:membro_id>/', views.desvincular_membro_funcao, name='desvincular_membro_funcao'),
    path('avisos/', views.painel_avisos, name='painel_avisos'),
    path('avisos/criar/', views.criar_aviso, name='criar_aviso'),
    path('avisos/editar/<int:aviso_id>/', views.editar_aviso, name='editar_aviso'),
    path('avisos/excluir/<int:aviso_id>/', views.excluir_aviso, name='excluir_aviso'),
    path('avisos/pdf/<int:aviso_id>/', views.exportar_aviso_pdf, name='exportar_aviso_pdf'),
    path('departamentos/detalhes/<int:dep_id>/', views.detalhes_departamento, name='detalhes_departamento'),
    path('departamentos/excluir/<int:dep_id>/', views.excluir_departamento, name='excluir_departamento'),
    path('departamento/<int:dep_id>/atribuir-lideranca/', views.atribuir_lideranca, name='atribuir_lideranca'),
    path('departamentos/<int:dep_id>/salvar-instrucoes-escala/', views.salvar_instrucoes_escala, name='salvar_instrucoes_escala'),
    path('departamento/<int:dep_id>/salvar-slot/', views.salvar_configuracao_slot, name='salvar_configuracao_slot'),
    path('departamento/remover-slot/<int:config_id>/', views.remover_configuracao_slot, name='remover_configuracao_slot'),
    path('membros/', views.painel_membros, name='painel_membros'),
    path('membros/exportar/', views.exportar_membros_excel, name='exportar_membros_excel'),
    path('membros/importar/', views.importar_membros_excel, name='importar_membros_excel'),
    path('membros/baixar-modelo/', views.baixar_modelo_importacao, name='baixar_modelo_importacao'),
    path('membros/adicionar/', views.adicionar_membro, name='adicionar_membro'),
    path('membros/editar/<int:membro_id>/', views.editar_membro, name='editar_membro'),
    path('membros/excluir/<int:membro_id>/', views.excluir_membro, name='excluir_membro'),

    path('membro/gerir-lider/<int:membro_id>/', views.gerir_membro_lider, name='gerir_membro_lider'),
    path('membros/admin-excluir-mfa/<int:membro_id>/', views.admin_excluir_mfa, name='admin_excluir_mfa'),

    # Módulo de Gestão de Voluntários (RH)
    path('painel-lider/rh/', views.rh_painel, name='rh_painel'),
    path('painel-lider/rh/dossie/<int:membro_id>/', views.rh_dossie_membro, name='rh_dossie_membro'),
    path('painel-lider/rh/avaliar/<int:membro_id>/', views.rh_avaliar_membro, name='rh_avaliar_membro'),
    path('painel-lider/rh/ocorrencia/nova/', views.rh_nova_ocorrencia, name='rh_nova_ocorrencia'),
    path('painel-lider/rh/disciplina/<int:membro_id>/', views.rh_aplicar_disciplina, name='rh_aplicar_disciplina'),
    path('painel-lider/rh/disciplina/pdf/<int:acao_id>/', views.rh_gerar_pdf_disciplina, name='rh_gerar_pdf_disciplina'),

    # API
    path('api/membros/ai-autofill/', views.api_autofill_membro, name='api_autofill_membro'),

    # Recrutamento e Vagas
    path('departamento/<int:dep_id>/vaga/criar/', views.criar_vaga_setor, name='criar_vaga_setor'),
    path('vagas/excluir/<int:vaga_id>/', views.excluir_vaga_setor, name='excluir_vaga_setor'),
    path('vagas-abertas/', views.painel_vagas_publico, name='painel_vagas_publico'),
    path('vagas/candidatar/<int:vaga_id>/', views.candidatar_vaga, name='candidatar_vaga'),
    path('candidatura/avaliar/<int:candidatura_id>/<str:acao>/', views.avaliar_candidatura, name='avaliar_candidatura'),

    # Agenda do Setor
    path('departamento/<int:dep_id>/evento/criar/', views.criar_evento_setor, name='criar_evento_setor'),
    path('evento/excluir/<int:evento_id>/', views.excluir_evento_setor, name='excluir_evento_setor'),
]
