from django.urls import path
from . import views

urlpatterns = [
    # Painel do Lider
    path('painel/', views.painel_inventario, name='painel_inventario'),
    path('painel/cadastrar/', views.cadastrar_item_almoxarifado, name='cadastrar_item_almoxarifado'),
    path('livro/', views.livro_almoxarifado, name='livro_almoxarifado'),
    path('livro/exportar/', views.exportar_livro_pdf, name='exportar_livro_pdf'),

    # Auto-Serviço Público QR Code
    path('qr/retirar/<str:item_id>/', views.qr_movimentar_item, {'tipo': 'retirada'}, name='qr_retirar_item'),
    path('qr/devolver/<str:item_id>/', views.qr_movimentar_item, {'tipo': 'devolucao'}, name='qr_devolver_item'),
]
