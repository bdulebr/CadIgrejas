"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/urls.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.urls import path
from . import views

app_name = 'permissoes'

urlpatterns = [
    path('', views.painel_permissoes, name='dashboard'),
    path('membro/<int:membro_id>/salvar/', views.salvar_permissoes_membro, name='salvar_membro'),
    path('departamento/<int:departamento_id>/salvar/', views.salvar_permissoes_departamento, name='salvar_departamento'),
]
