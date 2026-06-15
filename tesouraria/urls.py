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
    path('configuracoes/', views.configuracoes_tesouraria, name='configuracoes'),
    path('lancamentos/<int:pk>/baixa/', views.dar_baixa_lancamento, name='dar_baixa_lancamento'),
]
