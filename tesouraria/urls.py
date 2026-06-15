from django.urls import path
from . import views

app_name = 'tesouraria'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lancamentos/', views.lista_lancamentos, name='lista_lancamentos'),
    path('lancamentos/novo/', views.novo_lancamento, name='novo_lancamento'),
    path('lancamentos/<int:pk>/', views.detalhe_lancamento, name='detalhe_lancamento'),
    path('lancamentos/<int:pk>/cancelar/', views.cancelar_lancamento, name='cancelar_lancamento'),
    path('exportar/', views.exportar_relatorio, name='exportar_relatorio'),

    # API endpoints
    path('api/scan_comprovante/', views.api_scan_comprovante, name='api_scan_comprovante'),
    path('sede/gerar-planilha/', views.gerar_e_revisar_planilha_sede, name='gerar_planilha_sede'),
    path('sede/enviar-email/', views.enviar_relatorio_sede_email, name='enviar_email_sede'),
    path('configuracoes/', views.configuracoes_tesouraria, name='configuracoes'),
    path('lancamentos/<int:pk>/baixa/', views.dar_baixa_lancamento, name='dar_baixa_lancamento'),
    # Importacao em Lote
    path('importacao/template/', views.download_template_importacao, name='download_template_importacao'),
    path('importacao/preview/', views.preview_importacao, name='preview_importacao'),
    path('importacao/confirmar/', views.confirmar_importacao, name='confirmar_importacao'),
]
