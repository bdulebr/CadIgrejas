"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/urls.py
* DESCRIÇÃO: Rotas do almoxarifado
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:05
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:05: Criação inicial
"""

from django.urls import path
from . import views

urlpatterns = [
    path('almoxarifado/', views.painel_inventario, name='painel_inventario'),
    path('almoxarifado/novo/', views.registrar_novo_ativo, name='registrar_novo_ativo'),
    path('almoxarifado/emprestar/', views.registrar_emprestimo, name='registrar_emprestimo'),
    path('almoxarifado/devolver/<int:ativo_id>/', views.devolver_item, name='devolver_item'),
    path('almoxarifado/termo-pdf/<int:ativo_id>/', views.gerar_termo_pdf, name='gerar_termo_pdf'),
    path('almoxarifado/alimentos/', views.painel_alimentos, name='painel_alimentos'),
    path('almoxarifado/alimentos/novo/', views.adicionar_alimento, name='adicionar_alimento'),
    path('almoxarifado/alimentos/deletar/<int:lote_id>/', views.deletar_alimento, name='deletar_alimento'),
    path('almoxarifado/ativo/<int:ativo_id>/', views.ativo_detalhe, name='ativo_detalhe'),
    path('almoxarifado/ativo/<int:ativo_id>/deletar/', views.deletar_ativo, name='deletar_ativo'),
    path('almoxarifado/ativo/<int:ativo_id>/alocar/', views.alocar_uso_fixo, name='alocar_uso_fixo'),
    path('almoxarifado/ativo/<int:ativo_id>/remover-fixo/', views.remover_uso_fixo, name='remover_uso_fixo'),
    path('almoxarifado/ativo/<int:ativo_id>/manutencao/', views.enviar_manutencao, name='enviar_manutencao'),
    path('almoxarifado/manutencao/<int:manutencao_id>/concluir/', views.concluir_manutencao, name='concluir_manutencao'),
    path('almoxarifado/alimentos/<int:lote_id>/', views.alimento_detalhe, name='alimento_detalhe'),
    path('almoxarifado/alimentos/<int:lote_id>/transacao/', views.transacionar_alimento, name='transacionar_alimento'),
    path('almoxarifado/scanner/', views.scanner_qr, name='scanner_qr'),
    path('almoxarifado/pegar-item/', views.pegar_item_almoxarifado, name='pegar_item_almoxarifado'),
    path('almoxarifado/livro-caixa/', views.livro_caixa_almoxarifado, name='livro_caixa_almoxarifado'),
]
