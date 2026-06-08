from django.urls import path
from . import views

urlpatterns = [
    path('item/<int:item_id>/etiqueta/', views.imprimir_etiqueta_qr, name='imprimir_etiqueta_qr'),
    path('item/todas-etiquetas/', views.imprimir_todos_qrs, name='imprimir_todos_qrs'),
    path('item/<int:item_id>/editar/', views.editar_item_almoxarifado, name='editar_item_almoxarifado'),
    path('categorias/', views.gerenciar_categorias, name='gerenciar_categorias_almoxarifado'),
    # Painel do Lider
    path('painel/', views.painel_inventario, name='painel_inventario'),
    path('painel/aprovacoes/', views.painel_aprovacoes_almoxarifado, name='painel_aprovacoes_almoxarifado'),
    path('painel/aprovacao/<int:mov_id>/<str:acao>/', views.processar_aprovacao, name='processar_aprovacao'),
    path('painel/cadastrar/', views.cadastrar_item_almoxarifado, name='cadastrar_item_almoxarifado'),
    path('livro/', views.livro_almoxarifado, name='livro_almoxarifado'),
    path('livro/exportar/', views.exportar_livro_pdf, name='exportar_livro_pdf'),

    # Auto-Serviço Público QR Code (Específicos)
    path('qr/retirar/<str:item_id>/', views.qr_movimentar_item, {'tipo': 'retirada'}, name='qr_retirar_item'),
    path('qr/devolver/<str:item_id>/', views.qr_movimentar_item, {'tipo': 'devolucao'}, name='qr_devolver_item'),

    # API Auto-Serviço (Carrinho)
    path('api/item/<str:item_id>/', views.api_buscar_item, name='api_buscar_item'),
    path('api/carrinho/finalizar/', views.finalizar_carrinho, name='finalizar_carrinho'),

    # QR Codes Genéricos (Leitores e Download)
    path('scanner/retirada/', views.scanner_generico, {'tipo': 'retirada'}, name='scanner_retirada_generico'),
    path('scanner/devolucao/', views.scanner_generico, {'tipo': 'devolucao'}, name='scanner_devolucao_generico'),
    path('qr-global/baixar/<str:tipo>/', views.baixar_qr_generico, name='baixar_qr_generico'),
]
