"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: pdv/urls.py
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
    path('', views.pdv_dashboard, name='pdv_dashboard'),
    path('relatorios/fiados/', views.relatorio_fiados, name='pdv_relatorio_fiados'),
    path('relatorios/', views.relatorios_painel, name='pdv_relatorios_painel'),
    path('relatorios/exportar-pdf/', views.exportar_financeiro_pdf, name='pdv_exportar_financeiro_pdf'),

    path('login/', views.pdv_login, name='pdv_login'),
    path('logout/', views.pdv_logout, name='pdv_logout'),
    path('frente-caixa/', views.pdv_frente_caixa, name='pdv_frente_caixa'),
    path('api/produto/<str:codigo>/', views.api_buscar_produto, name='api_buscar_produto'),
    path('api/venda/finalizar/', views.api_finalizar_venda, name='api_finalizar_venda'),
    path('api/reservas/', views.api_listar_reservas, name='api_listar_reservas'),
    path('api/reservas/<int:reserva_id>/atualizar/', views.api_atualizar_reserva, name='api_atualizar_reserva'),
    path('api/caixa/abrir/', views.api_abrir_caixa, name='api_abrir_caixa'),
    path('api/caixa/fechar/', views.api_fechar_caixa, name='api_fechar_caixa'),
    path('venda/<int:venda_id>/cupom/', views.imprimir_cupom, name='pdv_imprimir_cupom'),
    path('importar-xml/', views.importar_xml_fornecedor, name='importar_xml_fornecedor'),
    path('produtos/', views.lista_produtos, name='pdv_lista_produtos'),
    path('produtos/novo/', views.novo_produto, name='pdv_novo_produto'),
    path('produtos/<int:produto_id>/editar/', views.editar_produto, name='pdv_editar_produto'),
    path('configuracoes/', views.configuracoes_pdv, name='pdv_configuracoes'),
    path('operadores/', views.gerenciar_operadores, name='pdv_gerenciar_operadores'),
    path('livro-caixa/', views.livro_caixa, name='pdv_livro_caixa'),
    # KDS TV
    path('tv/', views.pdv_painel_tv, name='pdv_painel_tv'),
    path('cozinha/', views.pdv_cozinha, name='pdv_cozinha'),
    path('api/tv/', views.api_tv_data, name='api_tv_data'),
    path('api/cozinha/atualizar/<int:venda_id>/<str:acao>/', views.api_cozinha_atualizar, name='api_cozinha_atualizar'),
]
