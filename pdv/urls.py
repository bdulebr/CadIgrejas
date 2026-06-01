from django.urls import path
from . import views

urlpatterns = [
    path('', views.pdv_dashboard, name='pdv_dashboard'),
    path('frente-caixa/', views.pdv_frente_caixa, name='pdv_frente_caixa'),
    path('api/produto/<str:codigo>/', views.api_buscar_produto, name='api_buscar_produto'),
    path('api/venda/finalizar/', views.api_finalizar_venda, name='api_finalizar_venda'),
    path('importar-xml/', views.importar_xml_fornecedor, name='importar_xml_fornecedor'),
    path('produtos/', views.lista_produtos, name='pdv_lista_produtos'),
    path('produtos/novo/', views.novo_produto, name='pdv_novo_produto'),
    path('produtos/<int:produto_id>/editar/', views.editar_produto, name='pdv_editar_produto'),
    path('configuracoes/', views.configuracoes_pdv, name='pdv_configuracoes'),
    path('livro-caixa/', views.livro_caixa, name='pdv_livro_caixa'),
]
